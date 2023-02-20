import redis


class mRedis:
    _redis :redis.Redis = None

    def __init__(self):
        if self._redis == None:
            self._redis = redis.Redis(host="127.0.0.1",port="6379",db=0)
        else:
             self._redis