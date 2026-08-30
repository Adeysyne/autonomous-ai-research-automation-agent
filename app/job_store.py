from datetime import datetime, timezone
from uuid import uuid4

from app.models import (
    ResearchFindings,
    ResearchJob,
    ResearchJobEvent,
    ResearchPlan,
    ResearchRequest,
    ResearchResult,
)


TRANSITIONS = {
    ("accepted", "planner"): (
        "planning",
        "planner",
    ),
    ("planning", "planner"): (
        "researching",
        "researcher",
    ),
    ("researching", "researcher"): (
        "synthesizing",
        "synthesizer",
    ),
    ("synthesizing", "synthesizer"): (
        "completed",
        "complete",
    ),
}


class InMemoryResearchJobStore:
    def __init__(self):
        self._jobs: dict[str, ResearchJob] = {}

    def create(
        self,
        request: ResearchRequest,
    ) -> ResearchJob:
        now = datetime.now(
            timezone.utc
        ).isoformat()

        job = ResearchJob(
            request_id=str(uuid4()),
            status="accepted",
            current_stage="planner",
            created_at=now,
            updated_at=now,
            research_request=request,
            plan=None,
            research_findings=None,
            result=None,
            history=[
                ResearchJobEvent(
                    status="accepted",
                    current_stage="planner",
                    timestamp=now,
                )
            ],
        )

        self._jobs[job.request_id] = job

        return job

    def get(
        self,
        request_id: str,
    ) -> ResearchJob | None:
        return self._jobs.get(request_id)

    def save_plan(
        self,
        request_id: str,
        plan: ResearchPlan,
    ) -> ResearchJob | None:
        job = self.get(request_id)

        if job is None:
            return None

        job.plan = plan
        job.updated_at = datetime.now(
            timezone.utc
        ).isoformat()

        return job

    def save_findings(
        self,
        request_id: str,
        findings: ResearchFindings,
    ) -> ResearchJob | None:
        job = self.get(request_id)

        if job is None:
            return None

        job.research_findings = findings
        job.updated_at = datetime.now(
            timezone.utc
        ).isoformat()

        return job

    def save_result(
        self,
        request_id: str,
        result: ResearchResult,
    ) -> ResearchJob | None:
        job = self.get(request_id)

        if job is None:
            return None

        job.result = result
        job.updated_at = datetime.now(
            timezone.utc
        ).isoformat()

        return job

    def advance(
        self,
        request_id: str,
    ) -> ResearchJob | None:
        job = self.get(request_id)

        if job is None:
            return None

        transition = TRANSITIONS.get(
            (
                job.status,
                job.current_stage,
            )
        )

        if transition is None:
            return job

        next_status, next_stage = transition

        now = datetime.now(
            timezone.utc
        ).isoformat()

        job.status = next_status
        job.current_stage = next_stage
        job.updated_at = now

        job.history.append(
            ResearchJobEvent(
                status=next_status,
                current_stage=next_stage,
                timestamp=now,
            )
        )

        return job

    def clear(self) -> None:
        self._jobs.clear()


research_job_store = InMemoryResearchJobStore()