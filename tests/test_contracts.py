from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mlops_tlc_demo.contracts import (
    DatasetVersion,
    FeatureSetVersion,
    ModelVersion,
    PredictionBatch,
)


def test_dataset_version_accepts_valid_payload() -> None:
    dataset = DatasetVersion(
        dataset_id="tlc_yellow_raw_2026_01",
        dataset_name="tlc_yellow_raw",
        version="2026-01",
        stage="raw",
        source_type="external_file",
        source_uri="https://example.com/yellow_tripdata_2026-01.parquet",
        artifact_path="data/raw/yellow/2026-01/data.parquet",
        schema_hash="sha256:abc",
        row_count=100,
        created_at=datetime.now(tz=UTC),
        quality_status="pending",
    )

    assert dataset.dataset_id == "tlc_yellow_raw_2026_01"


def test_feature_set_version_requires_non_empty_feature_list() -> None:
    with pytest.raises(ValidationError):
        FeatureSetVersion(
            feature_set_id="trip_duration_features_v1_2026_01",
            feature_set_name="trip_duration_features",
            version="v1",
            input_dataset_id="tlc_yellow_clean_2026_01",
            entity_key="trip_id",
            target_name="trip_duration_minutes",
            feature_list=[],
            code_version="abc123",
            artifact_path="data/features/trip_duration/v1/2026-01/features.parquet",
            created_at=datetime.now(tz=UTC),
        )


def test_model_version_requires_registered_model_name() -> None:
    with pytest.raises(ValidationError):
        ModelVersion(
            registered_model_name="",
            model_version="7",
            stage="candidate",
            mlflow_run_id="run-1",
            algorithm="xgboost_regressor",
            feature_set_id="trip_duration_features_v1_2026_01",
            train_dataset_id="tlc_yellow_train_2026_01",
            validation_dataset_id="tlc_yellow_valid_2026_01",
            primary_metric="mae",
            primary_metric_value=3.82,
            baseline_metric_value=4.41,
            champion_metric_value=3.9,
            promotion_status="pending",
            artifact_uri="models:/xgb_trip_duration/7",
            created_at=datetime.now(tz=UTC),
        )


def test_prediction_batch_rejects_negative_row_count() -> None:
    with pytest.raises(ValidationError):
        PredictionBatch(
            prediction_batch_id="pred_2026_02_v7",
            model_name="xgb_trip_duration",
            model_version="7",
            input_dataset_id="tlc_yellow_score_2026_02",
            output_path="data/predictions/2026-02/v7/predictions.parquet",
            row_count=-1,
            scored_at=datetime.now(tz=UTC),
        )
