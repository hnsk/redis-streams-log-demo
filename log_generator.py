#!/usr/bin/env python

import json, time
from datetime import datetime
from os import environ
from random import choice, choices, randint
from typing import Optional, List

import redis

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = int(environ.get('REDIS_PORT') or 6379)

#if not environ.get('REDIS_OM_URL'):
#    environ['REDIS_OM_URL'] = f'redis://@{REDIS_HOST}:{REDIS_PORT}/'

#from redis_om import (
#    EmbeddedJsonModel,
#    JsonModel
#)

redis_conn = redis.Redis(
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

#class Host(EmbeddedJsonModel):
#    hostname: str
#    enabled: bool
#    amount: int
#    messages: List[str]

#class Configuration(JsonModel):
#    hosts: List[Host]

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


def init_config():
    """ Init configuration for generator. """
    ret = redis_conn.json().set("generator:config", "$", INITIAL_CONFIGURATION)
    return ret

def get_config():
    """ Retrieve full configuration. """
    config = redis_conn.json().get("generator:config")
    return config

def add_message_to_host(hostidx, message):
    ret = redis_conn.json().arrappend("generator:config", f"$.hosts[{hostidx}].messages", message)
    return ret

def delete_message_from_host(hostidx, msgidx):
    ret = redis_conn.json().arrpop("generator:config", f"$.hosts[{hostidx}].messages", msgidx)
    return ret

def modify_message_on_host(hostidx, msgidx, message):
    ret = redis_conn.json().set("generator:config", f"$.hosts[{hostidx}].messages[{msgidx}]", message)
    return ret

def write_config(config):
    ret = redis_conn.json().set("generator:config", "$.hosts", config)
    return ret

def add_host(config):
    ret = redis_conn.json().arrappend("generator:config", f"$.hosts", config)
    return ret

def random_message():
    config = get_config()

    hostconfig = choice([host for host in filter(lambda x: x["options"]["enabled"], config["hosts"])])

    hostname = hostconfig["options"]["hostname"].replace('RANDINT', str(randint(1, int(hostconfig["options"]["amount"]))))

    message = {}
    #message['timestamp'] = datetime.now().isoformat()
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
