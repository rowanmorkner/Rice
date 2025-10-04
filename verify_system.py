#!/usr/bin/env python3
"""
Verification script for Water-Opt MVP.

Tests all completed functionality and generates a report.
"""

import sys
from pathlib import Path
import pandas as pd

def check_file_exists(path: Path, description: str) -> bool:
    """Check if file exists and report."""
    if path.exists():
        size_mb = path.stat().st_size / 1024 / 1024
        print(f"  ✓ {description}: {path.name} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"  ✗ {description}: MISSING - {path}")
        return False

def verify_parquet(path: Path, min_rows: int = 1) -> dict:
    """Verify parquet file and return stats."""
    try:
        df = pd.read_parquet(path)
        stats = {
            "rows": len(df),
            "columns": list(df.columns),
            "size_mb": path.stat().st_size / 1024 / 1024
        }

        if len(df) >= min_rows:
            print(f"  ✓ {path.name}: {len(df):,} rows, {len(df.columns)} cols")
        else:
            print(f"  ✗ {path.name}: Only {len(df)} rows (expected >= {min_rows})")

        return stats
    except Exception as e:
        print(f"  ✗ {path.name}: Error reading - {e}")
        return None

def main():
    print("=" * 60)
    print("Water-Opt MVP - System Verification")
    print("=" * 60)

    all_checks_passed = True
    data_dir = Path("data")

    # Check directories
    print("\n1. Directory Structure:")
    dirs = ["data/raw/b120", "data/stage", "data/mart"]
    for dir_path in dirs:
        if Path(dir_path).exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - MISSING")
            all_checks_passed = False

    # Check manifest
    print("\n2. Manifest:")
    manifest_path = data_dir / "manifest.csv"
    if check_file_exists(manifest_path, "Manifest"):
        df_manifest = pd.read_csv(manifest_path)
        print(f"    - Total artifacts logged: {len(df_manifest)}")
        print(f"    - Sources: {', '.join(df_manifest['source'].unique())}")
    else:
        all_checks_passed = False

    # Check AWDB outputs
    print("\n3. AWDB (Snow Water Equivalent) Data:")
    awdb_stage = data_dir / "stage" / "awdb_swe_daily.parquet"
    awdb_mart = data_dir / "mart" / "hydro_scenarios.parquet"

    if awdb_stage.exists():
        stats = verify_parquet(awdb_stage, min_rows=1000)
        if stats:
            print(f"    - Date range: {pd.read_parquet(awdb_stage)['date'].min()} to {pd.read_parquet(awdb_stage)['date'].max()}")
            print(f"    - Stations: {pd.read_parquet(awdb_stage)['station_id'].nunique()}")
    else:
        print(f"  ✗ awdb_swe_daily.parquet - MISSING")
        all_checks_passed = False

    if awdb_mart.exists():
        stats = verify_parquet(awdb_mart, min_rows=12)
        if stats:
            df_scenarios = pd.read_parquet(awdb_mart)
            print(f"    - Months covered: {df_scenarios['month'].nunique()}/12")
    else:
        print(f"  ✗ hydro_scenarios.parquet - MISSING")
        all_checks_passed = False

    # Check Bulletin 120 outputs
    print("\n4. Bulletin 120 (Water Supply Forecasts):")
    b120_pdf = data_dir / "raw" / "b120" / "b120apr22.pdf"
    b120_stage = data_dir / "stage" / "b120_forecast.parquet"

    if b120_pdf.exists():
        print(f"  ✓ Raw PDF downloaded: {b120_pdf.name} ({b120_pdf.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        print(f"  ✗ Raw PDF - MISSING")
        all_checks_passed = False

    if b120_stage.exists():
        stats = verify_parquet(b120_stage, min_rows=10)
        if stats:
            df_b120 = pd.read_parquet(b120_stage)
            print(f"    - Basins: {df_b120['basin'].nunique()}")
            print(f"    - Report date: {df_b120['report_date'].iloc[0]}")
            print(f"    - Sample basins: {', '.join(df_b120['basin'].head(3).tolist())}")
    else:
        print(f"  ✗ b120_forecast.parquet - MISSING")
        all_checks_passed = False

    # Check utilities
    print("\n5. ETL Utilities:")
    utils = [
        "etl/utils_pdf.py",
        "etl/utils_manifest.py",
        "etl/fetch_awdb.py",
        "etl/fetch_b120.py"
    ]
    for util in utils:
        if Path(util).exists():
            print(f"  ✓ {util}")
        else:
            print(f"  ✗ {util} - MISSING")
            all_checks_passed = False

    # Test imports
    print("\n6. Module Imports:")
    try:
        from etl.utils_pdf import extract_tables_fallback
        from etl.utils_manifest import append_to_manifest
        print("  ✓ etl.utils_pdf imports successfully")
        print("  ✓ etl.utils_manifest imports successfully")
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        all_checks_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✓ ALL CHECKS PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME CHECKS FAILED - Review above")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
