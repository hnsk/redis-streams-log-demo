#!/usr/bin/env python

from datetime import datetime
from random import choice, randint
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
    message = {}
    message['timestamp'] = datetime.now().isoformat()
    message['hostname'] = choice(HOSTS)
    message['log_level'] = choice(LOG_LEVELS)
    message['message'] = choice(MESSAGES)
    return message

async def add_message(r, stream="test"):
    message = random_message()
    ret = await r.xadd(
        name=stream,
        fields=message,
        maxlen=200000,
        approximate=True
    )
    return ret

# if __name__ == '__main__':
#     r = aioredis.Redis(host=REDIS_HOST)
#     for x in range(10000):
#         #message = random_message()
#         id = await add_message(r)
#         #print(f"{message} stored as {id}")
#         print(x)
#         #sleep(randint(0,100) / 1000)