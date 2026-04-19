from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from mlops_tlc_demo.contracts import (
    DatasetVersion,
    FeatureSetVersion,
    ModelVersion,
    PredictionBatch,
)
from mlops_tlc_demo.metadata_store import MetadataStore


def test_metadata_store_round_trip_for_all_entities(tmp_path: Path) -> None:
    store = MetadataStore(tmp_path / "catalog.sqlite3")

    dataset = DatasetVersion(
        dataset_id="tlc_yellow_clean_2026_01",
        dataset_name="tlc_yellow_clean",
        version="2026-01",
        stage="clean",
        source_type="local_artifact",
        source_uri="data/raw/yellow/2026-01/data.parquet",
        artifact_path="data/clean/yellow/2026-01/data.parquet",
        schema_hash="sha256:dataset",
        row_count=10,
        created_at=datetime.now(tz=UTC),
        quality_status="passed",
        quality_report_path="artifacts/data_quality/raw_2026_01.json",
    )
    store.save_dataset_version(dataset)
    loaded_dataset = store.get_dataset_version(dataset.dataset_id)
    assert loaded_dataset == dataset

    feature_set = FeatureSetVersion(
        feature_set_id="trip_duration_features_v1_2026_01",
        feature_set_name="trip_duration_features",
        version="v1",
        input_dataset_id=dataset.dataset_id,
        entity_key="trip_id",
        target_name="trip_duration_minutes",
        feature_list=[
            "pickup_hour",
            "pickup_weekday",
            "trip_distance",
            "pickup_location_id",
            "dropoff_location_id",
        ],
        code_version="abc123",
        artifact_path="data/features/trip_duration/v1/2026-01/features.parquet",
        created_at=datetime.now(tz=UTC),
    )
    store.save_feature_set_version(feature_set)
    loaded_feature_set = store.get_feature_set_version(feature_set.feature_set_id)
    assert loaded_feature_set == feature_set

    model_version = ModelVersion(
        registered_model_name="xgb_trip_duration",
        model_version="7",
        stage="candidate",
        mlflow_run_id="run-123",
        algorithm="xgboost_regressor",
        feature_set_id=feature_set.feature_set_id,
        train_dataset_id=dataset.dataset_id,
        validation_dataset_id=dataset.dataset_id,
        primary_metric="mae",
        primary_metric_value=3.82,
        baseline_metric_value=4.41,
        champion_metric_value=3.90,
        promotion_status="pending",
        artifact_uri="models:/xgb_trip_duration/7",
        created_at=datetime.now(tz=UTC),
    )
    store.save_model_version(model_version)
    loaded_model_version = store.get_model_version(
        model_version.registered_model_name,
        model_version.model_version,
    )
    assert loaded_model_version == model_version

    prediction_batch = PredictionBatch(
        prediction_batch_id="pred_2026_02_v7",
        model_name=model_version.registered_model_name,
        model_version=model_version.model_version,
        input_dataset_id=dataset.dataset_id,
        output_path="data/predictions/2026-02/v7/predictions.parquet",
        row_count=10,
        scored_at=datetime.now(tz=UTC),
        monitoring_report_path="artifacts/monitoring/2026-02_v7_report.json",
    )
    store.save_prediction_batch(prediction_batch)
    loaded_prediction_batch = store.get_prediction_batch(prediction_batch.prediction_batch_id)
    assert loaded_prediction_batch == prediction_batch
