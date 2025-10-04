"""
Manifest tracking utilities for ETL pipeline.

Maintains a CSV log of all data artifacts with metadata.
"""

import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Union
import pandas as pd

logger = logging.getLogger(__name__)

MANIFEST_COLUMNS = [
    "timestamp",
    "artifact_path",
    "artifact_type",
    "row_count",
    "file_size_bytes",
    "sha256_hash",
    "source",
    "notes"
]


def get_manifest_path(data_dir: Path = Path("data")) -> Path:
    """Get path to manifest CSV file."""
    return data_dir / "manifest.csv"


def init_manifest(data_dir: Path = Path("data")) -> None:
    """
    Initialize manifest.csv if it doesn't exist.

    Args:
        data_dir: Root data directory
    """
    manifest_path = get_manifest_path(data_dir)

    if not manifest_path.exists():
        logger.info(f"Creating manifest at {manifest_path}")
        df = pd.DataFrame(columns=MANIFEST_COLUMNS)
        df.to_csv(manifest_path, index=False)
    else:
        logger.debug(f"Manifest already exists at {manifest_path}")


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal hash string
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_row_count(file_path: Path) -> Optional[int]:
    """
    Get row count for supported file types.

    Args:
        file_path: Path to data file

    Returns:
        Row count, or None if unsupported format
    """
    suffix = file_path.suffix.lower()

    try:
        if suffix == ".parquet":
            df = pd.read_parquet(file_path)
            return len(df)
        elif suffix == ".csv":
            df = pd.read_csv(file_path)
            return len(df)
        elif suffix == ".geojson":
            import geopandas as gpd
            gdf = gpd.read_file(file_path)
            return len(gdf)
        else:
            logger.debug(f"Row count not supported for {suffix}")
            return None
    except Exception as e:
        logger.warning(f"Could not count rows in {file_path.name}: {e}")
        return None


def append_to_manifest(
    artifact_path: Union[str, Path],
    source: str,
    artifact_type: str = "data",
    notes: str = "",
    data_dir: Path = Path("data")
) -> None:
    """
    Append a new artifact entry to the manifest.

    Args:
        artifact_path: Path to the artifact (relative to project root or absolute)
        source: Data source name (e.g., "AWDB", "Bulletin_120", "ERS")
        artifact_type: Type of artifact ("data", "geojson", "pdf", etc.)
        notes: Optional notes about this artifact
        data_dir: Root data directory containing manifest
    """
    artifact_path = Path(artifact_path)

    if not artifact_path.exists():
        logger.error(f"Artifact does not exist: {artifact_path}")
        return

    # Initialize manifest if needed
    init_manifest(data_dir)

    # Gather metadata
    timestamp = datetime.now().isoformat()
    file_size = artifact_path.stat().st_size
    file_hash = compute_file_hash(artifact_path)
    row_count = get_row_count(artifact_path)

    # Make path relative to project root if possible
    try:
        rel_path = artifact_path.relative_to(Path.cwd())
    except ValueError:
        rel_path = artifact_path

    # Create new entry
    entry = {
        "timestamp": timestamp,
        "artifact_path": str(rel_path),
        "artifact_type": artifact_type,
        "row_count": row_count,
        "file_size_bytes": file_size,
        "sha256_hash": file_hash,
        "source": source,
        "notes": notes
    }

    # Append to manifest
    manifest_path = get_manifest_path(data_dir)
    df_manifest = pd.read_csv(manifest_path)
    df_new = pd.DataFrame([entry])
    df_combined = pd.concat([df_manifest, df_new], ignore_index=True)
    df_combined.to_csv(manifest_path, index=False)

    logger.info(
        f"Manifest updated: {rel_path} ({row_count} rows, {file_size:,} bytes) from {source}"
    )


def get_latest_artifact(
    source: str,
    data_dir: Path = Path("data")
) -> Optional[Path]:
    """
    Get path to the most recent artifact from a given source.

    Args:
        source: Data source name
        data_dir: Root data directory

    Returns:
        Path to latest artifact, or None if not found
    """
    manifest_path = get_manifest_path(data_dir)

    if not manifest_path.exists():
        logger.warning("Manifest does not exist")
        return None

    df_manifest = pd.read_csv(manifest_path)

    # Filter by source
    df_source = df_manifest[df_manifest["source"] == source]

    if df_source.empty:
        logger.warning(f"No artifacts found for source: {source}")
        return None

    # Get most recent
    df_source = df_source.sort_values("timestamp", ascending=False)
    latest_path = Path(df_source.iloc[0]["artifact_path"])

    if not latest_path.exists():
        logger.warning(f"Latest artifact no longer exists: {latest_path}")
        return None

    return latest_path
