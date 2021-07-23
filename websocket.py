import asyncio
from dataclasses import dataclass
from os import environ
from pydantic import BaseModel
from time import time

import aioredis
from aioredis.client import string_keys_to_dict

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
    websocket: WebSocket
    streams: dict

    def add_stream(self, stream):
        self.streams[stream] = ">"

    def remove_stream(self, stream):
        if stream in self.streams:
            del self.streams[stream]

app = FastAPI()
templates = Jinja2Templates(directory="templates")
rpool = aioredis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
        self.rconn = aioredis.Redis(connection_pool=rpool)
        self.available_streams = {}
        self.splitter_active = False

    async def connect(self, websocket: WebSocket, client_id: int):
        await websocket.accept()
        await self.update_available_streams()
        self.active_connections[client_id] = WebsocketClientConnection(
            websocket=websocket,
            streams=self.available_streams
        )

    def disconnect(self, client_id: int) -> None:
        del self.active_connections[client_id]

    async def update_available_streams(self) -> dict:
        cursor = None
        avail = {}
        while cursor != 0:
            cursor, res = await self.rconn.zscan(
                name="severities",
                cursor=cursor or 0)
            for severity in res:
                avail[severity[0]] = ">"
                if severity[0] not in self.available_streams:
                    try:
                        await self.rconn.xgroup_create(
                            name=severity[0],
                            groupname=REDIS_CONSUMER_GROUP,
                            mkstream=False
                        )
                    except aioredis.exceptions.ResponseError:
                        pass
        if len(avail) == 0 and not self.splitter_active:
            avail = {REDIS_STREAM_NAME: ">"}
        self.available_streams = avail
        return avail

    def activate_splitter(self):
        self.splitter_active = True

    async def send_client_message(self, message: str, client_id: int):
        await self.active_connections[client_id].websocket.send_text(message)
    
    async def send_client_json(self, message: dict, client_id: int):
        await self.active_connections[client_id].websocket.send_json(message)

    async def send_broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    r = aioredis.Redis(connection_pool=rpool)
    await r.delete("consumerids")
    await r.delete("severities")
    active_gears_registrations = await r.execute_command('RG.DUMPREGISTRATIONS')
    for registration in active_gears_registrations:
        print(f"Unregistering: {registration[1]}... ", end="")
        print(await r.execute_command('RG.UNREGISTER', registration[1]))
        await r.delete("test")
    await r.delete(REDIS_STREAM_NAME)
    await r.xgroup_create(
        name=REDIS_STREAM_NAME,
        groupname=REDIS_CONSUMER_GROUP,
        mkstream = True
    )

@app.on_event("shutdown")
def shutdown_event():
    print("shutting down")
    for client_id in manager.active_connections:
        manager.disconnect(client_id)

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    r = aioredis.Redis(connection_pool=rpool)
    client_id = await r.incrby("consumerids", 1)
    return templates.TemplateResponse("websockets.html", {
        "request": request,
        "host": "127.0.0.1",
        "port": 8000,
        "client_id": client_id})

@app.get("/generate/{n}", response_class=HTMLResponse)
async def generate(request: Request, n: int):
    await generate_messages(n=n)
    return f"Generated {n} log entries"

@app.get("/streams/splitter", response_class=JSONResponse)
async def register_stream_splitter():
    r = aioredis.Redis(connection_pool=rpool)
    print(f"Trimming {REDIS_STREAM_NAME} before registering Gears function")
    await r.xtrim(
        name=REDIS_STREAM_NAME,
        maxlen=0,
        approximate=False)
    print(f"Removing {REDIS_STREAM_NAME} from all clients")
    for client_id in manager.active_connections:
        manager.active_connections[client_id].remove_stream(REDIS_STREAM_NAME)
    print("Registering severity splitter... ", end="")
    print(await r.execute_command('RG.PYEXECUTE', gears_functions.SPLIT_BY_SEVERITY))
    manager.activate_splitter()
    return JSONResponse(content={"response": "ok"})

@app.get("/streams/update", response_class=JSONResponse)
async def update_streams():
    streams = await manager.update_available_streams()
    return JSONResponse(content=streams)

@app.get("/streams/{client_id}/add/{stream}", response_class=JSONResponse)
def add_stream_to_client(client_id: int, stream: str):
    manager.active_connections[client_id].add_stream(stream)
    return JSONResponse(content={"response": "ok"})

@app.get("/streams/{client_id}/del/{stream}", response_class=JSONResponse)
def del_stream_from_client(client_id: int, stream: str):
    manager.active_connections[client_id].remove_stream(stream)
    return JSONResponse(content={"response": "ok"})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket, client_id)
    print(f"connected: {client_id}")
    try:
        last_keepalive = time()
        while True:
            if time() - 5 > last_keepalive:
                #print(f"sending ping to {client_id}")
                await manager.send_client_json({
                    'type': 'ping',
                    'data': {"timestamp": last_keepalive}},
                    client_id)
                await websocket.receive_text()
                #print(f"received pong from {client_id}")
                last_keepalive = time()

            if len(manager.active_connections[client_id].streams) == 0:
                await asyncio.sleep(1)
                continue

            data = await read_streams(client_id)
            if len(data) > 0:
                for contents in data:
                    await manager.send_client_json({
                        'type': 'message',
                        'data': contents},
                        client_id)
    except (ConnectionClosedOK, ConnectionClosedError):
        print(f"{client_id} disconnected")
        manager.disconnect(client_id)

async def read_streams(client_id: str):
    r = aioredis.Redis(connection_pool=rpool)
    consumername = f"consumer-{client_id}"
    if client_id in manager.active_connections and len(manager.active_connections[client_id].streams) > 0:
        #print(client_id)
        #print(manager.active_connections[client_id].streams)
        response = []
        try:
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
    n: int = 100):
    r = aioredis.Redis(connection_pool=rpool)
    for _ in range(n):
        await log_generator.add_message(r, stream)


@app.get("/search", response_class=HTMLResponse)
async def get_search(request: Request):
    return templates.TemplateResponse("search.html", {
        "request": request,
        "host": "127.0.0.1",
        "port": 8000
        })

class SearchQuery(BaseModel):
    query: str

@app.post("/search", response_class=JSONResponse)
def search_string(query: SearchQuery):
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
    query: str
    field: str

@app.post("/search/aggregate", response_class=JSONResponse)
def search_aggregate_by_fields(query: AggregateQuery):
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
