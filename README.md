# Autonomous AI Research & Automation Agent

A production-oriented multi-agent research orchestration system built with FastAPI, n8n, OpenAI, and Web Search.

The system accepts a research question, creates a persistent research job, plans the investigation, performs web-grounded research, synthesizes the evidence, and tracks the job through a resumable lifecycle.

---

## Project Status

**Production E2E Passed**

- Backend regression tests: **14/14 passed**
- Production E2E scenarios: **3/3 passed**
- Production completion rate: **100%**
- Average end-to-end latency: **164.79 seconds**
- Average unique sources per research job: **24.67**

---

## Architecture

The system uses three specialized agents.

```text
Research Request
      |
      v
FastAPI Research Intake
      |
      v
Persistent Research Job State
      |
      v
n8n Research Job Orchestrator
      |
      v
Route Job Status
      |
      v
Planner Agent
      |
      v
Structured Research Plan
      |
      v
Persist Plan
      |
      v
Researcher Agent
      |
      +----> OpenAI Web Search
      |
      v
Evidence-Based Findings
      |
      v
Persist Findings
      |
      v
Synthesizer Agent
      |
      v
Final Structured Result
      |
      v
Persist Result
      |
      v
completed / complete
```

---

## Agent Roles

### Planner Agent

Transforms the research question into a structured plan containing:

- research objective
- sub-questions
- search strategy
- completion criteria

The plan is validated, parsed, and persisted before research begins.

### Researcher Agent

Executes the Planner's research plan using OpenAI Web Search.

Produces structured:

- findings
- supporting evidence
- source URLs
- unresolved gaps

The Researcher is instructed not to fabricate evidence or URLs.

### Synthesizer Agent

Consumes the persisted research plan and research findings.

Produces:

- executive summary
- key findings
- recommendations
- limitations
- consolidated source URLs

The Synthesizer performs no new web research and must remain grounded in the Researcher's evidence.

---

## Research Job Lifecycle

```text
accepted / planner
        |
        v
planning / planner
        |
        v
researching / researcher
        |
        v
synthesizing / synthesizer
        |
        v
completed / complete
```

Lifecycle transitions are idempotent.

Calling `/advance` on an already completed job returns the completed job without adding duplicate lifecycle events.

---

## Resume and Recovery

The n8n orchestrator routes jobs according to their persisted state:

```text
accepted
    -> Start Planning

planning
    -> Prepare Planner Input

researching
    -> Prepare Researcher Input

synthesizing
    -> Prepare Synthesizer Input

completed
    -> Prepare Completed Job Response
```

This enables interrupted workflows to resume from the appropriate stage instead of restarting the full research process.

---

## API

### Health Check

```http
GET /health
```

### Create Research Job

```http
POST /research/intake
```

Example:

```json
{
  "question": "How should autonomous AI agents be evaluated?",
  "depth": "standard",
  "delivery": "api"
}
```

### Retrieve Research Job

```http
GET /research/{request_id}
```

### Save Planner Output

```http
POST /research/{request_id}/plan
```

### Save Research Findings

```http
POST /research/{request_id}/findings
```

### Save Final Result

```http
POST /research/{request_id}/result
```

### Advance Job Lifecycle

```http
POST /research/{request_id}/advance
```

---

## n8n Production Webhook

Published workflow:

```text
P2-04 Research Job Orchestrator
```

Production webhook:

```text
http://localhost:5678/webhook/p2-research-orchestrator
```

The workflow orchestrates:

```text
Planner
→ Researcher
→ Synthesizer
→ Completed Research Job
```

---

## Reliability Features

The current implementation includes:

- explicit research-job lifecycle
- resumable stage routing
- persisted Planner output
- persisted Researcher findings
- persisted Synthesizer result
- idempotent lifecycle advancement
- schema validation with Pydantic
- JSON-output validation
- HTTP retry handling
- explicit success/error branches
- automated backend regression testing
- automated production E2E evaluation
- findings-count quality thresholds
- source-count quality thresholds
- latency measurement

---

## Evaluation

### Backend Regression Suite

Run:

```powershell
python -m pytest -q
```

Current baseline:

```text
14 passed
```

### Production E2E Evaluation

Run a single case:

```powershell
python .\tests\run_e2e_eval.py --limit 1
```

Run the full baseline:

```powershell
python .\tests\run_e2e_eval.py
```

Current measured results:

| Metric | Result |
|---|---:|
| Evaluation cases | 3 |
| Passed | 3 |
| Failed | 0 |
| Completion rate | 100% |
| Average E2E latency | 164.79 s |
| Average unique sources | 24.67 |

Evaluation scenarios cover:

1. autonomous-agent reliability and safety
2. RAG-system evaluation
3. tool-using agent security and reliability

Machine-readable evaluation output:

```text
tests/e2e_eval_results.json
```

Evaluation configuration:

```text
tests/e2e_eval_cases.json
```

Evaluation runner:

```text
tests/run_e2e_eval.py
```

---

## Technology Stack

- Python 3.12
- FastAPI
- Pydantic
- pytest
- n8n
- OpenAI API
- OpenAI Web Search
- Docker
- Git / GitHub
- PowerShell

---

## Local Development

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start the FastAPI service:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check the API:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health"
```

Run tests:

```powershell
python -m pytest -q
```

n8n runs separately in Docker on:

```text
http://localhost:5678
```

---

## Repository Structure

```text
autonomous-ai-research-automation-agent/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── job_store.py
│
├── tests/
│   ├── test_main.py
│   ├── e2e_eval_cases.json
│   ├── e2e_eval_results.json
│   └── run_e2e_eval.py
│
├── ARCHITECTURE.md
├── EVALUATION.md
├── README.md
└── requirements.txt
```

---

## Current Limitations

The current research-job store is in memory.

This is sufficient for the current orchestration and evaluation implementation, but restarting the FastAPI service clears active jobs.

A production deployment should replace the in-memory store with durable persistence such as PostgreSQL, Redis, DynamoDB, or another appropriate datastore.

Additional production-hardening opportunities include:

- authentication and authorization
- persistent distributed job state
- structured observability and tracing
- rate limiting
- cost/token monitoring
- dead-letter handling
- deployment automation

---

## What This Project Demonstrates

This project demonstrates practical implementation of:

- multi-agent AI orchestration
- planner/researcher/synthesizer architectures
- autonomous tool use
- web-grounded research
- structured LLM outputs
- state-machine workflow design
- resumable agent execution
- API-based agent state persistence
- reliability engineering
- automated AI-system evaluation
- production workflow testing

---

## Evaluation Result

The production baseline successfully completed all evaluation scenarios:

```text
3 / 3 production E2E cases passed
100% completion rate
14 / 14 backend tests passed
24.67 average unique sources
164.79 second average E2E latency
```

This establishes a reproducible baseline for future orchestration and research-quality improvements.