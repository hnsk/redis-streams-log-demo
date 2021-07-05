# Redis Log streaming demo

Uses [FastApi](https://fastapi.tiangolo.com/) for asynchronous web serving. All communication is done over WebSockets.

## Installation

### Docker
```
docker-compose up
```

### Manually
Assumes redis-server to be running in `localhost:6379`, to override set `REDIS_HOST` and `REDIS_PORT` environment variables.

```
pip install -r requirements.txt
# to run
uvicorn websocket:app
```
### Usage

Connect to `http://localhost:8000` and generate some logs.
