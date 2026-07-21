from cachetools import TTLCache
from threading import RLock
from copy import deepcopy

class CacheManager:
    def __init__(self, maxsize: int = 512, ttl: int = 60):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = RLock()

    def get(self,key):
        with self.lock:
            if key not in self.cache:
                return None
            print(f'已读取缓存 key{key},value{self.cache[key]}')
            return deepcopy(self.cache[key])
    
    def set(self, key, value):
        with self.lock:
            self.cache[key] = deepcopy(value)
            print(f'已存储缓存 key{key},value{self.cache[key]}')

    def delete(self, key):
        with self.lock:
            self.cache.pop(key, None)
            print(f'已删除缓存 key{key}')

    def delete_prefix(self, prefix: tuple):
         with self.lock:
            keys = list(self.cache.keys())
            for key in keys:
                if isinstance(key, tuple) and key[:len(prefix)] == prefix:
                    self.cache.pop(key, None)

    def clear(self):
        with self.lock:
            self.cache.clear()

cache_manager = CacheManager(maxsize=512, ttl=60)