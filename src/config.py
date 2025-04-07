"""yaml config loader."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(name: str = "default") -> dict[str, Any]:
    base = Path(__file__).resolve().parent.parent / "configs"
    path = base / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def deep_merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out
