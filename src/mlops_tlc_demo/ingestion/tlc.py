from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen

import duckdb

from mlops_tlc_demo.config import AppPaths, build_app_paths
from mlops_tlc_demo.contracts import DatasetVersion
from mlops_tlc_demo.metadata_store import MetadataStore

TLC_YELLOW_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"


class DuplicateDatasetVersionError(RuntimeError):
    """Raised when an ingest would silently overwrite an existing dataset version."""


@dataclass(frozen=True)
class IngestResult:
    dataset: DatasetVersion
    artifact_absolute_path: Path


def normalize_month(month: str) -> str:
    try:
        parsed = datetime.strptime(month, "%Y-%m")
    except ValueError as exc:
        raise ValueError(f"Expected month in YYYY-MM format, got {month!r}") from exc
    return parsed.strftime("%Y-%m")


def build_tlc_yellow_source_url(month: str) -> str:
    normalized_month = normalize_month(month)
    return f"{TLC_YELLOW_BASE_URL}/yellow_tripdata_{normalized_month}.parquet"


def build_raw_artifact_relative_path(month: str) -> Path:
    normalized_month = normalize_month(month)
    return Path("data") / "raw" / "yellow" / normalized_month / "data.parquet"


def build_raw_dataset_id(month: str) -> str:
    normalized_month = normalize_month(month).replace("-", "_")
    return f"tlc_yellow_raw_{normalized_month}"


def download_to_path(source_url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(".tmp")

    with urlopen(source_url, timeout=30) as response, temp_path.open("wb") as target:
        shutil.copyfileobj(response, target)

    temp_path.replace(destination)


def inspect_parquet(parquet_path: Path) -> tuple[int, str]:
    connection = duckdb.connect()
    try:
        row_count = connection.execute(
            "SELECT COUNT(*) FROM read_parquet(?)",
            [str(parquet_path)],
        ).fetchone()[0]
        schema_rows = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)",
            [str(parquet_path)],
        ).fetchall()
    finally:
        connection.close()

    schema_payload = [
        {"column_name": row[0], "column_type": row[1], "null": row[2]}
        for row in schema_rows
    ]
    schema_hash = hashlib.sha256(
        json.dumps(schema_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return int(row_count), schema_hash


def ingest_yellow_taxi_month(
    month: str,
    *,
    source_url: str | None = None,
    replace: bool = False,
    app_paths: AppPaths | None = None,
    metadata_store: MetadataStore | None = None,
) -> IngestResult:
    paths = app_paths or build_app_paths()
    store = metadata_store or MetadataStore(paths.metadata_db_path)

    normalized_month = normalize_month(month)
    dataset_id = build_raw_dataset_id(normalized_month)
    existing_dataset = store.get_dataset_version(dataset_id)
    if existing_dataset is not None and not replace:
        raise DuplicateDatasetVersionError(
            f"Dataset version {dataset_id!r} already exists. Use replace=True to overwrite it."
        )

    resolved_source_url = source_url or build_tlc_yellow_source_url(normalized_month)
    artifact_relative_path = build_raw_artifact_relative_path(normalized_month)
    artifact_absolute_path = paths.repo_root / artifact_relative_path

    download_to_path(resolved_source_url, artifact_absolute_path)
    row_count, schema_hash = inspect_parquet(artifact_absolute_path)

    dataset = DatasetVersion(
        dataset_id=dataset_id,
        dataset_name="tlc_yellow_raw",
        version=normalized_month,
        stage="raw",
        source_type="tlc_monthly_parquet",
        source_uri=resolved_source_url,
        artifact_path=artifact_relative_path.as_posix(),
        schema_hash=schema_hash,
        row_count=row_count,
        created_at=datetime.now(tz=UTC),
        quality_status="pending",
        quality_report_path=None,
    )
    store.save_dataset_version(dataset)

    return IngestResult(dataset=dataset, artifact_absolute_path=artifact_absolute_path)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest a monthly NYC TLC yellow taxi parquet file."
    )
    parser.add_argument("--month", required=True, help="Target month in YYYY-MM format.")
    parser.add_argument(
        "--source-url",
        default=None,
        help="Optional explicit source URL override. Defaults to the official TLC monthly pattern.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing raw dataset version for this month.",
    )
    return parser


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    result = ingest_yellow_taxi_month(
        args.month,
        source_url=args.source_url,
        replace=args.replace,
    )
    print(json.dumps(result.dataset.model_dump(mode="json"), indent=2))
    print(f"artifact_absolute_path={result.artifact_absolute_path}")


if __name__ == "__main__":
    main()
