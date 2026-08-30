import pytest
from fastapi.testclient import TestClient

from app.job_store import research_job_store
from app.main import app


client = TestClient(app)


VALID_REQUEST = {
    "question": (
        "What are the major approaches "
        "to evaluating agentic AI systems?"
    ),
    "depth": "standard",
    "delivery": "api",
}


@pytest.fixture(autouse=True)
def clear_research_jobs():
    research_job_store.clear()

    yield

    research_job_store.clear()


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"

    assert (
        data["service"]
        == "Autonomous AI Research & Automation Agent"
    )


def test_research_intake_success():
    response = client.post(
        "/research/intake",
        json=VALID_REQUEST,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "accepted"
    assert data["next_stage"] == "planner"

    assert "request_id" in data
    assert "created_at" in data

    assert (
        data["research_request"]["depth"]
        == "standard"
    )

    assert (
        data["research_request"]["delivery"]
        == "api"
    )


def test_research_job_can_be_retrieved():
    create_response = client.post(
        "/research/intake",
        json=VALID_REQUEST,
    )

    request_id = (
        create_response.json()["request_id"]
    )

    response = client.get(
        f"/research/{request_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["request_id"] == request_id
    assert data["status"] == "accepted"
    assert data["current_stage"] == "planner"
    assert data["result"] is None

    assert len(data["history"]) == 1

    assert (
        data["history"][0]["status"]
        == "accepted"
    )


def test_research_job_lifecycle():
    create_response = client.post(
        "/research/intake",
        json=VALID_REQUEST,
    )

    request_id = (
        create_response.json()["request_id"]
    )

    expected_transitions = [
        ("planning", "planner"),
        ("researching", "researcher"),
        ("synthesizing", "synthesizer"),
        ("completed", "complete"),
    ]

    for expected_status, expected_stage in expected_transitions:
        response = client.post(
            f"/research/{request_id}/advance"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == expected_status
        assert data["current_stage"] == expected_stage

    final_response = client.get(
        f"/research/{request_id}"
    )

    final_data = final_response.json()

    assert final_data["status"] == "completed"
    assert final_data["current_stage"] == "complete"

    assert len(final_data["history"]) == 5


def test_completed_job_cannot_advance():
    create_response = client.post(
        "/research/intake",
        json=VALID_REQUEST,
    )

    request_id = (
        create_response.json()["request_id"]
    )

    for _ in range(4):
        response = client.post(
            f"/research/{request_id}/advance"
        )

        assert response.status_code == 200

    response = client.post(
        f"/research/{request_id}/advance"
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Research job is already completed."
    )


def test_unknown_research_job_returns_404():
    response = client.get(
        "/research/does-not-exist"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Research job not found."
    )


def test_unknown_research_job_cannot_advance():
    response = client.post(
        "/research/does-not-exist/advance"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Research job not found."
    )


def test_research_intake_rejects_short_question():
    response = client.post(
        "/research/intake",
        json={
            "question": "Too short",
            "depth": "standard",
            "delivery": "api",
        },
    )

    assert response.status_code == 422


def test_research_intake_rejects_invalid_depth():
    response = client.post(
        "/research/intake",
        json={
            "question": (
                "What are the major approaches "
                "to evaluating agentic AI systems?"
            ),
            "depth": "extreme",
            "delivery": "api",
        },
    )

    assert response.status_code == 422


def test_research_plan_can_be_saved():
    create_response = client.post(
        "/research/intake",
        json=VALID_REQUEST,
    )

    request_id = (
        create_response.json()["request_id"]
    )

    plan = {
        "research_objective": (
            "Evaluate major approaches for "
            "agentic AI system assessment."
        ),
        "sub_questions": [
            "How should reliability be measured?",
            "How should safety be measured?",
            "How should tool-use failures be evaluated?",
        ],
        "search_strategy": [
            "Review peer-reviewed literature.",
            "Compare evaluation frameworks.",
        ],
        "completion_criteria": [
            "Identify major evaluation dimensions.",
            "Provide evidence-backed recommendations.",
        ],
    }

    response = client.post(
        f"/research/{request_id}/plan",
        json=plan,
    )

    assert response.status_code == 200

    assert response.json()["plan"] == plan


def test_saved_plan_is_available_when_job_is_retrieved():
    create_response = client.post(
        "/research/intake",
        json=VALID_REQUEST,
    )

    request_id = (
        create_response.json()["request_id"]
    )

    plan = {
        "research_objective": "Evaluate agentic AI.",
        "sub_questions": [
            "What should be measured?"
        ],
        "search_strategy": [
            "Review relevant literature."
        ],
        "completion_criteria": [
            "Produce evidence-backed findings."
        ],
    }

    client.post(
        f"/research/{request_id}/plan",
        json=plan,
    )

    response = client.get(
        f"/research/{request_id}"
    )

    assert response.status_code == 200

    assert response.json()["plan"] == plan


def test_research_findings_can_be_saved():
    create_response = client.post(
        "/research/intake",
        json=VALID_REQUEST,
    )

    request_id = (
        create_response.json()["request_id"]
    )

    findings = {
        "findings": [
            {
                "sub_question": (
                    "How should reliability be measured?"
                ),
                "finding": (
                    "Reliability should be evaluated "
                    "across repeated task executions."
                ),
                "evidence": [
                    (
                        "Repeated trials expose variance "
                        "and execution instability."
                    )
                ],
                "source_urls": [
                    "https://example.com/source"
                ],
            }
        ],
        "unresolved_gaps": [],
    }

    response = client.post(
        f"/research/{request_id}/findings",
        json=findings,
    )

    assert response.status_code == 200

    assert (
        response.json()["research_findings"]
        == findings
    )


def test_research_result_can_be_saved():
    create_response = client.post(
        "/research/intake",
        json=VALID_REQUEST,
    )

    request_id = (
        create_response.json()["request_id"]
    )

    result = {
        "executive_summary": (
            "Agentic AI evaluation requires "
            "multi-dimensional testing."
        ),
        "key_findings": [
            "Reliability requires repeated trials.",
            "Safety requires explicit failure testing.",
        ],
        "recommendations": [
            "Use reproducible evaluation protocols.",
            "Track recovery and tool-use failures.",
        ],
        "limitations": [
            "Benchmarks vary across application domains."
        ],
        "source_urls": [
            "https://www.nist.gov/"
        ],
    }

    response = client.post(
        f"/research/{request_id}/result",
        json=result,
    )

    assert response.status_code == 200

    assert (
        response.json()["result"]
        == result
    )