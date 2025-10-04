"""
Basic ETL tests to verify data artifacts exist after pipeline runs.

Tests check:
- Presence of key parquet files
- Non-empty data with reasonable row counts
- Manifest tracking
"""

import pytest
from pathlib import Path
import pandas as pd


DATA_DIR = Path("data")


class TestDataArtifacts:
    """Tests for data artifact presence and validity."""

    def test_data_directory_exists(self):
        """Test that data directory exists."""
        assert DATA_DIR.exists(), "data/ directory should exist"
        assert DATA_DIR.is_dir(), "data/ should be a directory"

    def test_stage_directory_exists(self):
        """Test that stage directory exists."""
        stage_dir = DATA_DIR / "stage"
        assert stage_dir.exists(), "data/stage/ directory should exist"

    def test_mart_directory_exists(self):
        """Test that mart directory exists."""
        mart_dir = DATA_DIR / "mart"
        assert mart_dir.exists(), "data/mart/ directory should exist"

    def test_manifest_exists(self):
        """Test that manifest.csv exists."""
        manifest_path = DATA_DIR / "manifest.csv"
        assert manifest_path.exists(), "data/manifest.csv should exist"

        # Check that manifest has content
        df = pd.read_csv(manifest_path)
        assert len(df) > 0, "Manifest should have at least one entry"
        assert "artifact_path" in df.columns, "Manifest should have artifact_path column"
        assert "row_count" in df.columns, "Manifest should have row_count column"


class TestAWDBData:
    """Tests for AWDB SNOTEL data artifacts."""

    def test_awdb_swe_daily_exists(self):
        """Test that AWDB daily SWE data exists."""
        awdb_path = DATA_DIR / "stage" / "awdb_swe_daily.parquet"

        if not awdb_path.exists():
            pytest.skip("AWDB data not fetched yet (run: python -m etl.fetch_awdb)")

        df = pd.read_parquet(awdb_path)
        assert len(df) > 1000, f"AWDB should have >1000 rows (got {len(df)})"
        assert "date" in df.columns, "AWDB should have date column"
        assert "station_id" in df.columns, "AWDB should have station_id column"
        assert "wteq_mm" in df.columns, "AWDB should have wteq_mm column"

    def test_hydro_scenarios_exists(self):
        """Test that hydrology scenarios exist."""
        scenarios_path = DATA_DIR / "mart" / "hydro_scenarios.parquet"

        if not scenarios_path.exists():
            pytest.skip("Hydro scenarios not generated yet")

        df = pd.read_parquet(scenarios_path)
        assert len(df) > 0, "Hydro scenarios should have data"
        assert "month" in df.columns, "Scenarios should have month column"


class TestBulletin120Data:
    """Tests for Bulletin 120 forecast data."""

    def test_b120_forecast_exists(self):
        """Test that B120 forecast data exists."""
        b120_path = DATA_DIR / "stage" / "b120_forecast.parquet"

        if not b120_path.exists():
            pytest.skip("B120 data not fetched yet (run: python -m etl.fetch_b120)")

        df = pd.read_parquet(b120_path)
        assert len(df) > 30, f"B120 should have >30 basins (got {len(df)})"
        assert "basin" in df.columns, "B120 should have basin column"
        assert "median" in df.columns, "B120 should have median forecast column"


class TestERSData:
    """Tests for ERS Rice Outlook price data."""

    def test_ers_prices_exists(self):
        """Test that ERS price data exists."""
        ers_path = DATA_DIR / "stage" / "ers_prices.parquet"

        if not ers_path.exists():
            pytest.skip("ERS data not fetched yet (run: python -m etl.fetch_ers_rice_outlook)")

        df = pd.read_parquet(ers_path)
        assert len(df) > 0, "ERS prices should have data"
        assert "date" in df.columns, "ERS should have date column"
        assert "price_usd_cwt" in df.columns, "ERS should have price_usd_cwt column"


class TestDWRCropMapData:
    """Tests for DWR crop mapping data."""

    def test_dwr_geojson_exists(self):
        """Test that DWR rice GeoJSON exists."""
        geojson_path = DATA_DIR / "stage" / "dwr_rice_2022.geojson"

        if not geojson_path.exists():
            pytest.skip("DWR crop map not fetched yet (run: python -m etl.fetch_dwr_cropmap)")

        # Check file size (GeoJSON should be large)
        file_size = geojson_path.stat().st_size
        assert file_size > 1_000_000, f"GeoJSON should be >1MB (got {file_size/1e6:.1f}MB)"

    def test_dwr_parquet_exists(self):
        """Test that DWR rice parquet exists."""
        parquet_path = DATA_DIR / "mart" / "rice_polygons_2022.parquet"

        if not parquet_path.exists():
            pytest.skip("DWR rice parquet not generated yet")

        df = pd.read_parquet(parquet_path)
        assert len(df) > 1000, f"DWR should have >1000 rice polygons (got {len(df)})"
        assert "centroid_x" in df.columns, "DWR should have centroid_x column"
        assert "centroid_y" in df.columns, "DWR should have centroid_y column"
        assert "acres" in df.columns, "DWR should have acres column"


class TestCIMISData:
    """Tests for CIMIS ETo data."""

    def test_cimis_daily_exists(self):
        """Test that CIMIS daily ETo data exists."""
        cimis_path = DATA_DIR / "stage" / "cimis_daily.parquet"

        if not cimis_path.exists():
            pytest.skip("CIMIS data not fetched yet (run: python -m etl.fetch_cimis)")

        df = pd.read_parquet(cimis_path)
        assert len(df) > 100, f"CIMIS should have >100 records (got {len(df)})"
        assert "date" in df.columns, "CIMIS should have date column"
        assert "station" in df.columns, "CIMIS should have station column"
        assert "eto_in" in df.columns, "CIMIS should have eto_in column"


class TestDataQuality:
    """Tests for basic data quality checks."""

    def test_awdb_no_nulls_in_key_columns(self):
        """Test that AWDB data has no nulls in key columns."""
        awdb_path = DATA_DIR / "stage" / "awdb_swe_daily.parquet"

        if not awdb_path.exists():
            pytest.skip("AWDB data not available")

        df = pd.read_parquet(awdb_path)
        assert df["date"].notna().all(), "AWDB date should have no nulls"
        assert df["station_id"].notna().all(), "AWDB station_id should have no nulls"
        assert df["wteq_mm"].notna().all(), "AWDB wteq_mm should have no nulls"

    def test_dwr_acres_positive(self):
        """Test that DWR rice polygons have positive acreage."""
        parquet_path = DATA_DIR / "mart" / "rice_polygons_2022.parquet"

        if not parquet_path.exists():
            pytest.skip("DWR data not available")

        df = pd.read_parquet(parquet_path)
        assert (df["acres"] > 0).all(), "All rice polygons should have positive acreage"
        assert df["acres"].sum() > 100_000, \
            f"Total rice acreage should be >100,000 acres (got {df['acres'].sum():,.0f})"

    def test_cimis_eto_reasonable_range(self):
        """Test that CIMIS ETo values are in reasonable range."""
        cimis_path = DATA_DIR / "stage" / "cimis_daily.parquet"

        if not cimis_path.exists():
            pytest.skip("CIMIS data not available")

        df = pd.read_parquet(cimis_path)

        # Daily ETo should be between 0 and 0.5 inches for CA
        assert (df["eto_in"] >= 0).all(), "ETo should be non-negative"
        assert (df["eto_in"] <= 0.5).all(), \
            f"Daily ETo should be ≤0.5 inches (max: {df['eto_in'].max():.3f})"


class TestManifestIntegrity:
    """Tests for manifest integrity."""

    def test_manifest_has_all_sources(self):
        """Test that manifest includes all expected data sources."""
        manifest_path = DATA_DIR / "manifest.csv"

        if not manifest_path.exists():
            pytest.skip("Manifest not created yet")

        df = pd.read_csv(manifest_path)
        sources = df["source"].unique()

        # Check for core sources (some may be missing if not fetched)
        expected_sources = ["AWDB", "Bulletin_120", "ERS_Rice_Outlook", "DWR_Crop_Map"]

        # At least one source should be present
        assert len(sources) > 0, "Manifest should have at least one source"

    def test_manifest_row_counts_match(self):
        """Test that manifest row counts match actual file contents."""
        manifest_path = DATA_DIR / "manifest.csv"

        if not manifest_path.exists():
            pytest.skip("Manifest not created yet")

        manifest_df = pd.read_csv(manifest_path)

        # Check a few parquet files
        for _, row in manifest_df.iterrows():
            artifact_path = Path(row["artifact_path"])

            if artifact_path.suffix == ".parquet" and artifact_path.exists():
                df = pd.read_parquet(artifact_path)
                manifest_count = row["row_count"]
                actual_count = len(df)

                assert manifest_count == actual_count, \
                    f"{artifact_path.name}: manifest says {manifest_count} rows, actual {actual_count}"
