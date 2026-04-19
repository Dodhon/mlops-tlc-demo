from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from mlops_tlc_demo.config import build_app_paths
from mlops_tlc_demo.data_prep.clean_tlc import (
    SchemaContractError,
    build_clean_artifact_relative_path,
    build_clean_dataset_id,
    clean_yellow_taxi_month,
)
from mlops_tlc_demo.ingestion.tlc import ingest_yellow_taxi_month
from mlops_tlc_demo.metadata_store import MetadataStore


def _write_valid_raw_parquet(path: Path) -> None:
    first_good_row = (
        1,
        1,
        3.4,
        161,
        236,
        1,
        "2026-02-01 08:00:00",
        "2026-02-01 08:20:00",
        18.5,
    )
    negative_distance_row = (
        1,
        1,
        -5.0,
        161,
        236,
        1,
        "2026-02-01 09:00:00",
        "2026-02-01 09:20:00",
        18.5,
    )
    missing_timestamp_row = (
        1,
        1,
        3.4,
        161,
        236,
        1,
        None,
        "2026-02-01 10:20:00",
        18.5,
    )
    reversed_duration_row = (
        1,
        1,
        3.4,
        161,
        236,
        1,
        "2026-02-01 11:20:00",
        "2026-02-01 10:20:00",
        18.5,
    )
    extreme_fare_row = (
        1,
        1,
        3.4,
        161,
        236,
        1,
        "2026-02-01 12:00:00",
        "2026-02-01 12:20:00",
        2000.0,
    )

    connection = duckdb.connect()
    try:
        connection.execute(
            """
            CREATE TABLE raw_trips AS
            SELECT * FROM (
                VALUES
                    (?, ?, ?, ?, ?, ?, CAST(? AS TIMESTAMP), CAST(? AS TIMESTAMP), ?),
                    (?, ?, ?, ?, ?, ?, CAST(? AS TIMESTAMP), CAST(? AS TIMESTAMP), ?),
                    (?, ?, ?, ?, ?, ?, CAST(? AS TIMESTAMP), CAST(? AS TIMESTAMP), ?),
                    (?, ?, ?, ?, ?, ?, CAST(? AS TIMESTAMP), CAST(? AS TIMESTAMP), ?),
                    (?, ?, ?, ?, ?, ?, CAST(? AS TIMESTAMP), CAST(? AS TIMESTAMP), ?)
            ) AS t(
                VendorID,
                passenger_count,
                trip_distance,
                PULocationID,
                DOLocationID,
                RatecodeID,
                tpep_pickup_datetime,
                tpep_dropoff_datetime,
                fare_amount
            )
            """,
            [
                *first_good_row,
                *negative_distance_row,
                *missing_timestamp_row,
                *reversed_duration_row,
                *extreme_fare_row,
            ],
        )
        connection.execute("COPY raw_trips TO ? (FORMAT PARQUET)", [str(path)])
    finally:
        connection.close()


def _write_invalid_schema_parquet(path: Path) -> None:
    connection = duckdb.connect()
    try:
        connection.execute(
            """
            CREATE TABLE invalid_trips AS
            SELECT
                1 AS VendorID,
                1 AS passenger_count,
                3.4 AS trip_distance,
                TIMESTAMP '2026-02-01 08:00:00' AS tpep_pickup_datetime
            """
        )
        connection.execute("COPY invalid_trips TO ? (FORMAT PARQUET)", [str(path)])
    finally:
        connection.close()


def test_clean_yellow_taxi_month_filters_bad_rows_and_registers_clean_dataset(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "yellow_tripdata_2026-02.parquet"
    _write_valid_raw_parquet(source_path)

    app_paths = build_app_paths(tmp_path)
    store = MetadataStore(app_paths.metadata_db_path)
    ingest_yellow_taxi_month(
        "2026-02",
        source_url=source_path.as_uri(),
        app_paths=app_paths,
        metadata_store=store,
    )

    result = clean_yellow_taxi_month(
        "2026-02",
        app_paths=app_paths,
        metadata_store=store,
    )

    assert result.dataset.dataset_id == build_clean_dataset_id("2026-02")
    assert result.dataset.upstream_dataset_id == "tlc_yellow_raw_2026_02"
    assert result.dataset.artifact_path == build_clean_artifact_relative_path("2026-02").as_posix()
    assert result.dataset.row_count == 1
    assert result.artifact_absolute_path.exists()
    assert result.quality_report_absolute_path.exists()

    quality_report = json.loads(result.quality_report_absolute_path.read_text(encoding="utf-8"))
    assert quality_report["removed_row_count"] == 4

    stored_dataset = store.get_dataset_version(result.dataset.dataset_id)
    assert stored_dataset == result.dataset


def test_clean_yellow_taxi_month_raises_on_missing_required_columns(tmp_path: Path) -> None:
    source_path = tmp_path / "yellow_tripdata_2026-03.parquet"
    _write_invalid_schema_parquet(source_path)

    app_paths = build_app_paths(tmp_path)
    store = MetadataStore(app_paths.metadata_db_path)
    ingest_yellow_taxi_month(
        "2026-03",
        source_url=source_path.as_uri(),
        app_paths=app_paths,
        metadata_store=store,
    )

    with pytest.raises(SchemaContractError):
        clean_yellow_taxi_month(
            "2026-03",
            app_paths=app_paths,
            metadata_store=store,
        )
