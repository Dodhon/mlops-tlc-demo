from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class DatasetVersion(ContractModel):
    dataset_id: str = Field(min_length=1)
    dataset_name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    stage: Literal["raw", "clean", "train", "validation", "score"]
    upstream_dataset_id: str | None = None
    source_type: str = Field(min_length=1)
    source_uri: str = Field(min_length=1)
    artifact_path: str = Field(min_length=1)
    schema_hash: str = Field(min_length=1)
    row_count: int = Field(ge=0)
    created_at: datetime
    quality_status: Literal["pending", "passed", "failed", "warning"]
    quality_report_path: str | None = None


class FeatureSetVersion(ContractModel):
    feature_set_id: str = Field(min_length=1)
    feature_set_name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    input_dataset_id: str = Field(min_length=1)
    entity_key: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    feature_list: list[str] = Field(min_length=1)
    code_version: str = Field(min_length=1)
    artifact_path: str = Field(min_length=1)
    created_at: datetime


class ModelVersion(ContractModel):
    registered_model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    stage: Literal["candidate", "staging", "production", "archived"]
    mlflow_run_id: str = Field(min_length=1)
    algorithm: str = Field(min_length=1)
    feature_set_id: str = Field(min_length=1)
    train_dataset_id: str = Field(min_length=1)
    validation_dataset_id: str = Field(min_length=1)
    primary_metric: str = Field(min_length=1)
    primary_metric_value: float
    baseline_metric_value: float
    champion_metric_value: float | None = None
    promotion_status: Literal["pending", "approved", "rejected"]
    artifact_uri: str = Field(min_length=1)
    created_at: datetime


class PredictionBatch(ContractModel):
    prediction_batch_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    input_dataset_id: str = Field(min_length=1)
    output_path: str = Field(min_length=1)
    row_count: int = Field(ge=0)
    scored_at: datetime
    monitoring_report_path: str | None = None
