#!/usr/bin/env python

import asyncio
import json
import time
from os import environ
from random import choice, choices, randint
from typing import Optional, List
from pydantic import BaseModel

import redis.asyncio as redis
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = int(environ.get('REDIS_PORT') or 6379)
REDIS_STREAM_NAME = environ.get('REDIS_STREAM_NAME') or 'test'

rpool = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

LOG_LEVELS = [
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL"
]

INITIAL_CONFIGURATION = {
    "hosts": [
        {
            "name": "Mail servers",
            "options": {
                "hostname": "mailserver-RANDINT.mega-server-fleet.tld",
                "enabled": True,
                "amount": 100
            },
            "messages": [
                "Mail received from test@example.com",
                "Mail sent to test@example.com"
            ]
        },
        {
            "name": "Web servers",
            "options": {
                "hostname": "webserver-RANDINT.example.com",
                "enabled": True,
                "amount": 20
            },
            "messages": [
                "1.2.3.4 requested / status 200",
                "4.3.2.1 requested /forbidden 404"
            ]
        }
    ]
}

async def populate_capitals():
    # Populate country capitals object
    with open('country-capitals.json', 'r') as capitals:
        capitals = json.loads(capitals.read())
        await rpool.json().set('capitals', '$', capitals)

class MessageGenerator:
    """ Class for automated message generation. """
    def __init__(self, enabled: bool = False, min_delay: int = 100, max_delay: int = 1000, stream: str = "test"):
        self.enabled = enabled
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.stream = stream

    async def enable(self) -> None:
        """ Enable generator and run it until it is disabled. """
        self.generator_enabled = True
        while self.generator_enabled:
            await add_message(self.stream)
            await asyncio.sleep(randint(self.min_delay, self.max_delay) / 1000)

    def disable(self) -> None:
        """ Disable generator. """
        self.generator_enabled = False

    def set_min_delay(self, min_delay: int):
        """ Set minimum delay in milliseconds. """
        self.min_delay = min_delay

    def set_max_delay(self, max_delay: int):
        """ Set maximum delay in milliseconds. """
        self.max_delay = max_delay

message_generator = MessageGenerator(stream=REDIS_STREAM_NAME)

async def init_config():
    """ Init configuration for generator. """
    ret = await rpool.json().set("generator:config", "$", INITIAL_CONFIGURATION)
    return ret

async def get_config():
    """ Retrieve full configuration. """
    config = await rpool.json().get("generator:config")
    return config

async def get_random_capital_with_coordinates():
    """ Return random capital city with coordinates. """
    numcapitals = await rpool.json().arrlen('capitals')
    capital = await rpool.json().get('capitals', f'.[{randint(0, numcapitals-1)}]')
    return {
        'capital': capital['CapitalName'],
        'coordinates': f"{capital['CapitalLongitude']},{capital['CapitalLatitude']}",
        'country_code': capital['CountryCode']
    }
    
async def random_message():
    """ Generate random message. """
    config = await get_config()
    hostconfig = choice([host for host in filter(lambda x: x["options"]["enabled"], config["hosts"])])
    hostname = hostconfig["options"]["hostname"].replace('RANDINT', str(randint(1, int(hostconfig["options"]["amount"]))))

    message = {}
    message['timestamp'] = round(time.time() * 1000)
    message['hostname'] = hostname
    message['log_level'] = choices(
        population=LOG_LEVELS,
        weights=[
            0.3,
            0.3,
            0.2,
            0.15,
            0.05
        ],
        k=1
    )[0]
    message["message"] = choice(hostconfig["messages"])
    location = await get_random_capital_with_coordinates()
    message["city"] = location['capital']
    message["coordinates"] = location['coordinates']
    message['country_code'] = location['country_code']
    return message

async def add_message(stream="test"):
    """ Add log message to Redis stream. """
    message = json.dumps(await random_message())
    ret = await rpool.xadd(
        name=stream,
        fields={"json": message},
        maxlen=200000,
        approximate=True
    )
    return ret

### FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """ Initialize config on startup. """
    await populate_capitals()
    await init_config()

@app.get("/api/generator/enable", response_class=JSONResponse)
async def enable_generator(background_tasks: BackgroundTasks):
    """ Start message generator instance. """
    background_tasks.add_task(message_generator.enable)
    return {"success": True}

@app.get("/api/generator/disable", response_class=JSONResponse)
async def disable_generator():
    """ Disable all generators. """
    message_generator.disable()
    return {"success": True}

@app.get("/api/generator/generate/{n}", response_class=JSONResponse)
async def generate(request: Request, n: int):
    """ Call log generator to generate n log messages to stream. """
    await generate_messages(n=n, stream=REDIS_STREAM_NAME)
    return f"Generated {n} log entries"

async def generate_messages(
    stream: str = REDIS_STREAM_NAME,
    n: int = 100
    ):
    """ Call log generator to generate n messages to stream. """
    for _ in range(n):
        await add_message(stream)


@app.get("/api/generator/config", response_class=JSONResponse)
async def get_generator_config():
    """ Get generator config. """
    config = await get_config()
    return JSONResponse(content={"response": "ok", "config": config})

class GeneratorMessageAdd(BaseModel):
    """ Define message add payload"""
    hostidx: int
    message: str

@app.post("/api/generator/message/add", response_class=JSONResponse)
async def generator_message_add(query: GeneratorMessageAdd):
    """ Add message for host. """
    ret = await rpool.json().arrappend("generator:config", f"$.hosts[{query.hostidx}].messages", query.message)
    return JSONResponse(ret)

class GeneratorMessageDelete(BaseModel):
    """ Define message delete payload. """
    hostidx: int
    msgidx: int

@app.post("/api/generator/message/delete", response_class=JSONResponse)
async def generator_message_delete(query: GeneratorMessageDelete):
    """ Delete message from host. """
    ret = await rpool.json().arrpop("generator:config", f"$.hosts[{query.hostidx}].messages", query.msgidx)
    return JSONResponse(ret)

class GeneratorMessageModify(BaseModel):
    """ Define message modify payload. """
    hostidx: int
    msgidx: int
    message: str

@app.post("/api/generator/message/modify", response_class=JSONResponse)
async def generator_message_modify(query: GeneratorMessageModify):
    """ Modify message on host. """
    ret = await rpool.json().set("generator:config", f"$.hosts[{query.hostidx}].messages[{query.msgidx}]", query.message)
    return JSONResponse(ret)

class GeneratorConfig(BaseModel):
    """ Define generator config payload as dict. """
    config: list

@app.post("/api/generator/config/update", response_class=JSONResponse)
async def generator_config_write(query: GeneratorConfig):
    """ Replace configuration. """
    ret = await rpool.json().set("generator:config", "$.hosts", query.config)
    return JSONResponse(ret)

class GeneratorHostOptions(BaseModel):
    """ Generator host options payload. """
    hostname: str
    enabled: bool
    amount: int

class GeneratorHostAdd(BaseModel):
    """ Generator host add payload. """
    name: str
    options: GeneratorHostOptions
    messages: list[str]

@app.post("/api/generator/host/add", response_class=JSONResponse)
async def generator_host_add(query: GeneratorHostAdd):
    """ Add host to generator configuration. """
    ret = await rpool.json().arrappend("generator:config", f"$.hosts", query.dict())
    return JSONResponse(ret)

def main():
    pass

if __name__ == '__main__':
    main()
