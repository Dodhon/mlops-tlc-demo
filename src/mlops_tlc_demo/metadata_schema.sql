CREATE TABLE IF NOT EXISTS dataset_versions (
    dataset_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    version TEXT NOT NULL,
    stage TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    schema_hash TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    quality_status TEXT NOT NULL,
    quality_report_path TEXT
);

CREATE TABLE IF NOT EXISTS feature_set_versions (
    feature_set_id TEXT PRIMARY KEY,
    feature_set_name TEXT NOT NULL,
    version TEXT NOT NULL,
    input_dataset_id TEXT NOT NULL,
    entity_key TEXT NOT NULL,
    target_name TEXT NOT NULL,
    feature_list_json TEXT NOT NULL,
    code_version TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_versions (
    catalog_model_id TEXT PRIMARY KEY,
    registered_model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    stage TEXT NOT NULL,
    mlflow_run_id TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    feature_set_id TEXT NOT NULL,
    train_dataset_id TEXT NOT NULL,
    validation_dataset_id TEXT NOT NULL,
    primary_metric TEXT NOT NULL,
    primary_metric_value REAL NOT NULL,
    baseline_metric_value REAL NOT NULL,
    champion_metric_value REAL,
    promotion_status TEXT NOT NULL,
    artifact_uri TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prediction_batches (
    prediction_batch_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    input_dataset_id TEXT NOT NULL,
    output_path TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    scored_at TEXT NOT NULL,
    monitoring_report_path TEXT
);
