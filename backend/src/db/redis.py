from fastapi import Request
import redis
from os import environ

from src.db.db import get_client

class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db)

    def set(self, key, value, timeout=60):
        self.client.set(key, value, ex=timeout)

    def get(self, key):
        return self.client.get(key)

    def delete(self, key):
        self.client.delete(key)


redis_master = RedisClient(
    host=environ.get('REDIS_HOST', 'localhost'),
    port=int(environ.get('REDIS_PORT', 6379)),
    db=int(environ.get('REDIS_DB', 0))
)

redis_clients = {}

def get_redis_client(request: Request) -> RedisClient:
    # Parse the db_url to extract host, port, and db
    # For simplicity, we assume the db_url is in the format: redis://host:port/db
    client = get_client(request)
    db_url = client.redis_client
    try:
        _, rest = db_url.split("://")
        host_port, db = rest.split("/")
        host, port = host_port.split(":")
        if db_url not in redis_clients:
            redis_clients[db_url] = RedisClient(host=host, port=int(port), db=int(db))
        return redis_clients[db_url]
    except Exception as e:
        raise ValueError(f"Invalid Redis URL: {db_url}") from e
    