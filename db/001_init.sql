CREATE TABLE IF NOT EXISTS incident_memories (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id STRING NOT NULL,
    incident_text STRING NOT NULL,
    action_text STRING NOT NULL,
    outcome_success BOOL NOT NULL,
    verified BOOL NOT NULL DEFAULT false,
    occurred_at TIMESTAMPTZ NOT NULL,
    provenance JSONB NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS incident_memories_tenant_idx
    ON incident_memories (tenant_id, occurred_at DESC);

CREATE VECTOR INDEX IF NOT EXISTS incident_memories_embedding_idx
    ON incident_memories (embedding vector_cosine_ops)
    WITH (min_partition_size = 16, max_partition_size = 64);

CREATE TABLE IF NOT EXISTS decision_traces (
    trace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id STRING NOT NULL,
    incident_text STRING NOT NULL,
    recommendation STRING NULL,
    status STRING NOT NULL CHECK (status IN ('recommended', 'held')),
    candidate_trace JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
