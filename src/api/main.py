"""FastAPI entrypoint."""
from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..graph import run as run_graph
from ..llm import llm_from_env
from ..state import Itinerary

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("travel.api")

app = FastAPI(title="multiagent-travel-planner", version="0.1.0")


class PlanRequest(BaseModel):
    query: str = Field(..., min_length=4)
    profile: str = "default"


class PlanResponse(BaseModel):
    summary: str
    itinerary: dict[str, Any]


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/plan", response_model=PlanResponse)
def plan(req: PlanRequest) -> PlanResponse:
    logger.info("plan request: %s", req.query[:80])
    try:
        llm = llm_from_env()
        it: Itinerary = run_graph(req.query, llm=llm)
    except Exception as e:
        logger.exception("planning failed")
        raise HTTPException(status_code=500, detail=str(e))
    return PlanResponse(summary=it.summary or "", itinerary=it.model_dump(mode="json"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
