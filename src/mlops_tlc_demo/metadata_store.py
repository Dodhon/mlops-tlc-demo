from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .contracts import DatasetVersion, FeatureSetVersion, ModelVersion, PredictionBatch


def _schema_path() -> Path:
    return Path(__file__).with_name("metadata_schema.sql")


def initialize_metadata_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = _schema_path().read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as connection:
        connection.executescript(schema_sql)


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


class MetadataStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        initialize_metadata_db(db_path)

    def save_dataset_version(self, dataset: DatasetVersion) -> None:
        with _connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO dataset_versions (
                    dataset_id,
                    dataset_name,
                    version,
                    stage,
                    upstream_dataset_id,
                    source_type,
                    source_uri,
                    artifact_path,
                    schema_hash,
                    row_count,
                    created_at,
                    quality_status,
                    quality_report_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dataset.dataset_id,
                    dataset.dataset_name,
                    dataset.version,
                    dataset.stage,
                    dataset.upstream_dataset_id,
                    dataset.source_type,
                    dataset.source_uri,
                    dataset.artifact_path,
                    dataset.schema_hash,
                    dataset.row_count,
                    dataset.created_at.isoformat(),
                    dataset.quality_status,
                    dataset.quality_report_path,
                ),
            )

    def get_dataset_version(self, dataset_id: str) -> DatasetVersion | None:
        with _connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM dataset_versions WHERE dataset_id = ?",
                (dataset_id,),
            ).fetchone()
        if row is None:
            return None
        return DatasetVersion.model_validate(dict(row))

    def save_feature_set_version(self, feature_set: FeatureSetVersion) -> None:
        with _connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO feature_set_versions (
                    feature_set_id, feature_set_name, version, input_dataset_id, entity_key,
                    target_name, feature_list_json, code_version, artifact_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feature_set.feature_set_id,
                    feature_set.feature_set_name,
                    feature_set.version,
                    feature_set.input_dataset_id,
                    feature_set.entity_key,
                    feature_set.target_name,
                    json.dumps(feature_set.feature_list),
                    feature_set.code_version,
                    feature_set.artifact_path,
                    feature_set.created_at.isoformat(),
                ),
            )

    def get_feature_set_version(self, feature_set_id: str) -> FeatureSetVersion | None:
        with _connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM feature_set_versions WHERE feature_set_id = ?",
                (feature_set_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["feature_list"] = json.loads(payload.pop("feature_list_json"))
        return FeatureSetVersion.model_validate(payload)

    def save_model_version(self, model_version: ModelVersion) -> None:
        catalog_model_id = self._catalog_model_id(model_version)
        with _connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO model_versions (
                    catalog_model_id, registered_model_name, model_version, stage, mlflow_run_id,
                    algorithm, feature_set_id, train_dataset_id, validation_dataset_id,
                    primary_metric, primary_metric_value, baseline_metric_value,
                    champion_metric_value, promotion_status, artifact_uri, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    catalog_model_id,
                    model_version.registered_model_name,
                    model_version.model_version,
                    model_version.stage,
                    model_version.mlflow_run_id,
                    model_version.algorithm,
                    model_version.feature_set_id,
                    model_version.train_dataset_id,
                    model_version.validation_dataset_id,
                    model_version.primary_metric,
                    model_version.primary_metric_value,
                    model_version.baseline_metric_value,
                    model_version.champion_metric_value,
                    model_version.promotion_status,
                    model_version.artifact_uri,
                    model_version.created_at.isoformat(),
                ),
            )

    def get_model_version(
        self,
        registered_model_name: str,
        model_version: str,
    ) -> ModelVersion | None:
        catalog_model_id = self._catalog_model_id_parts(registered_model_name, model_version)
        with _connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM model_versions WHERE catalog_model_id = ?",
                (catalog_model_id,),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload.pop("catalog_model_id", None)
        return ModelVersion.model_validate(payload)

    def save_prediction_batch(self, prediction_batch: PredictionBatch) -> None:
        with _connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO prediction_batches (
                    prediction_batch_id, model_name, model_version, input_dataset_id,
                    output_path, row_count, scored_at, monitoring_report_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prediction_batch.prediction_batch_id,
                    prediction_batch.model_name,
                    prediction_batch.model_version,
                    prediction_batch.input_dataset_id,
                    prediction_batch.output_path,
                    prediction_batch.row_count,
                    prediction_batch.scored_at.isoformat(),
                    prediction_batch.monitoring_report_path,
                ),
            )

    def get_prediction_batch(self, prediction_batch_id: str) -> PredictionBatch | None:
        with _connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM prediction_batches WHERE prediction_batch_id = ?",
                (prediction_batch_id,),
            ).fetchone()
        if row is None:
            return None
        return PredictionBatch.model_validate(dict(row))

    @staticmethod
    def _catalog_model_id(model_version: ModelVersion) -> str:
        return MetadataStore._catalog_model_id_parts(
            model_version.registered_model_name,
            model_version.model_version,
        )

    @staticmethod
    def _catalog_model_id_parts(registered_model_name: str, model_version: str) -> str:
        return f"{registered_model_name}:{model_version}"
