import time
from typing import Any, Hashable

class TTLCache:
    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._store = {}

    def get(self, key: Hashable) -> Any:
        now = time.time()
        if key in self._store:
            value, ts = self._store[key]
            if now - ts < self.ttl:
                return value
            else:
                del self._store[key]
        return None

    def set(self, key: Hashable, value: Any):
        self._store[key] = (value, time.time())

    def clear(self):
        self._store.clear() 