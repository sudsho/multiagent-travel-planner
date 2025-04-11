"""structured logging setup for agents + tools."""
from __future__ import annotations

import json
import logging
import os
import sys
import time


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": int(time.time() * 1000),
            "lvl": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for k in ("agent", "tool", "lat_ms", "cache_hit"):
            if k in record.__dict__:
                payload[k] = record.__dict__[k]
        return json.dumps(payload, ensure_ascii=False)


def configure(level: str | None = None) -> None:
    lvl = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(lvl)
