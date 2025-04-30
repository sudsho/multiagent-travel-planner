"""Startup environment validation.

Reads required + optional env vars and reports what's missing. Run this
during container start so misconfig fails fast instead of leaking through
to the first /plan request.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field


# at least one of these must be set
LLM_KEYS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")

# always required
REQUIRED = (
    "LLM_PROVIDER",
    "LLM_MODEL",
)

# strongly recommended in production
RECOMMENDED = (
    "OPENWEATHER_API_KEY",
    "AMADEUS_CLIENT_ID",
    "AMADEUS_CLIENT_SECRET",
    "GOOGLE_MAPS_API_KEY",
    "REDIS_URL",
)


@dataclass
class EnvReport:
    missing_required: list[str] = field(default_factory=list)
    missing_llm_key: bool = False
    missing_recommended: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.missing_required or self.missing_llm_key)

    def format(self) -> str:
        lines = []
        if self.missing_llm_key:
            lines.append("  no llm api key set: need one of " + ", ".join(LLM_KEYS))
        for k in self.missing_required:
            lines.append(f"  required env var missing: {k}")
        for k in self.missing_recommended:
            lines.append(f"  recommended env var missing: {k}")
        return "\n".join(lines) if lines else "  all env vars look ok"


def check_env(env: dict[str, str] | None = None) -> EnvReport:
    e = env if env is not None else dict(os.environ)
    rep = EnvReport()
    if not any(e.get(k) for k in LLM_KEYS):
        rep.missing_llm_key = True
    for k in REQUIRED:
        if not e.get(k):
            rep.missing_required.append(k)
    for k in RECOMMENDED:
        if not e.get(k):
            rep.missing_recommended.append(k)
    return rep


def main() -> int:
    rep = check_env()
    print("env check:")
    print(rep.format())
    if not rep.ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
