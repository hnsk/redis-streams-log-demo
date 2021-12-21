# Redis Log streaming demo

Uses [FastAPI](https://fastapi.tiangolo.com/) for asynchronous web serving. Logging output is done over WebSockets.

Redis modules:
- [RedisGears](https://oss.redislabs.com/redisgears/) for splitting streams and storing the entries to hashes
- [RedisJSON 2.0+](https://oss.redis.com/redisjson/)
- [RediSearch 2.2+](https://oss.redislabs.com/redisearch/) for searching logs

## Installation

### Docker
```
docker-compose up
```

### Manually
Assumes redis-server (RedisGears, RedisJSON 2.0+ and RediSearch 2.2+ modules loaded) to be running in `localhost:6379`, to override set `REDIS_HOST` and `REDIS_PORT` environment variables.

```
pip install -r requirements.txt
# to run
uvicorn websocket:app
```

### Gitpod
You can also spawn the deployment on https://gitpod.io/

https://gitpod.io/#https://github.com/hnsk/redis-streams-log-demo


### Usage

Connect to http://yourhost:8000 and generate some logs.

RedisInsight is also available at http://yourhost:8001

#### Index
- Generate messages: generates n messages to stream "test"
- Reset counter: Resets the JavaScript counter
- Update available streams: If stream splitter is enabled, will refresh currently seen severity streams
- Register stream splitter: Registers RedisGears function to split "test" to streams for each severity and stores the JSON events for RedisSearch

#### RediSearch
- Search: If input is longer than 2 characters, every time the field is updated, it will perform RediSearch query with the input value
- If you enable auto-refresh then search is performed once a second
- Timestamp is a link to the JSON key directly