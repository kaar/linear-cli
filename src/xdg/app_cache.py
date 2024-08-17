import json
import os
import time
from pathlib import Path
from typing import Optional


XDG_CACHE_HOME = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
DEFAULT_CACHE_LIMIT = 30


def cache_file(app_name: str, key: str) -> Path:
    return Path(XDG_CACHE_HOME, app_name, f"{key}.json")


def load_json_cache_file(path: Path, ttl: int = DEFAULT_CACHE_LIMIT) -> Optional[dict]:
    if not path.exists():
        return None
    creation_time = path.stat().st_mtime
    if time.time() - creation_time > ttl:
        path.unlink()
        return None
    return json.loads(path.read_text())


def dump_json_cache_file(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


class XDGAppCache:
    def __init__(self, app_name: str):
        self.app_name = app_name

    def load(self, key: str, ttl: int = DEFAULT_CACHE_LIMIT) -> Optional[dict]:
        return load_json_cache_file(cache_file(self.app_name, key), ttl)

    def save(self, key: str, data: dict):
        dump_json_cache_file(cache_file(self.app_name, key), data)
