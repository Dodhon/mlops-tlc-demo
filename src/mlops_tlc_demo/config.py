from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppPaths:
    repo_root: Path
    data_dir: Path
    raw_data_dir: Path
    clean_data_dir: Path
    feature_data_dir: Path
    prediction_data_dir: Path
    artifacts_dir: Path
    metadata_dir: Path
    metadata_db_path: Path


def build_app_paths(root: Path | None = None) -> AppPaths:
    actual_root = root or repo_root()
    data_dir = actual_root / "data"
    artifacts_dir = actual_root / "artifacts"
    metadata_dir = actual_root / ".local" / "metadata"

    return AppPaths(
        repo_root=actual_root,
        data_dir=data_dir,
        raw_data_dir=data_dir / "raw",
        clean_data_dir=data_dir / "clean",
        feature_data_dir=data_dir / "features",
        prediction_data_dir=data_dir / "predictions",
        artifacts_dir=artifacts_dir,
        metadata_dir=metadata_dir,
        metadata_db_path=metadata_dir / "catalog.sqlite3",
    )
