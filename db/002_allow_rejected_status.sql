ALTER TABLE decision_traces
    ADD CONSTRAINT check_status_v2
    CHECK (status IN ('recommended', 'held', 'rejected'));

ALTER TABLE decision_traces
    DROP CONSTRAINT check_status;
