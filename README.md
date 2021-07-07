# Redis Log streaming demo

Uses [FastAPI](https://fastapi.tiangolo.com/) for asynchronous web serving. All communication is done over WebSockets.

Uses [RedisGears](https://oss.redislabs.com/redisgears/) for splitting streams.

## Installation

### Docker
```
docker-compose up
```

### Manually
Assumes redis-server (with RedisGears lodaded) to be running in `localhost:6379`, to override set `REDIS_HOST` and `REDIS_PORT` environment variables.

```
pip install -r requirements.txt
# to run
uvicorn websocket:app
```
### Usage

Connect to <http://localhost:8000> and generate some logs.
