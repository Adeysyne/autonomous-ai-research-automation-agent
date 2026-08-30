from fastapi import FastAPI, HTTPException

from app.job_store import research_job_store
from app.models import (
    ResearchFindings,
    ResearchPlan,
    ResearchRequest,
    ResearchResult,
)


app = FastAPI(
    title="Autonomous AI Research & Automation Agent",
    description=(
        "API foundation for receiving, validating, "
        "tracking, and orchestrating autonomous "
        "research tasks."
    ),
    version="0.6.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": (
            "Autonomous AI Research & Automation Agent"
        ),
    }


@app.post("/research/intake")
def research_intake(
    request: ResearchRequest,
):
    job = research_job_store.create(request)

    return {
        "request_id": job.request_id,
        "status": job.status,
        "created_at": job.created_at,
        "research_request": (
            job.research_request.model_dump()
        ),
        "next_stage": job.current_stage,
    }


@app.get("/research/{request_id}")
def get_research_job(
    request_id: str,
):
    job = research_job_store.get(request_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Research job not found.",
        )

    return job.model_dump()


@app.post("/research/{request_id}/plan")
def save_research_plan(
    request_id: str,
    plan: ResearchPlan,
):
    job = research_job_store.save_plan(
        request_id,
        plan,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Research job not found.",
        )

    return job.model_dump()


@app.post("/research/{request_id}/findings")
def save_research_findings(
    request_id: str,
    findings: ResearchFindings,
):
    job = research_job_store.save_findings(
        request_id,
        findings,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Research job not found.",
        )

    return job.model_dump()


@app.post("/research/{request_id}/result")
def save_research_result(
    request_id: str,
    result: ResearchResult,
):
    job = research_job_store.save_result(
        request_id,
        result,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Research job not found.",
        )

    return job.model_dump()


@app.post("/research/{request_id}/advance")
def advance_research_job(
    request_id: str,
):
    job = research_job_store.get(request_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Research job not found.",
        )

    if job.status == "completed":
        raise HTTPException(
            status_code=409,
            detail="Research job is already completed.",
        )

    updated_job = research_job_store.advance(
        request_id
    )

    return updated_job.model_dump()