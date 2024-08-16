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

    def load(self, key: str, ttl: int = DEFAULT_CACHE_LIMIT) -> Optional[dict]:
        """
        Load a cached query.

        Args:
            query: The query to load.
            ttl: The time to live of the cache in seconds.
        """
        path = os.path.join(XDG_CACHE_HOME, self.app_name, f"{key}.json")

        if os.path.exists(path):
            creation_time = os.path.getctime(path)
            if time.time() - creation_time > ttl:
                os.remove(path)
                return
            else:
                with open(path, "r") as f:
                    return json.load(f)

    def save(self, key: str, data: dict):
        """
        Save a query to cache.

        Args:
            query: The query to save.
            data: The data to save.
        """
        path = os.path.join(XDG_CACHE_HOME, self.app_name, f"{key}.json")

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)
