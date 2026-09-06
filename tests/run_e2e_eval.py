import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request


API_BASE_URL = "http://127.0.0.1:8000"

N8N_PRODUCTION_WEBHOOK = (
    "http://localhost:5678/"
    "webhook/p2-research-orchestrator"
)

TEST_DIR = Path(__file__).resolve().parent

CASES_PATH = TEST_DIR / "e2e_eval_cases.json"

RESULTS_PATH = TEST_DIR / "e2e_eval_results.json"


def http_json(
    method: str,
    url: str,
    payload: dict | None = None,
    timeout: int = 600,
):
    body = None

    headers = {
        "Content-Type": "application/json"
    }

    if payload is not None:
        body = json.dumps(payload).encode(
            "utf-8"
        )

    req = request.Request(
        url=url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with request.urlopen(
            req,
            timeout=timeout,
        ) as response:
            raw = response.read().decode(
                "utf-8"
            )

            if not raw.strip():
                return None

            return json.loads(raw)

    except error.HTTPError as exc:
        raw = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"HTTP {exc.code} from {url}: {raw}"
        ) from exc

    except error.URLError as exc:
        raise RuntimeError(
            f"Could not connect to {url}: "
            f"{exc.reason}"
        ) from exc


def collect_source_urls(job: dict) -> set[str]:
    urls: set[str] = set()

    research_findings = (
        job.get("research_findings") or {}
    )

    for finding in research_findings.get(
        "findings",
        [],
    ):
        for url in finding.get(
            "source_urls",
            [],
        ):
            if url:
                urls.add(url)

    result = job.get("result") or {}

    for url in result.get(
        "source_urls",
        [],
    ):
        if url:
            urls.add(url)

    return urls


def evaluate_case(case: dict) -> dict:
    started = time.perf_counter()

    intake_payload = {
        "question": case["question"],
        "depth": case["depth"],
        "delivery": "api",
    }

    created = http_json(
        "POST",
        f"{API_BASE_URL}/research/intake",
        intake_payload,
    )

    request_id = created["request_id"]

    http_json(
        "POST",
        N8N_PRODUCTION_WEBHOOK,
        {
            "request_id": request_id,
        },
    )

    job = http_json(
        "GET",
        f"{API_BASE_URL}/research/{request_id}",
    )

    elapsed = round(
        time.perf_counter() - started,
        2,
    )

    plan_saved = job.get("plan") is not None

    findings = (
        job.get("research_findings") or {}
    )

    findings_saved = bool(findings)

    finding_count = len(
        findings.get("findings", [])
    )

    unresolved_gap_count = len(
        findings.get(
            "unresolved_gaps",
            [],
        )
    )

    result_saved = job.get("result") is not None

    sources = collect_source_urls(job)

    source_count = len(sources)

    completed = (
        job.get("status") == "completed"
        and job.get("current_stage") == "complete"
    )

    passed = all(
        [
            completed,
            plan_saved,
            findings_saved,
            result_saved,
            finding_count
            >= case["min_findings"],
            source_count
            >= case["min_sources"],
        ]
    )

    return {
        "id": case["id"],
        "request_id": request_id,
        "passed": passed,
        "status": job.get("status"),
        "current_stage": job.get(
            "current_stage"
        ),
        "plan_saved": plan_saved,
        "findings_saved": findings_saved,
        "final_result_saved": result_saved,
        "finding_count": finding_count,
        "unique_source_count": source_count,
        "unresolved_gap_count": (
            unresolved_gap_count
        ),
        "elapsed_seconds": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run production E2E evaluation "
            "for P2 research orchestration."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Run only the first N evaluation "
            "cases."
        ),
    )

    args = parser.parse_args()

    cases = json.loads(
        CASES_PATH.read_text(
            encoding="utf-8"
        )
    )

    if args.limit is not None:
        cases = cases[: args.limit]

    # Fail early if the backend is unavailable.
    health = http_json(
        "GET",
        f"{API_BASE_URL}/health",
    )

    print(
        "Backend:",
        health["status"],
    )

    print(
        f"Running {len(cases)} E2E case(s)..."
    )

    results = []

    for index, case in enumerate(
        cases,
        start=1,
    ):
        print(
            f"\n[{index}/{len(cases)}] "
            f"{case['id']}"
        )

        try:
            result = evaluate_case(case)

        except Exception as exc:
            result = {
                "id": case["id"],
                "passed": False,
                "error": str(exc),
            }

        results.append(result)

        if result["passed"]:
            print(
                "PASS",
                "| findings:",
                result["finding_count"],
                "| sources:",
                result["unique_source_count"],
                "| seconds:",
                result["elapsed_seconds"],
            )
        else:
            print(
                "FAIL",
                "|",
                result.get(
                    "error",
                    "quality threshold failed",
                ),
            )

    total = len(results)

    passed = sum(
        1
        for item in results
        if item["passed"]
    )

    failed = total - passed

    successful_timings = [
        item["elapsed_seconds"]
        for item in results
        if "elapsed_seconds" in item
    ]

    average_latency = (
        round(
            sum(successful_timings)
            / len(successful_timings),
            2,
        )
        if successful_timings
        else None
    )

    source_counts = [
        item["unique_source_count"]
        for item in results
        if "unique_source_count" in item
    ]

    average_sources = (
        round(
            sum(source_counts)
            / len(source_counts),
            2,
        )
        if source_counts
        else None
    )

    completion_rate = (
        round(
            (passed / total) * 100,
            1,
        )
        if total
        else 0.0
    )

    summary = {
        "evaluation_name": (
            "P2 Production E2E Evaluation"
        ),
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "total_cases": total,
        "passed_cases": passed,
        "failed_cases": failed,
        "completion_rate_percent": (
            completion_rate
        ),
        "average_latency_seconds": (
            average_latency
        ),
        "average_unique_sources": (
            average_sources
        ),
        "results": results,
    }

    RESULTS_PATH.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 60)

    print(
        f"Passed: {passed} / {total}"
    )

    print(
        "Completion rate:",
        f"{completion_rate}%",
    )

    print(
        "Average latency:",
        average_latency,
        "seconds",
    )

    print(
        "Average unique sources:",
        average_sources,
    )

    print(
        "Results saved to:",
        RESULTS_PATH,
    )

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()