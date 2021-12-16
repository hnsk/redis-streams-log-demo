#!/usr/bin/env python

import json
from datetime import datetime
from random import choice, choices, randint
from time import time, sleep
import aioredis

REDIS_HOST = "127.0.0.1"

LOG_LEVELS = [
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL"
]

HOSTS = [f"server-{x}.mega-server-fleet.tld" for x in range(1000)]

MESSAGES = [
    "Hello!",
    "Not feeling so great!",
    "All is fine",
    "What am I even doing here?",
    "What is the meaning of life?",
    "How many of these do we need really?",
    "Lorem ipsum etc."
]

def random_message():
    """ Generate random log message with weighted log severities"""
    message = {}
    message['timestamp'] = datetime.now().isoformat()
    message['hostname'] = choice(HOSTS)
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
    message['message'] = choice(MESSAGES)
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
