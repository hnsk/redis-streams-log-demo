import asyncio
import json
from dataclasses import dataclass
from os import environ
from time import time
from pydantic import BaseModel

import aioredis
import aiohttp

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from redis import ResponseError
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

import log_generator
import gears_functions
import search

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = environ.get('REDIS_PORT') or '6379'
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
templates = Jinja2Templates(directory="templates")

# Create connection pool for Redis
rpool = aioredis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True)

class ConnectionManager:
    """ Class for managing WebSocket connections"""
    def __init__(self):
        self.active_connections: dict = {}
        self.rconn = aioredis.Redis(connection_pool=rpool)
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
                    except aioredis.exceptions.ResponseError:
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
    r = aioredis.Redis(connection_pool=rpool)

    # Remove old consumer IDs and severities if they exist.
    await r.delete("consumerids")
    await r.delete("severities")

    # Remove existing Redis Gears script registrations if they exist.
    active_gears_registrations = await r.execute_command('RG.DUMPREGISTRATIONS')
    for registration in active_gears_registrations:
        print(f"Unregistering: {registration[1]}... ", end="")
        print(await r.execute_command('RG.UNREGISTER', registration[1]))
        await r.delete("test")

    # Delete existing stream if it exists
    await r.delete(REDIS_STREAM_NAME)

    # Create consumer group
    await r.xgroup_create(
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

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """ Index page. """
    r = aioredis.Redis(connection_pool=rpool)
    client_id = await r.incrby("consumerids", 1)
    return templates.TemplateResponse("websockets.html", {
        "request": request,
        "host": "127.0.0.1",
        "port": 8000,
        "client_id": client_id})

@app.get("/generate/{n}", response_class=HTMLResponse)
async def generate(request: Request, n: int):
    """ Call log generator to generate n log messages to stream. """
    await generate_messages(n=n, stream=REDIS_STREAM_NAME)
    return f"Generated {n} log entries"

@app.get("/streams/splitter", response_class=JSONResponse)
async def register_stream_splitter():
    """ Register Redis Gears function to split stream to severities. """
    r = aioredis.Redis(connection_pool=rpool)

    # Trim all old entries from the stream before registration.
    print(f"Trimming {REDIS_STREAM_NAME} before registering Gears function")
    await r.xtrim(
        name=REDIS_STREAM_NAME,
        maxlen=0,
        approximate=False)

    # Remove REDIS_STREAM_NAME from all active connections so
    # it's only being consumed by the Gears function.
    print(f"Removing {REDIS_STREAM_NAME} from all clients")
    for client_id in manager.active_connections:
        manager.active_connections[client_id].remove_stream(REDIS_STREAM_NAME)
    print("Registering severity splitter... ", end="")
    print(await r.execute_command('RG.PYEXECUTE', gears_functions.SPLIT_BY_SEVERITY))
    manager.activate_splitter()
    return JSONResponse(content={"response": "ok"})

@app.get("/streams/update", response_class=JSONResponse)
async def update_streams():
    """ Update available streams for all clients. """
    streams = await manager.update_available_streams()
    return JSONResponse(content=streams)

@app.get("/streams/{client_id}/add/{stream}", response_class=JSONResponse)
def add_stream_to_client(client_id: int, stream: str):
    """ Add stream subscription to client. """
    manager.active_connections[client_id].add_stream(stream)
    return JSONResponse(content={"response": "ok"})

@app.get("/streams/{client_id}/del/{stream}", response_class=JSONResponse)
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
                await manager.send_client_json({
                    'type': 'ping',
                    'data': {"timestamp": last_keepalive}},
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

    r = aioredis.Redis(connection_pool=rpool)
    consumername = f"consumer-{client_id}"
    if client_id in manager.active_connections and len(manager.active_connections[client_id].streams) > 0:
        response = []
        try:
            # Read up to 1 message from each subscribed stream.
            # Call is blocking and we're waiting for 1 second for new
            # events in the streams.
            data = await r.xreadgroup(
                groupname=REDIS_CONSUMER_GROUP,
                consumername=consumername,
                streams=manager.active_connections[client_id].streams,
                count=1,
                block=1000)
            if len(data) > 0:
                for entry in data:
                    response.append(entry[1][0][1]) # Event data
                    await r.xack(
                        entry[0], # Stream name
                        REDIS_CONSUMER_GROUP,
                        entry[1][0][0] # Stream ID
                    )
        except aioredis.exceptions.DataError:
            # If no streams are being consumed just return and try again later
            pass
        return response

async def generate_messages(
    stream: str = REDIS_STREAM_NAME,
    n: int = 100
    ):
    """ Call log generator to generate n messages to stream. """
    r = aioredis.Redis(connection_pool=rpool)
    for _ in range(n):
        await log_generator.add_message(r, stream)


@app.get("/search", response_class=HTMLResponse)
async def get_search(request: Request):
    """ Return RediSearch template page. """
    async with aiohttp.ClientSession() as session:
        async with session.get('http://redisinsight:8001/api/instance/') as response:
            ri_db = await response.json()
            ri_db = ri_db["dbs"][0]["id"]

    return templates.TemplateResponse("search.html", {
        "request": request,
        "host": "127.0.0.1",
        "port": 8000,
        "ri_db": ri_db
        })

class SearchQuery(BaseModel):
    """ Search query definition. Accepted parameters are a query string. """
    query: str

@app.post("/search", response_class=JSONResponse)
def search_string(query: SearchQuery):
    """ Search string from logs and return results and information. """

    # Make sure the index exists before querying.
    search.create_index()

    results = {}
    results['total'] = 0
    results['duration'] = 0
    results['messages'] = []
    results['literal_query'] = ""
    results['error'] = ""
    try:
        for res, literal_query in search.search_index(query.query):
            results['total'] = res.total
            results['duration'] += res.duration
            results['literal_query'] = literal_query
            for doc in res.docs:
               results['messages'].append({
                   "id": doc.id,
                    "hostname": doc.hostname,
                    "timestamp": doc.timestamp,
                    "message": doc.message,
                    "log_level": doc.log_level
                })
    except ResponseError:
        print(f"invalid query {query.query}")
        results['error'] = f"Invalid query {query.query}"
    results['duration'] = f"{results['duration']:.2f}"
    results['numresults'] = len(results['messages'])
    return JSONResponse(results)

class AggregateQuery(BaseModel):
    """
    Aggregate query definition.
    Accepts query string and field to aggregate on.
    """

    query: str
    field: str

@app.post("/search/aggregate", response_class=JSONResponse)
def search_aggregate_by_fields(query: AggregateQuery):
    """ Aggregate log severities based on the provided query. """

    # Make sure the index exists before querying.
    search.create_index()
    result = {}
    result["results"] = []
    result["literal_query"] = ""
    result["error"] = ""
    try:
        for res, literal_query in search.aggregate_by_field(query.query, query.field):
            result["literal_query"] = literal_query
            for row in res.rows:
                result["results"].append({
                    "field": row[1],
                    "entries": row[3]
                })
    except ResponseError:
        print(f"invalid query {query.query}")
        result["error"] = f"Invalid query {query.query}"

    return JSONResponse(result)
