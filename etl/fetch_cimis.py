#!/usr/bin/env python
"""
Fetch CIMIS (California Irrigation Management Information System) ETo data.

Pulls daily reference evapotranspiration (ETo) for stations near Sacramento Valley
rice-growing regions (Gridley, Richvale, Sutter).
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from etl.utils_manifest import append_to_manifest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# CIMIS API configuration
CIMIS_BASE_URL = "http://et.water.ca.gov/api/data"
CIMIS_STATION_URL = "http://et.water.ca.gov/api/station"
USER_AGENT = "Water-Opt/0.1.0 (Educational/Research)"

# Sacramento Valley rice region stations (near Gridley, Richvale, Sutter)
# Station IDs for the region (will verify availability)
SACRAMENTO_VALLEY_STATIONS = [
    "145",  # Colusa
    "131",  # Durham
    "146",  # Nicolaus
    "194",  # Yuba City
    "166",  # Rough & Ready
]


def get_api_key() -> Optional[str]:
    """
    Get CIMIS API key from environment.

    Returns:
        API key or None if not set
    """
    api_key = os.getenv("CIMIS_APP_KEY")
    if not api_key:
        logger.warning("CIMIS_APP_KEY not found in environment")
        logger.warning("Set CIMIS_APP_KEY in .env to enable CIMIS data fetching")
        logger.info("Get a key at: http://et.water.ca.gov/Home/Register")
    return api_key


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_station_info(api_key: str, station_ids: List[str]) -> pd.DataFrame:
    """
    Fetch station metadata from CIMIS API.

    Args:
        api_key: CIMIS API key
        station_ids: List of station IDs

    Returns:
        DataFrame with station info (station_id, name, latitude, longitude)
    """
    headers = {"User-Agent": USER_AGENT}
    params = {
        "appKey": api_key,
        "targets": ",".join(station_ids)
    }

    logger.info(f"Fetching metadata for {len(station_ids)} CIMIS stations")

    try:
        response = requests.get(CIMIS_STATION_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Parse station data
        stations = []
        if "Stations" in data:
            for station in data["Stations"]:
                stations.append({
                    "station_id": station.get("StationNbr"),
                    "name": station.get("Name"),
                    "latitude": station.get("Latitude"),
                    "longitude": station.get("Longitude"),
                    "county": station.get("County"),
                    "is_active": station.get("IsActive") == "True"
                })

        df_stations = pd.DataFrame(stations)
        logger.info(f"Retrieved metadata for {len(df_stations)} stations")

        return df_stations

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch station info: {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_daily_eto(
    api_key: str,
    station_ids: List[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    Fetch daily ETo data from CIMIS API.

    Args:
        api_key: CIMIS API key
        station_ids: List of station IDs
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame with daily ETo data
    """
    headers = {"User-Agent": USER_AGENT}
    params = {
        "appKey": api_key,
        "targets": ",".join(station_ids),
        "startDate": start_date,
        "endDate": end_date,
        "dataItems": "day-eto",  # Reference evapotranspiration
        "unitOfMeasure": "E"  # English units (inches)
    }

    logger.info(f"Fetching ETo data from {start_date} to {end_date}")
    logger.info(f"Stations: {', '.join(station_ids)}")

    try:
        response = requests.get(CIMIS_BASE_URL, headers=headers, params=params, timeout=60)

        # Check for error response before raising
        if response.status_code != 200:
            logger.error(f"API returned status {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")

        response.raise_for_status()

        data = response.json()

        # Parse ETo records
        records = []
        if "Data" in data and "Providers" in data["Data"]:
            for provider in data["Data"]["Providers"]:
                for record in provider.get("Records", []):
                    date_str = record.get("Date")
                    station = record.get("Station")

                    # Extract ETo value
                    eto_value = None
                    if "DayEto" in record:
                        eto_data = record["DayEto"]
                        if eto_data.get("Value") not in [None, "", "M"]:
                            try:
                                eto_value = float(eto_data["Value"])
                            except (ValueError, TypeError):
                                pass

                    if date_str and station and eto_value is not None:
                        records.append({
                            "date": date_str,
                            "station": station,
                            "eto_in": eto_value
                        })

        df = pd.DataFrame(records)

        if not df.empty:
            # Convert date to datetime
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values(["station", "date"]).reset_index(drop=True)

        logger.info(f"Retrieved {len(df):,} ETo records")

        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch ETo data: {e}")
        raise


def normalize_eto_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize CIMIS ETo data.

    Args:
        df: Raw ETo DataFrame

    Returns:
        Normalized DataFrame
    """
    if df.empty:
        return df

    # Ensure proper data types
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["station"] = df["station"].astype(str)
    df["eto_in"] = pd.to_numeric(df["eto_in"], errors="coerce")

    # Remove invalid records
    df = df.dropna(subset=["eto_in"])

    # Add year and month for aggregation
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    logger.info(f"Normalized {len(df):,} ETo records")
    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    logger.info(f"Stations: {sorted(df['station'].unique())}")

    return df


def save_eto_data(df: pd.DataFrame, data_dir: Path = Path("data")) -> Path:
    """
    Save ETo data to parquet file.

    Args:
        df: ETo DataFrame
        data_dir: Root data directory

    Returns:
        Path to saved parquet file
    """
    stage_dir = data_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)

    output_path = stage_dir / "cimis_daily.parquet"

    # Select final columns
    df_output = df[["date", "station", "eto_in"]].copy()

    df_output.to_parquet(output_path, index=False, engine="pyarrow")
    logger.info(f"Saved {len(df_output):,} records to {output_path}")

    # Update manifest
    append_to_manifest(
        artifact_path=output_path,
        source="CIMIS",
        artifact_type="parquet",
        notes=f"Daily reference ET from {len(df['station'].unique())} Sacramento Valley stations",
        data_dir=data_dir
    )

    return output_path


def main():
    """Main execution: fetch CIMIS ETo data."""
    data_dir = Path("data")

    # Check for API key
    api_key = get_api_key()
    if not api_key:
        logger.warning("Cannot fetch CIMIS data without API key")
        logger.info("Exiting gracefully")
        return

    # Date range: last year only (CIMIS API may have limits on historical data)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    try:
        # Fetch station info
        logger.info("Step 1: Fetching station metadata")
        df_stations = fetch_station_info(api_key, SACRAMENTO_VALLEY_STATIONS)

        # Filter for requested Sacramento Valley stations only
        active_stations = df_stations[
            (df_stations["is_active"] == True) &
            (df_stations["station_id"].isin(SACRAMENTO_VALLEY_STATIONS))
        ]["station_id"].tolist()

        if not active_stations:
            logger.warning("No active stations found in requested list, using original list")
            active_stations = SACRAMENTO_VALLEY_STATIONS

        logger.info(f"Using {len(active_stations)} Sacramento Valley stations: {', '.join(active_stations)}")

        # Fetch ETo data
        logger.info("Step 2: Fetching daily ETo data")
        df_eto = fetch_daily_eto(api_key, active_stations, start_date_str, end_date_str)

        if df_eto.empty:
            logger.warning("No ETo data retrieved")
            return

        # Normalize data
        logger.info("Step 3: Normalizing ETo data")
        df_normalized = normalize_eto_data(df_eto)

        # Save to parquet
        logger.info("Step 4: Saving to parquet")
        output_path = save_eto_data(df_normalized, data_dir)

        # Summary statistics
        logger.info("\n=== CIMIS Data Summary ===")
        logger.info(f"Records: {len(df_normalized):,}")
        logger.info(f"Date range: {df_normalized['date'].min()} to {df_normalized['date'].max()}")
        logger.info(f"Stations: {', '.join(sorted(df_normalized['station'].unique()))}")
        logger.info(f"Mean daily ETo: {df_normalized['eto_in'].mean():.3f} inches")
        logger.info(f"Output: {output_path}")

        logger.info("\nCIMIS fetch complete ✓")

    except Exception as e:
        logger.error(f"CIMIS fetch failed: {e}")
        logger.warning("Continuing without CIMIS data...")
        raise


if __name__ == "__main__":
    main()
