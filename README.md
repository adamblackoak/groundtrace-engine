# GroundTrace Memory

**Warranted incident memory for agents.**

GroundTrace Memory is an incident-response agent that stores prior incidents, actions, outcomes, provenance, and decision traces in CockroachDB. When a new incident arrives, it retrieves semantically similar memories, applies a deterministic `RELY / HOLD / REJECT` admission gate, and returns an action only when the supporting memory is verified, successful, and current.

This repository is the submission build for the CockroachDB × AWS **Build with Agentic Memory** hackathon.

## Frozen submission scope

One narrow vertical slice:

1. AWS Lambda receives an incident or a resolved-incident memory.
2. Amazon Bedrock Titan Text Embeddings V2 creates a 1024-dimensional embedding.
3. CockroachDB stores structured memory and embeddings transactionally.
4. CockroachDB Distributed Vector Indexing retrieves similar memories within a tenant.
5. The reused GroundTrace admission primitive classifies each candidate as `RELY`, `HOLD`, or `REJECT`.
6. The agent emits a bounded recommended action only from `RELY` memories and persists its decision trace.
7. CockroachDB Cloud Managed MCP Server provides read-only inspection of memories and traces for operators and judges.

## Why memory is the product

A conventional RAG demo retrieves text and hopes it is useful. GroundTrace Memory treats retrieved material as a candidate, not authority. The stored outcome, verification state, freshness, provenance, and trace determine whether the agent may rely on it. CockroachDB is therefore both semantic memory and the transactional system of record for memory admissibility.

## Architecture

```text
resolved incident ─┐
                   ├─> AWS Lambda ─> Bedrock embedding ─> CockroachDB memory
new incident ──────┘                                      │
                                                         ▼
                                             tenant-scoped vector recall
                                                         │
                                                         ▼
                                               RELY / HOLD / REJECT
                                                         │
                                      ┌──────────────────┴──────────────────┐
                                      ▼                                     ▼
                              bounded recommendation                 decision trace
                                      └──────────────────┬──────────────────┘
                                                         ▼
                                                    CockroachDB
```

## Admission gate

A retrieved memory is not automatically trusted. The deterministic gate evaluates each candidate using the stored evidence:

- unverified memory -> `HOLD`
- unsuccessful prior outcome -> `REJECT`
- memory older than 180 days -> `HOLD`
- cosine similarity below `0.70` -> `HOLD`
- missing provenance -> `REJECT`
- otherwise -> `RELY`

Only a `RELY` memory can supply the returned recommendation. Every recall persists a decision trace containing the candidate IDs, similarity scores, admissions, reasons, recommendation and overall status.

## Judge demo path

The shortest end-to-end proof is deliberately small:

1. Store a verified, successful resolved incident with provenance using `operation: "remember"`.
2. Submit a semantically similar new incident using `operation: "recall"`.
3. Observe the returned recommendation, `RELY` admission and persisted `trace_id`.
4. Inspect the stored memory and decision trace in CockroachDB.

Example resolved memory payload:

```json
{
  "operation": "remember",
  "tenant_id": "groundtrace-demo",
  "incident_text": "Database connection pool saturation caused elevated API latency",
  "action_text": "Inspect connection pool saturation and reduce burst concurrency",
  "outcome_success": true,
  "verified": true,
  "occurred_at": "2026-08-01T12:00:00+00:00",
  "provenance": {
    "source": "controlled-demo-incident"
  }
}
```

Example recall payload:

```json
{
  "operation": "recall",
  "tenant_id": "groundtrace-demo",
  "incident_text": "API latency increased while database connections were saturated"
}
```

The key output is not merely a similar document: it is a bounded recommendation plus a persisted, inspectable warrant showing why the retrieved memory was or was not admissible.

## Technology

- CockroachDB Cloud
- CockroachDB Distributed Vector Indexing
- CockroachDB Cloud Managed MCP Server
- AWS Lambda
- Amazon Bedrock Titan Text Embeddings V2
- Python 3.12 and `psycopg`

## Repository status

The concept and architecture are frozen. The end-to-end CockroachDB/AWS vertical path is implemented on `main`; remaining work is deployment verification, demo capture, and publication.

## Local quick start

Create a Python 3.12 virtual environment, install the project and run the unit tests:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

The variables listed in `.env.example` are examples only; the application does not automatically load a `.env` file.

Apply the database migrations in order:

```text
db/001_init.sql
db/002_allow_rejected_status.sql
```

Set `DATABASE_URL` in the current shell. For example:

```bash
export DATABASE_URL='postgresql://username:password@host:26257/defaultdb?sslmode=verify-full'
```

```powershell
$env:DATABASE_URL='postgresql://username:password@host:26257/defaultdb?sslmode=verify-full'
```

Then run the reversible database/vector smoke test:

```bash
python scripts/smoke_db.py
```

With AWS credentials configured and Bedrock access available, run the full Bedrock-to-CockroachDB smoke test:

```bash
python scripts/smoke_e2e.py
```

## AWS deployment and demo access

AWS deployment uses the SAM template in `template.yaml`. The template requires a `DemoApiToken` parameter of at least 32 characters. Do not commit the real token to the repository.

The deployed `/memory` endpoint requires the token as an HTTP Bearer credential. For example:

```bash
curl -X POST "$GROUNDTRACE_API_URL" \
  -H "Authorization: Bearer $GROUNDTRACE_DEMO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"operation":"health"}'
```

The HTTP API is also configured with modest route throttling to limit accidental or abusive invocation volume. Judge access credentials should be supplied privately with the submission rather than committed here.

## Licence

MIT
