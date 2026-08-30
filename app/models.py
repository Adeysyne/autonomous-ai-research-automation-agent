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


class ResearchPlan(BaseModel):
    research_objective: str
    sub_questions: list[str]
    search_strategy: list[str]
    completion_criteria: list[str]


class ResearchFinding(BaseModel):
    sub_question: str
    finding: str
    evidence: list[str]
    source_urls: list[str]


class ResearchFindings(BaseModel):
    findings: list[ResearchFinding]

    unresolved_gaps: list[str] = Field(
        default_factory=list
    )


class ResearchResult(BaseModel):
    executive_summary: str
    key_findings: list[str]
    recommendations: list[str]
    limitations: list[str]
    source_urls: list[str]


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

    plan: ResearchPlan | None = None

    research_findings: ResearchFindings | None = None

    result: ResearchResult | None = None