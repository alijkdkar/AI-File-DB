import redis


class mRedis:
    _redis = None

    def __init__(self):
        if self._redis == None:
            self._redis = redis.Redis(host="127.0.0.1",port="6379",db=0)
        else:
             self._redis

    # def GetInstance(self):
    #     if self._redis == None:
    #         redis1 = redis.Redis(host="127.0.0.1",port="6379",db=0)
    #     else:
    #         return self._redis
    #     return redis1