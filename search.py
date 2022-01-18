#!/usr/bin/env python

from os import environ
from typing import List, Tuple
import redis

from redis.commands.search import reducers
from redis.commands.search.aggregation import AggregateRequest, Asc, Desc
from redis.commands.search.commands import Query
from redis.commands.search.field import TextField, TagField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.suggestion import Suggestion

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = int(environ.get('REDIS_PORT') or 6379)
REDIS_CONSUMER_GROUP = environ.get('REDIS_CONSUMER_GROUP') or 'testgroup'
REDIS_STREAM_NAME = environ.get('REDIS_STREAM_NAME') or 'test'

LOG_SCHEMA = (
    #TextField("$.timestamp", as_name="timestamp", sortable=True, no_stem=True),
    NumericField("$.timestamp", as_name="timestamp", sortable=True),
    TextField("$.hostname", as_name="hostname", sortable=True),
    TagField("$.log_level", as_name="log_level"),
    TextField("$.message", as_name="message")
)

LOG_PREFIX = ["logs:"]
IDX_NAME = "jsonIdx"

AUTOCOMPLETE_DEFAULTS = [
    "@log_level:",
    "@hostname:",
    "@timestamp:",
    "@message:",
    "mail",
    "example",
    "request",
    "status"
]

redisconn = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

client = redisconn.ft(
    index_name=IDX_NAME,
)

def create_index(
    idx_schema: Tuple = LOG_SCHEMA,
    idx_prefix: List = LOG_PREFIX
    ):
    """ Create index if it doesn't exist. """

    definition = IndexDefinition(
        prefix=idx_prefix,
        index_type=IndexType.JSON
        )
    try:
        client.info()
    except redis.exceptions.ResponseError:
        client.create_index(idx_schema, definition=definition)
    

def search_index(query: str, limit: int = 100):
    """ Search for query from index. """

    count = 0
    while True:
        request = (
            Query(f"{query}")
            .sort_by("timestamp", asc=False)
            .paging(count, 100)
            .highlight()
            .return_fields(
                "timestamp",
                "hostname",
                "log_level",
                "message"
            )
        )

        literal_query = f"FT.SEARCH {IDX_NAME} \"{request.query_string()}\" {' '.join([str(x) for x in request.get_args()[1:]])}"
        res = client.search(request)
        yield res, literal_query
        count += 100
        if len(res.docs) == 0 or count >= limit:
            return res, literal_query
        

def aggregate_by_field(query: str, field: str):
    """ Aggregate counts for query and group by field. """

    request = (
        AggregateRequest(query)
        .group_by(
            f"@{field}",
            reducers
            .count()
            .alias("entries")
        )
        .sort_by(Desc("@entries"))
    )

    literal_query = f"FT.AGGREGATE {IDX_NAME} \"{request.build_args()[0]}\" {' '.join([str(x) for x in request.build_args()[1:]])}"
    res = None
    while True:
        res = client.aggregate(request)
        yield res, literal_query
        if not res.cursor:
            break
    return res, literal_query

def autocomplete_suggestion_add(idx: str, string: str, score: float = 1, increment=True):
    sug = Suggestion(string=string, score=score)
    res = redisconn.ft().sugadd(idx, sug, increment=increment)
    return res

def autocomplete_suggestion_get(idx: str, prefix: str, num: int = 5):
    res = redisconn.ft().sugget(key=idx, prefix=prefix, num=num)
    res = [x.string for x in res]
    return res

def autocomplete_add_defaults():
    for prefix in AUTOCOMPLETE_DEFAULTS:
        autocomplete_suggestion_add("autocomplete", prefix, 1)

def autocomplete_delete(idx: str):
    redisconn.delete(idx)

def get_tagvals(field: str):
    res = client.tagvals(tagfield=field)
    return res

def main():
    create_index()
    for result, rawquery in aggregate_by_field("*", "log_level"):
        for row in result.rows:
            print(row)

    counter = 0
    duration = 0
    for result, rawquery in search_index("*", 100):
        for subres in result.docs:
            print(subres.id)
            print(subres.message)
            print(result.total)
            counter += 1
        duration += result.duration
    print(f"Got {counter} results in {duration:.2f}ms")
    print(autocomplete_suggestion_add("autocomplete", "male", 1))
    print(autocomplete_suggestion_get("autocomplete", "m"))
    print(get_tagvals("log_level"))
    info = redisconn.info()
    print(f"used_memory: {info['used_memory']}")
    print(f"keys: {info['db0']['keys']}")

if __name__ == '__main__':
    main()