from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from mlops_tlc_demo.config import build_app_paths
from mlops_tlc_demo.ingestion.tlc import (
    DuplicateDatasetVersionError,
    build_raw_artifact_relative_path,
    build_tlc_yellow_source_url,
    ingest_yellow_taxi_month,
)
from mlops_tlc_demo.metadata_store import MetadataStore


def _write_sample_parquet(path: Path) -> None:
    connection = duckdb.connect()
    try:
        connection.execute(
            """
            CREATE TABLE sample_trips AS
            SELECT
                1 AS vendor_id,
                1 AS passenger_count,
                3.4 AS trip_distance,
                TIMESTAMP '2026-01-01 12:00:00' AS tpep_pickup_datetime,
                TIMESTAMP '2026-01-01 12:20:00' AS tpep_dropoff_datetime
            """
        )
        connection.execute("COPY sample_trips TO ? (FORMAT PARQUET)", [str(path)])
    finally:
        connection.close()


def test_build_tlc_yellow_source_url_uses_official_pattern() -> None:
    assert (
        build_tlc_yellow_source_url("2026-02")
        == "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-02.parquet"
    )


def test_ingest_registers_raw_dataset_from_local_file_uri(tmp_path: Path) -> None:
    source_path = tmp_path / "yellow_tripdata_2026-01.parquet"
    _write_sample_parquet(source_path)

    app_paths = build_app_paths(tmp_path)
    store = MetadataStore(app_paths.metadata_db_path)

    result = ingest_yellow_taxi_month(
        "2026-01",
        source_url=source_path.as_uri(),
        app_paths=app_paths,
        metadata_store=store,
    )

    assert result.dataset.dataset_id == "tlc_yellow_raw_2026_01"
    assert result.dataset.row_count == 1
    assert result.dataset.artifact_path == build_raw_artifact_relative_path("2026-01").as_posix()
    assert result.artifact_absolute_path.exists()
    assert result.dataset.schema_hash

    stored_dataset = store.get_dataset_version(result.dataset.dataset_id)
    assert stored_dataset == result.dataset


def test_ingest_blocks_duplicate_dataset_without_replace(tmp_path: Path) -> None:
    source_path = tmp_path / "yellow_tripdata_2026-02.parquet"
    _write_sample_parquet(source_path)

    app_paths = build_app_paths(tmp_path)
    store = MetadataStore(app_paths.metadata_db_path)

    ingest_yellow_taxi_month(
        "2026-02",
        source_url=source_path.as_uri(),
        app_paths=app_paths,
        metadata_store=store,
    )

    with pytest.raises(DuplicateDatasetVersionError):
        ingest_yellow_taxi_month(
            "2026-02",
            source_url=source_path.as_uri(),
            app_paths=app_paths,
            metadata_store=store,
        )
