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

## Technology

- CockroachDB Cloud
- CockroachDB Distributed Vector Indexing
- CockroachDB Cloud Managed MCP Server
- AWS Lambda
- Amazon Bedrock Titan Text Embeddings V2
- Python 3.12 and `psycopg`

## Repository status

The concept and architecture are frozen. The end-to-end CockroachDB/AWS vertical path is implemented on `main`; remaining work is submission hardening, documentation, demo capture, and publication.

## Local quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
pytest
```

Apply `db/001_init.sql` to a CockroachDB cluster, set `DATABASE_URL`, and run the local smoke script:

```bash
python scripts/smoke_local.py
```

AWS deployment uses the SAM template in `template.yaml`.

## Licence

MIT
