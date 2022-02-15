#!/usr/bin/env python

from os import environ
from typing import List, Tuple
from pydantic import BaseModel

import redis

from redis.commands.search import reducers
from redis.commands.search.aggregation import AggregateRequest, Asc, Desc
from redis.commands.search.commands import Query
from redis.commands.search.field import TextField, TagField, NumericField, GeoField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.suggestion import Suggestion

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

REDIS_HOST = environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = int(environ.get('REDIS_PORT') or 6379)
REDIS_CONSUMER_GROUP = environ.get('REDIS_CONSUMER_GROUP') or 'testgroup'
REDIS_STREAM_NAME = environ.get('REDIS_STREAM_NAME') or 'test'

LOG_SCHEMA = (
    NumericField("$.timestamp", as_name="timestamp", sortable=True),
    TextField("$.hostname", as_name="hostname", sortable=True),
    TagField("$.log_level", as_name="log_level"),
    TextField("$.message", as_name="message"),
    TagField("$.country_code", as_name="country_code"),
    TagField("$.city", as_name="city"),
    GeoField("$.coordinates", as_name="coordinates")
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

rpool = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

client = rpool.ft(
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

def generate_literal_query(cmd: str, idx: str, build_args):
    """ Return literal query. """
    literal_query = [cmd, idx]
    for elem in build_args:
        if len(elem.split(" ")) > 1:
            literal_query.append(f'"{elem}"')
        else:
            literal_query.append(elem)
    
    return ' '.join(literal_query)

def search_index(query: str, start: int = 0, limit: int = 100, sortby_field: str = "timestamp", sort_asc: bool = False):
    """ Search for query from index. """

    while True:
        request = (
            Query(f"{query}")
            .sort_by(sortby_field, asc=sort_asc)
            .paging(start, limit)
            .highlight()
            .return_fields(
                "timestamp",
                "hostname",
                "log_level",
                "message",
                "coordinates",
                "city",
                "country_code"
            )
        )

        literal_query = f"FT.SEARCH {IDX_NAME} \"{request.query_string()}\" {' '.join([str(x) for x in request.get_args()[1:]])}"
        res = client.search(request)
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

    literal_query = generate_literal_query("FT.AGGREGATE", IDX_NAME, request.build_args())
    res = None
    while True:
        res = client.aggregate(request)
        yield res, literal_query
        if not res.cursor:
            break
    return res, literal_query


def get_cities_aggregate_by_coordinates(coordinates: str, distance: int, query: str = '*'):
    """ Get cities """

    request = (
        AggregateRequest(query)
        .load("coordinates")
        .apply(distance=f"geodistance(@coordinates, {coordinates})/1000")
        .group_by(
            ["@city", "@distance", "@country_code", "@coordinates"],
            reducers
            .count()
            .alias("entries")
        )
        .filter(f"@distance < {distance}")
        .sort_by("@distance")
        .limit(0, 250)
    )
    literal_query = generate_literal_query("FT.AGGREGATE", IDX_NAME, request.build_args())
    res = None
    res = client.aggregate(request)
    return res, literal_query


def autocomplete_suggestion_add(idx: str, string: str, score: float = 1, increment=True):
    sug = Suggestion(string=string, score=score)
    res = rpool.ft().sugadd(idx, sug, increment=increment)
    return res

def autocomplete_add_defaults():
    for prefix in AUTOCOMPLETE_DEFAULTS:
        autocomplete_suggestion_add("autocomplete", prefix, 1)

def autocomplete_delete(idx: str):
    rpool.delete(idx)

### FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """ Initialize config on startup. """
    autocomplete_delete("autocomplete")
    autocomplete_add_defaults()
    create_index()

class SearchQuery(BaseModel):
    """ Search query definition. Accepted parameters are a query string. """
    query: str
    start: int = 0
    limit: int = 25
    sortby: str = "timestamp"
    sort_asc: bool = False

@app.post("/api/search", response_class=JSONResponse)
def search_string(query: SearchQuery):
    """ Search string from logs and return results and information. """

    results = {}
    results['total'] = 0
    results['duration'] = 0
    results['messages'] = []
    results['literal_query'] = ""
    results['error'] = ""
    try:
        res, literal_query = search_index(
                                          query=query.query,
                                          start=query.start,
                                          limit=query.limit,
                                          sortby_field=query.sortby,
                                          sort_asc=query.sort_asc)
        results['total'] = res.total
        results['duration'] += res.duration
        results['literal_query'] = literal_query
        for doc in res.docs:
            results['messages'].append({
                "id": doc.id,
                "hostname": doc.hostname,
                "timestamp": doc.timestamp,
                "message": doc.message,
                "log_level": doc.log_level,
                "city": doc.city,
                "country_code": doc.country_code,
                "coordinates": doc.coordinates
            })
    except redis.exceptions.ResponseError:
        print(f"invalid query {query.query}")
        results['error'] = f"Invalid query {query.query}"
    results['duration'] = f"{results['duration']:.2f}"
    results['numresults'] = len(results['messages'])
    return JSONResponse(results)

class AggregateQuery(BaseModel):
    """
    Aggregate query definition.
    Accepts query string and field to aggregate on.
    """

    query: str
    field: str

@app.post("/api/search/aggregate", response_class=JSONResponse)
def search_aggregate_by_fields(query: AggregateQuery):
    """ Aggregate log severities based on the provided query. """

    result = {}
    result["results"] = []
    result["literal_query"] = ""
    result["error"] = ""
    try:
        for res, literal_query in aggregate_by_field(query.query, query.field):
            result["literal_query"] = literal_query
            for row in res.rows:
                result["results"].append({
                    "field": row[1],
                    "entries": row[3]
                })
    except redis.exceptions.ResponseError:
        print(f"invalid query {query.query}")
        result["error"] = f"Invalid query {query.query}"

    return JSONResponse(result)

class CitiesAggregateQuery(BaseModel):
    """ Cities Aggregate query.
    Receives coordinates and distance. Optionally query string. """
    coordinates: str
    distance: int
    query: str = '*'

@app.post("/api/search/aggregate/cities", response_class=JSONResponse)
def get_cities_by_coordinates(query: CitiesAggregateQuery):
    """ Get cities within specified distance of given coordinates"""
    result = {}
    result["results"] = []
    result["literal_query"] = ""
    result["error"] = ""

    res, literal_query = get_cities_aggregate_by_coordinates(
        coordinates=query.coordinates,
        distance=query.distance,
        query=query.query)

    result["literal_query"] = literal_query
    for row in res.rows:
        result["results"].append({
            "city": row[1],
            "distance": row[3],
            "country_code": row[5],
            "coordinates": row[7],
            "entries": row[9]
        })
    return JSONResponse(result)

class SuggestionQuery(BaseModel):
    """ Autocomplete suggestion query payload. """
    index: str
    prefix: str

@app.post("/api/search/suggestion/get", response_class=JSONResponse)
def get_autocomplete_suggestion(query: SuggestionQuery):
    """ Get autocompletion suggestion for prefix. """
    res = rpool.ft().sugget(key=query.index, prefix=query.prefix, num=5)
    res = [x.string for x in res]
    return JSONResponse(res)

class AutocompletePrefix(BaseModel):
    """ Autocomplete prefix definition. """
    prefix: str

@app.post("/api/search/suggestion/add", response_class=JSONResponse)
def add_autocomplete_suggestion(query: AutocompletePrefix):
    """ Add autocomplete suggestion. """
    return autocomplete_suggestion_add("autocomplete", query.prefix)

class TagValsQuery(BaseModel):
    """ Tagvals query payload. """
    field: str

@app.post("/api/search/tagvals/get", response_class=JSONResponse)
def get_tagvals(query: TagValsQuery):
    """ Get tagvals for indexed field. """
    res = client.tagvals(tagfield=query.field)
    return JSONResponse(res)

def main():
    res, literal_query = search_index(query="mail", start=5, limit=5)
    for doc in res.docs:
        print(doc.id)
    
    result = {}
    result["results"] = []
    result["literal_query"] = ""
    result["error"] = ""

    res, literal_query = get_cities_aggregate_by_coordinates(coordinates="24.933,60.16666", distance=400)
    result["literal_query"] = literal_query
    for row in res.rows:
        result["results"].append({
            "city": row[1],
            "distance": row[3],
            "coordinates": row[5],
            "entries": row[7]
        })

    print(result)

if __name__ == '__main__':
    main()