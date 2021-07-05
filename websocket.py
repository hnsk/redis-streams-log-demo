import asyncio
import json
import signal
import traceback
from os import environ
from typing import List
from random import randint
from time import sleep, time

import aioredis

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

import log_generator

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_client_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def send_client_json(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def send_broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

if environ.get('REDIS_HOST') is not None:
   REDIS_HOST = environ.get('REDIS_HOST')
else:
   REDIS_HOST = 'localhost'

if environ.get('REDIS_PORT') is not None:
   REDIS_PORT = environ.get('REDIS_PORT')
else:
   REDIS_PORT = '6379'

app = FastAPI()
templates = Jinja2Templates(directory="templates")

rpool = aioredis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
@app.on_event("startup")
async def startup_event():
    r = aioredis.Redis(connection_pool=rpool)
    await r.delete("consumerids")
    await r.delete("test")
    await r.xgroup_create(
        name="test",
        groupname="testgroup",
        mkstream = True
    )

@app.on_event("shutdown")
def shutdown_event():
    print("shutting down")
    for websocket in manager.active_connections():
        manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("websockets.html", {"request": request, "host": "127.0.0.1", "port": 8000})

@app.get("/generate/{n}", response_class=HTMLResponse)
async def generate(request: Request, n: int):
    await generate_messages(n=n)
    return "moi"

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        last_keepalive = time()
        while True:
            async for data in read_stream("test", websocket):
                if time() - 5 > last_keepalive:
                    await manager.send_client_json({'type': 'ping', 'data': {"timestamp": last_keepalive}}, websocket)
                    response = await websocket.receive_text()
                    last_keepalive = time()
                if len(data) > 0:
                    contents = data[0][1][0][1]
                    await manager.send_client_json({'type': 'message', 'data': contents}, websocket)
    except (ConnectionClosedOK, ConnectionClosedError):
        print(f"{client_id} disconnected")
        manager.disconnect(websocket)

async def read_stream(stream: str, websocket: WebSocket):    
    r = aioredis.Redis(connection_pool=rpool)
    consumer_number = await r.incrby("consumerid", 1)
    consumername = f"consumer-{consumer_number}"
    while websocket in manager.active_connections:
        data = await r.xreadgroup(
            groupname="testgroup",
            consumername=consumername,
            streams={stream: ">"},
            count=1,
            block=1000)
        if len(data) > 0:
            await r.xack(
                stream,
                "testgroup",
                data[0][1][0][0]
            )
        yield data

async def generate_messages(
    stream: str = "test",
    n: int = 100):
    r = aioredis.Redis(connection_pool=rpool)
    for x in range(n):
        await log_generator.add_message(r)
