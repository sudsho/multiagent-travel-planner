"""FastAPI entrypoint."""
from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..graph import run as run_graph
from ..llm import llm_from_env
from ..state import Itinerary

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("travel.api")

app = FastAPI(title="multiagent-travel-planner", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    query: str = Field(..., min_length=4)
    profile: str = "default"


class PlanResponse(BaseModel):
    summary: str
    itinerary: dict[str, Any]
    markdown: str | None = None


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
    from ..render import render_markdown
    return PlanResponse(
        summary=it.summary or "",
        itinerary=it.model_dump(mode="json"),
        markdown=render_markdown(it),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
