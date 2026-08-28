import argparse
import json
import time
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "qa_routing_eval.json"
RESULTS_PATH = BASE_DIR / "qa_routing_results.json"

WEBHOOK_URL = "http://localhost:5678/webhook/p2-agentic-qa"


def call_workflow(question: str):
    payload = json.dumps({
        "question": question
    }).encode("utf-8")

    request = urllib.request.Request(
        WEBHOOK_URL,
        data=payload,
        headers={
            "Content-Type": "application/json"
        },
        method="POST",
    )

    start = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
            result = json.loads(body)

    except Exception as exc:
        result = {
            "status": "error",
            "decision_reason": "evaluation_request_failed",
            "message": str(exc),
        }

    elapsed = time.perf_counter() - start

    return result, elapsed


parser = argparse.ArgumentParser()

parser.add_argument(
    "--category",
    choices=[
        "invalid",
        "grounded",
        "out_of_scope",
    ],
    help="Run only one evaluation category",
)

args = parser.parse_args()


with DATASET_PATH.open("r", encoding="utf-8") as file:
    cases = json.load(file)


if args.category:
    cases = [
        case
        for case in cases
        if case["category"] == args.category
    ]


results = []


for case in cases:
    response, elapsed = call_workflow(
        case["question"]
    )

    actual_status = response.get(
        "status",
        "unknown"
    )

    expected_status = case[
        "expected_status"
    ]

    passed = (
        actual_status
        == expected_status
    )

    result = {
        "id": case["id"],
        "category": case["category"],
        "question": case["question"],
        "expected_status": expected_status,
        "actual_status": actual_status,
        "passed": passed,

        "decision_reason":
            response.get(
                "decision_reason"
            ),

        "citation_count":
            response.get(
                "citation_count"
            ),

        "max_similarity_score":
            response.get(
                "max_similarity_score"
            ),

        "average_similarity_score":
            response.get(
                "average_similarity_score"
            ),

        "research_job_id":
            response.get(
                "research_job_id"
            ),

        "service":
            response.get(
                "service"
            ),

        "elapsed_seconds":
            round(elapsed, 3),
    }

    results.append(result)

    marker = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"{marker:4} | "
        f"{case['id']:12} | "
        f"expected={expected_status:9} | "
        f"actual={actual_status:9} | "
        f"{elapsed:.2f}s"
    )


total = len(results)

passed_count = sum(
    item["passed"]
    for item in results
)

accuracy = (
    passed_count / total
    if total
    else 0
)


summary = {
    "category_filter":
        args.category,

    "total_cases":
        total,

    "passed_cases":
        passed_count,

    "failed_cases":
        total - passed_count,

    "routing_accuracy":
        round(accuracy, 4),

    "results":
        results,
}


with RESULTS_PATH.open(
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        summary,
        file,
        indent=2,
    )


print()
print("=" * 65)

print(
    f"Routing accuracy: "
    f"{passed_count}/{total} "
    f"= {accuracy * 100:.1f}%"
)

print(
    f"Results saved to: "
    f"{RESULTS_PATH}"
)

print("=" * 65)