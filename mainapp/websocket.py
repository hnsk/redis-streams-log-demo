import asyncio
import json
from dataclasses import dataclass
from os import environ
from time import time
from pydantic import BaseModel

import redis.asyncio
import redis.exceptions

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from redis import ResponseError
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = int(environ.get('REDIS_PORT') or '6379')
REDIS_CONSUMER_GROUP = environ.get('REDIS_CONSUMER_GROUP') or 'testgroup'
REDIS_STREAM_NAME = environ.get('REDIS_STREAM_NAME') or 'test'

@dataclass
class WebsocketClientConnection:
    """ Class for WebSocket client connection. """

    websocket: WebSocket
    streams: dict

    def add_stream(self, stream):
        """ Add stream to the client. """
        self.streams[stream] = ">"

    def remove_stream(self, stream):
        """ Remove stream from the client. """
        if stream in self.streams:
            del self.streams[stream]

# Create FastAPI app instance
app = FastAPI()

# Create synchronous connection pool for Redis
rpool = redis.asyncio.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

# Get INFO from redis
async def get_redis_info():
    return await rpool.info()

class ConnectionManager:
    """ Class for managing WebSocket connections"""
    def __init__(self):
        self.active_connections: dict = {}
        self.rconn = rpool
        self.available_streams = {}
        self.splitter_active = False

    async def connect(self, websocket: WebSocket, client_id: int) -> None:
        """ Accept WebSocket connection and subscribe to available streams. """
        await websocket.accept()
        await self.update_available_streams()
        self.active_connections[client_id] = WebsocketClientConnection(
            websocket=websocket,
            streams=self.available_streams
        )

    def disconnect(self, client_id: int) -> None:
        """ On client disconnection remove client from active connections. """
        del self.active_connections[client_id]

    async def update_available_streams(self) -> dict:
        """
        Retrieve available streams from sorted set severities.
        If no streams are available and stream splitter is not activated
        then subscribe to REDIS_STREAM_NAME.

        Returns dictionary of available streams.
        """

        cursor = None
        avail = {}
        while cursor != 0:
            cursor, res = await self.rconn.zscan(
                name="severities",
                cursor=cursor or 0)
            for severity in res:
                avail[severity[0]] = ">"

                # If consumer group for severity doesn't exist, create it
                if severity[0] not in self.available_streams:
                    try:
                        await self.rconn.xgroup_create(
                            name=severity[0],
                            groupname=REDIS_CONSUMER_GROUP,
                            mkstream=False
                        )
                    except redis.exceptions.ResponseError:
                        pass

        # If no streams are available and splitter is not active.
        # Subscribe to REDIS_STREAM_NAME
        if len(avail) == 0 and not self.splitter_active:
            avail = {REDIS_STREAM_NAME: ">"}
        self.available_streams = avail
        return avail

    def activate_splitter(self) -> None:
        """ Set stream splitter status to active. """
        self.splitter_active = True

    async def send_client_message(self, message: str, client_id: int) -> None:
        """ Send message string to client_id. """
        await self.active_connections[client_id].websocket.send_text(message)
    
    async def send_client_json(self, message: dict, client_id: int) -> None:
        """ Send dictionary as JSON to client_id. """
        await self.active_connections[client_id].websocket.send_json(message)

    async def send_broadcast(self, message: str) -> None:
        """ Send broadcast message to all active clients. """
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """ Initialise Redis database on server startup. """

    # Remove old consumer IDs and severities if they exist.
    await rpool.delete("consumerids")
    await rpool.delete("severities")

    # Remove existing Redis Gears script registrations if they exist.
    try:
        await rpool.execute_command('TFUNCTION', 'DELETE', 'stream_splitter')
    except:
        pass

    # Delete existing stream if it exists
    await rpool.delete(REDIS_STREAM_NAME)

    # Create consumer group
    await rpool.xgroup_create(
        name=REDIS_STREAM_NAME,
        groupname=REDIS_CONSUMER_GROUP,
        mkstream = True
    )

@app.on_event("shutdown")
def shutdown_event() -> None:
    """ Disconnect all active connections on shutdown. """
    print("shutting down")
    for client_id in manager.active_connections:
        manager.disconnect(client_id)

@app.get("/api/clientid", response_class=JSONResponse)
async def get_clientid():
    """ Return new client ID. """
    client_id = await rpool.incrby("consumerids", 1)
    return JSONResponse(content={"response": "ok", "client_id": client_id})

@app.get("/api/streams/splitter", response_class=JSONResponse)
async def register_stream_splitter():
    """ Register Redis Gears function to split stream to severities. """
    # Trim all old entries from the stream before registration.
    print(f"Trimming {REDIS_STREAM_NAME} before registering Gears function")
    await rpool.xtrim(
        name=REDIS_STREAM_NAME,
        maxlen=0,
        approximate=False)

    # Remove REDIS_STREAM_NAME from all active connections so
    # it's only being consumed by the Gears function.
    print(f"Removing {REDIS_STREAM_NAME} from all clients")
    for client_id in manager.active_connections:
        manager.active_connections[client_id].remove_stream(REDIS_STREAM_NAME)
    print("Registering severity splitter... ", end="")

    with open('stream_splitter.js', 'r') as file:
        await rpool.execute_command('TFUNCTION', 'LOAD', 'REPLACE', file.read())
    manager.activate_splitter()
    return JSONResponse(content={"response": "ok"})

@app.get("/api/streams/update", response_class=JSONResponse)
async def update_streams():
    """ Update available streams for all clients. """
    streams = await manager.update_available_streams()
    return JSONResponse(content=streams)

@app.get("/api/streams/{client_id}/add/{stream}", response_class=JSONResponse)
def add_stream_to_client(client_id: int, stream: str):
    """ Add stream subscription to client. """
    manager.active_connections[client_id].add_stream(stream)
    return JSONResponse(content={"response": "ok"})

@app.get("/api/streams/{client_id}/del/{stream}", response_class=JSONResponse)
def del_stream_from_client(client_id: int, stream: str):
    """ Delete stream subscription from a client. """
    manager.active_connections[client_id].remove_stream(stream)
    return JSONResponse(content={"response": "ok"})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    """ Define websocket endpoint for log stream. """
    await manager.connect(websocket, client_id)
    print(f"connected: {client_id}")
    try:
        last_keepalive = time()
        while True:
            # Send ping every 5 seconds to make sure client connections
            # are still connected.
            if time() - 5 > last_keepalive:
                redis_info = await get_redis_info()
                await manager.send_client_json({
                    'type': 'ping',
                    'data': {
                        'timestamp': last_keepalive,
                        'redis_info': redis_info
                        }},
                    client_id)
                await websocket.receive_text()
                last_keepalive = time()

            # If we don't have any stream subscriptions sleep for 1 second
            if len(manager.active_connections[client_id].streams) == 0:
                await asyncio.sleep(1)
                continue

            # Read new entries from all subscribed streams.
            # If we received data, send it to the client WebSocket.
            data = await read_streams(client_id)
            if len(data) > 0:
                for contents in data:
                    await manager.send_client_json({
                        'type': 'message',
                        'data': json.loads(contents["json"])},
                        client_id)
    except (ConnectionClosedOK, ConnectionClosedError):
        print(f"{client_id} disconnected")
        manager.disconnect(client_id)

async def read_streams(client_id: str):
    """ Read entries from subscribed streams for client_id. """

    consumername = f"consumer-{client_id}"
    if client_id in manager.active_connections and len(manager.active_connections[client_id].streams) > 0:
        response = []
        try:
            # Read up to 1 message from each subscribed stream.
            # Call is blocking and we're waiting for 1 second for new
            # events in the streams.
            data = await rpool.xreadgroup(
                groupname=REDIS_CONSUMER_GROUP,
                consumername=consumername,
                streams=manager.active_connections[client_id].streams,
                count=1,
                block=1000)
            if len(data) > 0:
                for entry in data:
                    response.append(entry[1][0][1]) # Event data
                    await rpool.xack(
                        entry[0], # Stream name
                        REDIS_CONSUMER_GROUP,
                        entry[1][0][0] # Stream ID
                    )
        except redis.exceptions.DataError:
            # If no streams are being consumed just return and try again later
            pass
        return response


### Log event modification routes

class LogMessage(BaseModel):
    """ Log message payload. """
    key: str
    field: str
    value: str

@app.post("/api/log/message/modify", response_class=JSONResponse)
async def log_message_modify(query: LogMessage):
    """ Modify message. """
    ret = await rpool.json().set(query.key, f"$.{query.field}", query.value)
    return ret


### Misc routes

@app.get("/api/redis/info", response_class=JSONResponse)
async def redis_info():
    """ Get redis INFO. """
    return await get_redis_info()