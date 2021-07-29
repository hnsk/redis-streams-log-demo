#!/usr/bin/env python

from os import environ
from typing import List, Tuple
from redis import ResponseError
from redisearch import Client, Query, reducers
from redisearch.aggregation import AggregateRequest, Asc, Desc
from redisearch.client import IndexDefinition, TagField, TextField

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = environ.get('REDIS_PORT') or '6379'
REDIS_CONSUMER_GROUP = environ.get('REDIS_CONSUMER_GROUP') or 'testgroup'
REDIS_STREAM_NAME = environ.get('REDIS_STREAM_NAME') or 'test'

LOG_SCHEMA = (
    TextField("timestamp", sortable=True, no_stem=True),
    TextField("hostname", sortable=True),
    TagField("log_level"),
    TextField("message")
)

LOG_PREFIX = ["logs:"]

client = Client(
    'logIdx',
    host=REDIS_HOST,
    port=REDIS_PORT
)

def create_index(
    idx_schema: Tuple = LOG_SCHEMA,
    idx_prefix: List = LOG_PREFIX
    ):
    """ Create index if it doesn't exist. """

    definition = IndexDefinition(prefix=idx_prefix)
    try:
        client.info()
    except  ResponseError:
        client.create_index(idx_schema, definition=definition)
    

def search_index(query: str, limit: int = 100):
    """ Search for query from index. """

    count = 0
    while True:
        request = Query(f"{query}").sort_by("timestamp", asc=False).paging(count, 100).highlight()
        literal_query = f"FT.SEARCH logIdx \"{request.query_string()}\" {' '.join([str(x) for x in request.get_args()[1:]])}"
        res = client.search(request)
        yield res, literal_query
        count += 100
        if len(res.docs) == 0 or count >= limit:
            return res, literal_query
        

def aggregate_by_field(query: str, field: str):
    """ Aggregate counts for query and group by field. """

    request = AggregateRequest(query).group_by(
        f"@{field}",
        reducers.count().alias("entries")
    ).sort_by(Desc("@entries"))
    literal_query = f"FT.AGGREGATE logIdx \"{request.build_args()[0]}\" {' '.join([str(x) for x in request.build_args()[1:]])}"
    res = None
    while True:
        res = client.aggregate(request)
        yield res, literal_query
        if not res.cursor:
            break
    return res, literal_query

if __name__ == '__main__':
    create_index()
    for result in aggregate_by_field("log_level"):
        for row in result.rows:
            print(row)

    counter = 0
    duration = 0
    for result in search_index("%hrre%", 100):
        for subres in result.docs:
            print(subres.message)
            print(result.total)
            counter += 1
        duration += result.duration
    print(f"Got {counter} results in {duration:.2f}ms")
    #print(search_index('*'))
