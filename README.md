# Redis Log streaming demo

Uses [FastAPI](https://fastapi.tiangolo.com/) for asynchronous web serving. Logging output is done over WebSockets.

Frontend is built on [Quasar](https://quasar.dev/).

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
Requires npm/Quasar environment etc. Just use Docker :)

### Gitpod
You can also spawn the deployment on https://gitpod.io/

https://gitpod.io/#https://github.com/hnsk/redis-streams-log-demo


### Usage

Connect to http://yourhost:8000 and generate some logs.

RedisInsight is also available at http://yourhost:8001

#### Stream viewer
- Shows latest 25 log messages from streams.
- Generate messages: generates n messages to stream "test"
- Register stream splitter: Registers RedisGears function to split "test" to streams for each severity and stores the JSON events for RedisSearch

#### Search Logs
- Search: If input is longer than 2 characters, every time the field is updated, it will perform RediSearch query with the input value
- Autocompletion is enabled for some hardcoded keys
- Fields can be modified. Uses RedisJSON in the background, changes are automatically indexed.

### Generator
- Allows specifying generator configuration
- RANDINT gets converted to 1..amount
- Some changes require manual Save config to be updated
- Messages are modified directly with RedisJSON commands
