import redis
from os import environ

class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db)

    def set(self, key, value, timeout=60):
        self.client.set(key, value, ex=timeout)

    def get(self, key):
        return self.client.get(key)

    def delete(self, key):
        self.client.delete(key)


redis_client = RedisClient(
    host=environ.get('REDIS_HOST', 'localhost'),
    port=int(environ.get('REDIS_PORT', 6379)),
    db=int(environ.get('REDIS_DB', 0))
)