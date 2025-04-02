"""SQLite-backed cache with TTL. Optional Redis backend."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional


class Cache:
    """tiny key-value cache with TTL."""

    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError


class SQLiteCache(Cache):
    def __init__(self, path: str = ".cache/travel.db"):
        self.path = path
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS kv ("
            "  k TEXT PRIMARY KEY,"
            "  v TEXT NOT NULL,"
            "  expires_at REAL NOT NULL"
            ")"
        )
        self._conn.commit()

    def get(self, key: str) -> Optional[Any]:
        row = self._conn.execute(
            "SELECT v, expires_at FROM kv WHERE k = ?", (key,)
        ).fetchone()
        if not row:
            return None
        v, exp = row
        if exp < time.time():
            self.delete(key)
            return None
        return json.loads(v)

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        exp = time.time() + ttl
        self._conn.execute(
            "INSERT OR REPLACE INTO kv (k, v, expires_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), exp),
        )
        self._conn.commit()

    def delete(self, key: str) -> None:
        self._conn.execute("DELETE FROM kv WHERE k = ?", (key,))
        self._conn.commit()


class RedisCache(Cache):
    def __init__(self, url: str = "redis://localhost:6379/0"):
        import redis  # lazy
        self._r = redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        v = self._r.get(key)
        return json.loads(v) if v else None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        self._r.set(key, json.dumps(value), ex=ttl)

    def delete(self, key: str) -> None:
        self._r.delete(key)


def make_cache(backend: str | None = None) -> Cache:
    backend = (backend or os.getenv("CACHE_BACKEND") or "sqlite").lower()
    if backend == "redis":
        return RedisCache(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    return SQLiteCache(os.getenv("SQLITE_CACHE_PATH", ".cache/travel.db"))
