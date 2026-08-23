from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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
        json={
            "question": (
                "What are the major approaches "
                "to evaluating agentic AI systems?"
            ),
            "depth": "standard",
            "delivery": "api",
        },
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