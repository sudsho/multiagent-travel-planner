import os
import tempfile
import time

from src.cache import SQLiteCache


def test_set_get(tmp_path):
    c = SQLiteCache(str(tmp_path / "t.db"))
    c.set("a", {"x": 1}, ttl=10)
    assert c.get("a") == {"x": 1}


def test_ttl_expiry(tmp_path, monkeypatch):
    c = SQLiteCache(str(tmp_path / "t.db"))
    c.set("a", "v", ttl=1)
    assert c.get("a") == "v"
    # patch time to simulate expiry
    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + 5)
    assert c.get("a") is None


def test_delete(tmp_path):
    c = SQLiteCache(str(tmp_path / "t.db"))
    c.set("k", 1, ttl=60)
    c.delete("k")
    assert c.get("k") is None


def test_overwrite(tmp_path):
    c = SQLiteCache(str(tmp_path / "t.db"))
    c.set("k", 1, ttl=60)
    c.set("k", 2, ttl=60)
    assert c.get("k") == 2
