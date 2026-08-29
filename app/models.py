from typing import Literal

from pydantic import BaseModel, Field


ResearchStatus = Literal[
    "accepted",
    "planning",
    "researching",
    "synthesizing",
    "completed",
    "failed",
]

ResearchStage = Literal[
    "planner",
    "researcher",
    "synthesizer",
    "complete",
    "failed",
]


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


class ResearchJobEvent(BaseModel):
    status: ResearchStatus
    current_stage: ResearchStage
    timestamp: str


class ResearchJob(BaseModel):
    request_id: str

    status: ResearchStatus = "accepted"
    current_stage: ResearchStage = "planner"

    created_at: str
    updated_at: str

    research_request: ResearchRequest

    history: list[ResearchJobEvent] = Field(
        default_factory=list
    )

    result: str | None = None