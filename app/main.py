from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(
    title="Autonomous AI Research & Automation Agent",
    description=(
        "API foundation for receiving, validating, "
        "and orchestrating autonomous research tasks."
    ),
    version="0.1.0",
)


class ResearchRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=10,
        description="Research question to investigate.",
    )

    depth: Literal[
        "quick",
        "standard",
        "deep",
    ] = "standard"

    delivery: Literal[
        "api",
        "email",
        "slack",
    ] = "api"


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Autonomous AI Research & Automation Agent",
    }


@app.post("/research/intake")
def research_intake(request: ResearchRequest):
    request_id = str(uuid4())

    return {
        "request_id": request_id,
        "status": "accepted",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "research_request": request.model_dump(),
        "next_stage": "planner",
    }