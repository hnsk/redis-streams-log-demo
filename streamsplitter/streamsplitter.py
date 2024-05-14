import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from os import environ
from time import time

import redis.asyncio
import redis.exceptions

from fastapi import FastAPI, BackgroundTasks
from redis import ResponseError

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = int(environ.get('REDIS_PORT') or '6379')
REDIS_CONSUMER_GROUP = environ.get('REDIS_CONSUMER_GROUP') or 'streamsplitter'
REDIS_STREAM_NAME = environ.get('REDIS_STREAM_NAME') or 'test'

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

@app.on_event("startup")
async def startup_event():
    """ Initialise Redis database on server startup. """

    try:
        # Create consumer group
        await rpool.xgroup_create(
            name=REDIS_STREAM_NAME,
            groupname=REDIS_CONSUMER_GROUP,
            mkstream = True
        )
    except ResponseError:
        print("Consumer group already exists.")
    await rpool.set("stream_splitter", 0)
    asyncio.create_task(read_streams())

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """ Disconnect all active connections on shutdown. """
    await rpool.set("stream_splitter", 0)


async def split_by_severity(id, payload):
    event = json.loads(payload["json"])
    severity_stream = f"{event['log_level'].lower()}"
    beginning_of_today = datetime.today().date().strftime('%s')
    await rpool.xadd(
        name=severity_stream,
        id='*',
        fields={'json': payload["json"]},
        maxlen=2000000,
        approximate=True
    )

    sev_count = await rpool.zincrby(
        name='severities',
        amount=1,
        value=severity_stream
    )

    await rpool.ts().add(
        f"ts:{severity_stream}",
        '*',
        sev_count,
        labels={'log_level': severity_stream, 'type': 'logs'},
        duplicate_policy="LAST"
    )

    await rpool.json().set(
        f"logs:{beginning_of_today}:{id}",
        '$',
        event
    )

async def read_streams():
    """ Read entries from subscribed streams for client_id. """

    consumername = f"{REDIS_CONSUMER_GROUP}-streamreader"
    stream_id = ">"
    while True:
        splitter_enabled = await rpool.get("stream_splitter")
        if splitter_enabled == "0":
            await asyncio.sleep(0.5)
            continue
        data = await rpool.xreadgroup(
            groupname=REDIS_CONSUMER_GROUP,
            consumername=consumername,
            streams={REDIS_STREAM_NAME: ">"},
            count=100,
            block=1000)
        if len(data) > 0:
            for batch in data:
                stream_name = batch[0]
                for entry in batch[1]:
                    stream_id = entry[0]
                    stream_payload = entry[1] # json
                    await split_by_severity(stream_id, stream_payload)
                    await rpool.xack(
                        stream_name, # Stream name
                        REDIS_CONSUMER_GROUP,
                        stream_id # Stream ID
                    )
        #except redis.exceptions.DataError:
        #    # If no streams are being consumed just return and try again later
        #    pass


