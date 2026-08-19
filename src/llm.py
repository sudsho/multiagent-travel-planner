"""provider-agnostic LLM wrapper."""
from __future__ import annotations

import json
import os
import re
from datetime import date, timedelta
from typing import Any, Optional


class LLMResponse:
    def __init__(self, text: str, raw: Any = None):
        self.text = text
        self.raw = raw


class LLM:
    """thin abstraction so agents don't bind directly to a SDK."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: Optional[Any] = None

    def _ensure_client(self):
        if self._client is not None:
            return
        if self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"unknown provider: {self.provider}")

    def complete(self, system: str, user: str) -> LLMResponse:
        self._ensure_client()
        if self.provider == "openai":
            res = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return LLMResponse(text=res.choices[0].message.content or "", raw=res)
        # anthropic
        res = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(blk.text for blk in res.content if getattr(blk, "type", None) == "text")
        return LLMResponse(text=text, raw=res)


_KNOWN_CITIES = (
    "lisbon", "porto", "madrid", "barcelona", "paris", "london", "amsterdam",
    "rome", "berlin", "tokyo", "kyoto", "osaka", "bangkok", "singapore",
    "delhi", "mumbai", "bangalore", "new york", "san francisco",
    "los angeles", "chicago", "louisville", "boston", "miami",
)

# a few casual aliases the deterministic parser understands
_CITY_ALIASES = {"sf": "san francisco", "nyc": "new york", "la": "los angeles"}


class MockLLM(LLM):
    """Deterministic, offline stand-in for a real provider.

    No network, no API key. It reads the *system* prompt to decide which agent
    role is calling and returns a rule-based response:

      - research role  -> STRICT JSON extracted from the raw trip request
      - summary role   -> a short plain-prose trip summary from the itinerary JSON

    This lets the whole planner -> researcher -> budgeter loop run end to end with
    an "LLM in the loop" while staying fully reproducible.
    """

    def __init__(self, model: str = "mock-deterministic-v1", **kwargs: Any):
        super().__init__(provider="mock", model=model, **kwargs)
        self.calls: list[dict[str, str]] = []

    def _ensure_client(self):  # never touches the network
        self._client = "mock"

    def complete(self, system: str, user: str) -> LLMResponse:
        self.calls.append({"system": system[:40], "user": user[:80]})
        sys_l = (system or "").lower()
        if "summar" in sys_l:
            return LLMResponse(text=self._summarize(user), raw={"mock": True})
        # default / research role: extract structured fields
        return LLMResponse(text=json.dumps(self._extract(user)), raw={"mock": True})

    # -- rule-based "research" extraction ---------------------------------
    def _extract(self, text: str) -> dict[str, Any]:
        t = (text or "").lower()
        out: dict[str, Any] = {
            "origin": None, "destination": None, "start_date": None,
            "end_date": None, "duration_days": None, "party_size": None,
            "budget_total": None, "currency": "USD", "interests": [],
            "pace": "moderate", "notes": None,
        }

        # origin: "from <city>"
        m = re.search(r"\bfrom\s+([a-z ]+?)(?:,|\.|$|\s+(?:to|for|with|late|early|under|around|next))", t)
        if m:
            out["origin"] = self._match_city(m.group(1)) or m.group(1).strip()

        # destination: "to <city>" / "in <city>" / first known city that is not the origin
        for c in sorted(_KNOWN_CITIES, key=len, reverse=True):
            if c in t and c != out["origin"]:
                out["destination"] = c
                break

        m = re.search(r"(\d+)\s*(?:day|days|d|nights?)\b", t)
        if m:
            out["duration_days"] = int(m.group(1))

        # resolve a month phrase like "late october 2025" to a concrete date,
        # the way a real model would, so the plan is fully reproducible.
        sd = self._resolve_start_date(t)
        if sd is not None:
            out["start_date"] = sd.isoformat()

        out["budget_total"] = self._extract_budget(t)
        if re.search(r"\beur|euros?\b", t):
            out["currency"] = "EUR"

        if "solo" in t or "1 person" in t:
            out["party_size"] = 1
        else:
            m = re.search(r"(\d+)\s*(?:people|persons?|travel+ers?|adults?|pax|guests?)", t)
            out["party_size"] = int(m.group(1)) if m else 1

        for kw in ("food", "museum", "art", "hike", "park", "beach", "shop", "anime",
                   "architecture", "history", "nightlife", "cafe", "nature"):
            if kw in t:
                out["interests"].append(kw)

        if "relaxed" in t or "slow" in t:
            out["pace"] = "relaxed"
        elif "packed" in t or "busy" in t:
            out["pace"] = "packed"

        return {k: v for k, v in out.items() if v not in (None, [], "")}

    _MONTHS = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
        "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
        "november": 11, "december": 12,
    }

    @classmethod
    def _resolve_start_date(cls, t: str) -> date | None:
        month = next((v for k, v in cls._MONTHS.items() if k in t), None)
        if month is None:
            return None
        ym = re.search(r"(20\d{2})", t)
        year = int(ym.group(1)) if ym else date.today().year
        if "late" in t:
            day = 22
        elif "early" in t:
            day = 5
        elif "mid" in t:
            day = 15
        else:
            day = 15
        try:
            return date(year, month, day)
        except ValueError:
            return None

    @staticmethod
    def _extract_budget(t: str) -> float | None:
        """Find a money amount, anchored to a currency/budget cue so a bare
        year like '2025' is never mistaken for a budget."""
        patterns = (
            r"\$\s*(\d{3,5})",
            r"(\d{3,5})\s*(?:usd|dollars|eur|euros)",
            r"(?:budget|under|around|about|below|~|max|upto|up to)\D{0,12}(\d{3,5})",
        )
        for pat in patterns:
            m = re.search(pat, t)
            if m:
                val = float(m.group(1))
                if 2000 <= val <= 2099 and not re.search(r"\$|usd|dollars|eur", t[max(0, m.start() - 3):m.end() + 6]):
                    continue  # looks like a year, skip
                return val
        return None

    @staticmethod
    def _match_city(fragment: str) -> str | None:
        frag = fragment.strip()
        if frag in _CITY_ALIASES:
            return _CITY_ALIASES[frag]
        for c in sorted(_KNOWN_CITIES, key=len, reverse=True):
            if c in frag:
                return c
        return None

    # -- rule-based "summary" ---------------------------------------------
    def _summarize(self, itinerary_json: str) -> str:
        try:
            it = json.loads(itinerary_json)
        except Exception:
            return "Trip plan ready."
        q = it.get("query", {})
        dest = q.get("destination", "your destination")
        nd = q.get("duration_days", len(it.get("days", [])))
        party = q.get("party_size", 1)
        total = (it.get("budget") or {}).get("total", 0)
        cur = (it.get("budget") or {}).get("currency", "USD")
        top = []
        for d in it.get("days", []):
            for slot in ("morning", "afternoon", "evening"):
                for a in d.get(slot, []):
                    top.append(a.get("name"))
        highlights = ", ".join([x for x in top[:3] if x]) or "a mix of local highlights"
        return (
            f"A {nd}-day trip to {str(dest).title()} for {party} traveler(s), built around "
            f"{highlights}. Estimated all-in cost is about {total:.0f} {cur}."
        )


def mock_llm(**kwargs: Any) -> MockLLM:
    """Convenience factory for the offline deterministic LLM."""
    return MockLLM(**kwargs)


def llm_from_env(cfg: dict | None = None) -> LLM:
    cfg = cfg or {}
    provider = (cfg.get("provider") or os.getenv("LLM_PROVIDER", "openai")).lower()
    model = cfg.get("model") or os.getenv("LLM_MODEL", "gpt-4o-mini")
    temperature = float(cfg.get("temperature", 0.3))
    max_tokens = int(cfg.get("max_tokens", 1500))
    if provider in ("mock", "offline", "fake", "deterministic"):
        return MockLLM(model=model if model.startswith("mock") else "mock-deterministic-v1",
                       temperature=temperature, max_tokens=max_tokens)
    return LLM(provider=provider, model=model, temperature=temperature, max_tokens=max_tokens)
