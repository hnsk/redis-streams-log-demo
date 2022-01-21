#!/usr/bin/env python

import json
import time
from os import environ
from random import choice, choices, randint
from typing import Optional, List
from pydantic import BaseModel

import aioredis
import redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = int(environ.get('REDIS_PORT') or 6379)
REDIS_STREAM_NAME = environ.get('REDIS_STREAM_NAME') or 'test'

rpool = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

# Create asynchronous connection pool for Redis
aiorpool = aioredis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True)

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
                "Mail received from <test@example.com>",
                "Mail sent to <test@example.com>"
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

# Populate country capitals object
with open('country-capitals.json', 'r') as capitals:
    capitals = json.loads(capitals.read())
    rpool.json().set('capitals', '$', capitals)


def init_config():
    """ Init configuration for generator. """
    ret = rpool.json().set("generator:config", "$", INITIAL_CONFIGURATION)
    return ret

def get_config():
    """ Retrieve full configuration. """
    config = rpool.json().get("generator:config")
    return config

def get_random_capital_with_coordinates():
    """ Return random capital city with coordinates. """
    numcapitals = rpool.json().arrlen('capitals')
    capital = rpool.json().get('capitals', f'.[{randint(0, numcapitals-1)}]')
    return {
        'capital': capital['CapitalName'],
        'coordinates': f"{capital['CapitalLongitude']},{capital['CapitalLatitude']}",
        'country_code': capital['CountryCode']
    }
    
def random_message():
    """ Generate random message. """
    config = get_config()
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
    location = get_random_capital_with_coordinates()
    message["city"] = location['capital']
    message["coordinates"] = location['coordinates']
    message['country_code'] = location['country_code']
    return message

async def add_message(r, stream="test"):
    """ Add log message to Redis stream. """
    message = json.dumps(random_message())
    ret = await r.xadd(
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
    init_config()

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
    r = aioredis.Redis(connection_pool=aiorpool)
    for _ in range(n):
        await add_message(r, stream)


@app.get("/api/generator/config", response_class=JSONResponse)
def get_generator_config():
    """ Get generator config. """
    config = get_config()
    return JSONResponse(content={"response": "ok", "config": config})

class GeneratorMessageAdd(BaseModel):
    """ Define message add payload"""
    hostidx: int
    message: str

@app.post("/api/generator/message/add", response_class=JSONResponse)
def generator_message_add(query: GeneratorMessageAdd):
    """ Add message for host. """
    ret = rpool.json().arrappend("generator:config", f"$.hosts[{query.hostidx}].messages", query.message)
    return JSONResponse(ret)

class GeneratorMessageDelete(BaseModel):
    """ Define message delete payload. """
    hostidx: int
    msgidx: int

@app.post("/api/generator/message/delete", response_class=JSONResponse)
def generator_message_delete(query: GeneratorMessageDelete):
    """ Delete message from host. """
    ret = rpool.json().arrpop("generator:config", f"$.hosts[{query.hostidx}].messages", query.msgidx)
    return JSONResponse(ret)

class GeneratorMessageModify(BaseModel):
    """ Define message modify payload. """
    hostidx: int
    msgidx: int
    message: str

@app.post("/api/generator/message/modify", response_class=JSONResponse)
def generator_message_modify(query: GeneratorMessageModify):
    """ Modify message on host. """
    ret = rpool.json().set("generator:config", f"$.hosts[{query.hostidx}].messages[{query.msgidx}]", query.message)
    return JSONResponse(ret)

class GeneratorConfig(BaseModel):
    """ Define generator config payload as dict. """
    config: list

@app.post("/api/generator/config/update", response_class=JSONResponse)
def generator_config_write(query: GeneratorConfig):
    """ Replace configuration. """
    ret = rpool.json().set("generator:config", "$.hosts", query.config)
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
def generator_host_add(query: GeneratorHostAdd):
    """ Add host to generator configuration. """
    ret = rpool.json().arrappend("generator:config", f"$.hosts", query.dict())
    return JSONResponse(ret)

def main():
    print(random_message())

if __name__ == '__main__':
    main()
