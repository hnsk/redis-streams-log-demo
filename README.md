# Redis Log streaming demo

Uses [FastAPI](https://fastapi.tiangolo.com/) for asynchronous web serving. Logging output is done over WebSockets.

Redis modules:
- [RedisGears](https://oss.redislabs.com/redisgears/) for splitting streams and storing the entries to hashes
- [RediSearch](https://oss.redislabs.com/redisearch/) for searching logs

## Installation

### Docker
```
docker-compose up
```

### Manually
Assumes redis-server (with RedisGears and RediSearch loaded) to be running in `localhost:6379`, to override set `REDIS_HOST` and `REDIS_PORT` environment variables.

```
pip install -r requirements.txt
# to run
uvicorn websocket:app
```
### Usage

Connect to http://yourhost:8000 and generate some logs.

#### Index
- Generate messages: generates n messages to stream "test"
- Reset counter: Resets the JavaScript counter
- Update available streams: If stream splitter is enabled, will refresh currently seen severity streams
- Register stream splitter: Registers RedisGears function to split "test" to streams for each severity and generates hashes for RedisSearch

#### RediSearch
- Search: If input is longer than 2 characters, every time the field is updated, it will perform RediSearch query with the input value
- If you enable auto-refresh then search is performed once a second