import hashlib
import json
import os
import time
from typing import Optional

from .constants import XDG_CACHE_HOME


class XDGAppCache:
    """
    A cache for application data.

    The cache is stored in the XDG cache directory. (XDG_CACHE_HOME)
    Creates a directory for the application if it does not exist.
    """

    DEFAULT_CACHE_LIMIT = 30

    def __init__(self, app_name: str):
        """
        Initialize the cache by creating the application directory under
        `XDG_CACHE_HOME/app_name`.

        Args:
            app_name: The name of the application.
        """
        self.app_name = app_name

    def load(self, query: str, ttl: int = DEFAULT_CACHE_LIMIT) -> Optional[dict]:
        """
        Load a cached query.

        Args:
            query: The query to load.
            ttl: The time to live of the cache in seconds.
        """
        hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        cache_path = os.path.join(XDG_CACHE_HOME, self.app_name, f"{hash}.json")

        if os.path.exists(cache_path):
            creation_time = os.path.getctime(cache_path)
            if time.time() - creation_time > ttl:
                os.remove(cache_path)
                return
            else:
                with open(cache_path, "r") as f:
                    return json.load(f)

    def save(self, query: str, data: dict):
        """
        Save a query to cache.

        Args:
            query: The query to save.
            data: The data to save.
        """
        hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        cache_path = os.path.join(XDG_CACHE_HOME, self.app_name, f"{hash}.json")

        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(data, f)
