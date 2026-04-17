-- Index for faster lookups on experiment_results
CREATE INDEX IF NOT EXISTS idx_experiment_results_experiment_id
ON experiment_results(experiment_id);

CREATE INDEX IF NOT EXISTS idx_experiment_results_timestamp
ON experiment_results(timestamp);

-- Indexes for client_results
CREATE INDEX IF NOT EXISTS idx_client_results_experiment_id
ON client_results(experiment_id);

CREATE INDEX IF NOT EXISTS idx_client_results_experiment_round
ON client_results(experiment_id, round);

CREATE INDEX IF NOT EXISTS idx_client_results_client_id
ON client_results(client_id);

CREATE INDEX IF NOT EXISTS idx_client_results_timestamp
ON client_results(timestamp);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_client_results_lookup
ON client_results(experiment_id, round, client_id);
COMMIT;