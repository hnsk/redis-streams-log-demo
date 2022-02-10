#!/usr/bin/env python

from os import environ
from typing import Any, List, Union
from pydantic import BaseModel

import redis

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = int(environ.get('REDIS_PORT') or 6379)

rpool = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

def get_mrange(
        from_time: Union[int, str],
        to_time: Union[int, str],
        filters: List[str],
        aggregation_type: str,
        bucket_size_msec: int
    ) -> List:
    """ Get TS.MRANGE """

    res = rpool.ts().mrange(
        from_time=from_time,
        to_time=to_time,
        filters=filters,
        aggregation_type=aggregation_type,
        bucket_size_msec=bucket_size_msec,
        with_labels=True,
        align=to_time
    )

    result = []
    for series in res:
        for level, data in series.items():
            series = {
                'name': data[0]['log_level'],
                'data': []
            }
            for entry in data[1]:
                series['data'].append({
                    'x': entry[0],
                    'y': entry[1]
                })
            result.append(series)
    return result

### FastAPI

app = FastAPI()

class TimeSeriesMrangeQuery(BaseModel):
    """ TS.MRANGE query definition. """
    from_time: Any = "-"
    to_time: Any = "+"
    aggregation_type: str = "count"
    bucket_size_msec: int = 1000
    filters: List[str] = ["type=logs"]

@app.post("/api/timeseries/mrange", response_class=JSONResponse)
def timeseries_mrange(query: TimeSeriesMrangeQuery):
    """ Get TS.MRANGE results. """
    result = get_mrange(
        from_time=query.from_time,
        to_time=query.to_time,
        aggregation_type=query.aggregation_type,
        bucket_size_msec=query.bucket_size_msec,
        filters=query.filters
    )

    return result

def main():
    """Main. """
    #get_mrange()

if __name__ == '__main__':
    main()