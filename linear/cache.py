import hashlib
import json
import os
import time
from pathlib import Path
from typing import Protocol


class Cache(Protocol):
    def get(self, key: str) -> dict | None: ...

    def set(self, key: str, data: dict): ...


class XDGCache(Cache):
    """
    A simple cache implementation that stores data in the XDG_CACHE_HOME directory.
    """

    def __init__(self, app_name: str):
        self._cache_dir = Path(
            os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"), app_name
        )
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict | None:
        return self._query_cache_load(key)

    def set(self, key: str, data: dict):
        self._query_cache_dump(key, data)

    def _query_cache_file(self, query: str) -> Path:
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        return Path(self._cache_dir, f"{query_hash}.json")

    def _query_cache_load(self, query: str, ttl: int = 30) -> dict | None:
        cache_file = self._query_cache_file(query)
        if not cache_file.exists():
            return None
        creation_time = cache_file.stat().st_mtime
        if time.time() - creation_time > ttl:
            cache_file.unlink()
            return None
        return json.loads(cache_file.read_text())

    def _query_cache_dump(self, query: str, data: dict):
        cache_file = self._query_cache_file(query)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data))
