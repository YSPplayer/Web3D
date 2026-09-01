from cachetools import TTLCache
from threading import RLock
from copy import deepcopy
from System.log_manager import get_logger


logger = get_logger(__name__)

class CacheManager:
    def __init__(self, maxsize: int = 512, ttl: int = 60):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = RLock()

    def get(self,key):
        with self.lock:
            if key not in self.cache:
                return None
            logger.debug("缓存命中，key=%s", key)
            return deepcopy(self.cache[key])
    
    def set(self, key, value):
        with self.lock:
            self.cache[key] = deepcopy(value)
            logger.debug("缓存写入，key=%s", key)

    def delete(self, key):
        with self.lock:
            self.cache.pop(key, None)
            logger.debug("缓存删除，key=%s", key)

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
