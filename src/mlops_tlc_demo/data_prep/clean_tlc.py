from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from mlops_tlc_demo.config import AppPaths, build_app_paths
from mlops_tlc_demo.contracts import DatasetVersion
from mlops_tlc_demo.ingestion.tlc import build_raw_dataset_id, inspect_parquet, normalize_month
from mlops_tlc_demo.metadata_store import MetadataStore

REQUIRED_COLUMNS = [
    "VendorID",
    "passenger_count",
    "trip_distance",
    "PULocationID",
    "DOLocationID",
    "RatecodeID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "fare_amount",
]


class RawDatasetNotFoundError(RuntimeError):
    """Raised when a clean run is requested before a raw dataset is registered."""


class SchemaContractError(RuntimeError):
    """Raised when the raw dataset is missing required columns."""


class CatastrophicDataQualityError(RuntimeError):
    """Raised when cleaning removes effectively all usable rows."""


@dataclass(frozen=True)
class CleanResult:
    dataset: DatasetVersion
    artifact_absolute_path: Path
    quality_report_absolute_path: Path
    quality_report: dict[str, object]


def build_clean_dataset_id(month: str) -> str:
    normalized_month = normalize_month(month).replace("-", "_")
    return f"tlc_yellow_clean_{normalized_month}"


def build_clean_artifact_relative_path(month: str) -> Path:
    normalized_month = normalize_month(month)
    return Path("data") / "clean" / "yellow" / normalized_month / "data.parquet"


def build_quality_report_relative_path(month: str) -> Path:
    normalized_month = normalize_month(month)
    return Path("artifacts") / "data_quality" / "yellow" / normalized_month / "report.json"


def _schema_columns(parquet_path: Path) -> list[str]:
    connection = duckdb.connect()
    try:
        rows = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)",
            [str(parquet_path)],
        ).fetchall()
    finally:
        connection.close()
    return [row[0] for row in rows]


def _validate_required_columns(parquet_path: Path) -> None:
    columns = set(_schema_columns(parquet_path))
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing_columns:
        raise SchemaContractError(
            f"Raw dataset is missing required columns: {', '.join(missing_columns)}"
        )


def _compute_quality_summary(raw_parquet_path: Path) -> dict[str, int]:
    connection = duckdb.connect()
    try:
        query = """
            SELECT
                COUNT(*) AS input_row_count,
                COUNT(*) FILTER (
                    WHERE tpep_pickup_datetime IS NULL OR tpep_dropoff_datetime IS NULL
                ) AS missing_timestamp_rows,
                COUNT(*) FILTER (
                    WHERE date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) <= 0
                ) AS non_positive_duration_rows,
                COUNT(*) FILTER (
                    WHERE date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) > 720
                ) AS extreme_duration_rows,
                COUNT(*) FILTER (
                    WHERE trip_distance < 0 OR trip_distance > 200
                ) AS broken_distance_rows,
                COUNT(*) FILTER (
                    WHERE fare_amount < 0 OR fare_amount > 1000
                ) AS extreme_fare_rows
            FROM read_parquet(?)
        """
        row = connection.execute(query, [str(raw_parquet_path)]).fetchone()
    finally:
        connection.close()

    return {
        "input_row_count": int(row[0]),
        "missing_timestamp_rows": int(row[1]),
        "non_positive_duration_rows": int(row[2]),
        "extreme_duration_rows": int(row[3]),
        "broken_distance_rows": int(row[4]),
        "extreme_fare_rows": int(row[5]),
    }


def _write_clean_parquet(raw_parquet_path: Path, clean_parquet_path: Path) -> None:
    clean_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    try:
        escaped_destination = str(clean_parquet_path).replace("'", "''")
        query = """
            COPY (
                SELECT *
                FROM read_parquet(?)
                WHERE tpep_pickup_datetime IS NOT NULL
                  AND tpep_dropoff_datetime IS NOT NULL
                  AND date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) > 0
                  AND date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) <= 720
                  AND trip_distance >= 0
                  AND trip_distance <= 200
                  AND fare_amount >= 0
                  AND fare_amount <= 1000
            ) TO '__DESTINATION__' (FORMAT PARQUET)
        """.replace("__DESTINATION__", escaped_destination)
        connection.execute(query, [str(raw_parquet_path)])
    finally:
        connection.close()


def clean_yellow_taxi_month(
    month: str,
    *,
    replace: bool = False,
    app_paths: AppPaths | None = None,
    metadata_store: MetadataStore | None = None,
) -> CleanResult:
    paths = app_paths or build_app_paths()
    store = metadata_store or MetadataStore(paths.metadata_db_path)

    normalized_month = normalize_month(month)
    raw_dataset_id = build_raw_dataset_id(normalized_month)
    raw_dataset = store.get_dataset_version(raw_dataset_id)
    if raw_dataset is None:
        raise RawDatasetNotFoundError(
            f"Raw dataset {raw_dataset_id!r} was not found in the metadata store."
        )

    clean_dataset_id = build_clean_dataset_id(normalized_month)
    existing_clean_dataset = store.get_dataset_version(clean_dataset_id)
    if existing_clean_dataset is not None and not replace:
        raise RuntimeError(
            "Clean dataset version "
            f"{clean_dataset_id!r} already exists. Use replace=True to overwrite it."
        )

    raw_parquet_path = paths.repo_root / raw_dataset.artifact_path
    _validate_required_columns(raw_parquet_path)

    quality_summary = _compute_quality_summary(raw_parquet_path)
    clean_artifact_relative_path = build_clean_artifact_relative_path(normalized_month)
    clean_artifact_absolute_path = paths.repo_root / clean_artifact_relative_path
    _write_clean_parquet(raw_parquet_path, clean_artifact_absolute_path)
    output_row_count, schema_hash = inspect_parquet(clean_artifact_absolute_path)

    removed_row_count = quality_summary["input_row_count"] - output_row_count
    removed_fraction = (
        removed_row_count / quality_summary["input_row_count"]
        if quality_summary["input_row_count"] > 0
        else 1.0
    )
    if output_row_count == 0 or removed_fraction >= 0.95:
        raise CatastrophicDataQualityError(
            "Cleaning removed too many rows to produce a usable clean dataset."
        )

    quality_status = "warning" if removed_fraction >= 0.25 else "passed"
    quality_report = {
        "input_dataset_id": raw_dataset.dataset_id,
        "output_dataset_id": clean_dataset_id,
        "input_row_count": quality_summary["input_row_count"],
        "output_row_count": output_row_count,
        "removed_row_count": removed_row_count,
        "removed_fraction": removed_fraction,
        "quality_status": quality_status,
        "checks": quality_summary,
    }

    quality_report_relative_path = build_quality_report_relative_path(normalized_month)
    quality_report_absolute_path = paths.repo_root / quality_report_relative_path
    quality_report_absolute_path.parent.mkdir(parents=True, exist_ok=True)
    quality_report_absolute_path.write_text(
        json.dumps(quality_report, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    clean_dataset = DatasetVersion(
        dataset_id=clean_dataset_id,
        dataset_name="tlc_yellow_clean",
        version=normalized_month,
        stage="clean",
        upstream_dataset_id=raw_dataset.dataset_id,
        source_type="local_artifact",
        source_uri=raw_dataset.artifact_path,
        artifact_path=clean_artifact_relative_path.as_posix(),
        schema_hash=schema_hash,
        row_count=output_row_count,
        created_at=datetime.now(tz=UTC),
        quality_status=quality_status,
        quality_report_path=quality_report_relative_path.as_posix(),
    )
    store.save_dataset_version(clean_dataset)

    return CleanResult(
        dataset=clean_dataset,
        artifact_absolute_path=clean_artifact_absolute_path,
        quality_report_absolute_path=quality_report_absolute_path,
        quality_report=quality_report,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Clean a monthly NYC TLC yellow taxi parquet file into a validated artifact."
    )
    parser.add_argument("--month", required=True, help="Target month in YYYY-MM format.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing clean dataset version for this month.",
    )
    return parser


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    result = clean_yellow_taxi_month(args.month, replace=args.replace)
    print(json.dumps(result.dataset.model_dump(mode="json"), indent=2))
    print(f"artifact_absolute_path={result.artifact_absolute_path}")
    print(f"quality_report_absolute_path={result.quality_report_absolute_path}")


if __name__ == "__main__":
    main()
