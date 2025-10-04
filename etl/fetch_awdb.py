#!/usr/bin/env python
"""
Fetch SNOTEL snow water equivalent (SWE) data from NRCS AWDB API.

Retrieves daily SWE measurements from key Sierra Nevada stations since 2015.
Writes to stage/awdb_swe_daily.parquet and derives mart/hydro_scenarios.parquet.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from etl.utils_manifest import append_to_manifest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Key Sierra Nevada SNOTEL stations relevant to Central Valley water supply
SIERRA_STATIONS = [
    "428",   # CSS Lab (Nevada County)
    "463",   # Echo Peak (El Dorado County)
    "473",   # Fallen Leaf (El Dorado County)
    "508",   # Hagans Meadow (El Dorado County)
    "518",   # Heavenly Valley (El Dorado County)
    "540",   # Independence Lake (Nevada County)
    "724",   # Poison Flat (Mono County)
    "778",   # Rubicon #2 (El Dorado County)
    "1067",  # Carson Pass (Alpine County)
    "356",   # Blue Lakes (Alpine County)
    "1051",  # Burnside Lake (Alpine County)
    "462",   # Ebbetts Pass (Alpine County)
]

AWDB_BASE_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data"
USER_AGENT = "Water-Opt/0.1.0 (Educational/Research)"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_station_data(
    station_id: str,
    start_date: str,
    end_date: str,
    element: str = "WTEQ"
) -> Optional[pd.DataFrame]:
    """
    Fetch daily data for a single SNOTEL station.

    Args:
        station_id: AWDB station triplet (e.g., "305:CA:SNTL")
        start_date: ISO format date string (YYYY-MM-DD)
        end_date: ISO format date string
        element: Data element code (WTEQ = snow water equivalent)

    Returns:
        DataFrame with columns: date, station_id, wteq_mm
    """
    # Construct full station triplet if not provided
    if ":" not in station_id:
        station_triplet = f"{station_id}:CA:SNTL"
    else:
        station_triplet = station_id

    url = f"{AWDB_BASE_URL}"

    params = {
        "stationTriplets": station_triplet,
        "elements": element,
        "duration": "DAILY",
        "beginDate": start_date,
        "endDate": end_date
    }

    headers = {"User-Agent": USER_AGENT}

    logger.info(f"Fetching {element} for station {station_triplet} ({start_date} to {end_date})")

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data:
            logger.warning(f"No data returned for station {station_triplet}")
            return None

        # Parse response structure
        records = []
        for station_data in data:
            station_id_short = station_data.get("stationTriplet", "").split(":")[0]

            # Navigate through the nested 'data' array
            for data_obj in station_data.get("data", []):
                for value_entry in data_obj.get("values", []):
                    date_str = value_entry.get("date")
                    value = value_entry.get("value")

                    if date_str and value is not None:
                        records.append({
                            "date": pd.to_datetime(date_str).date(),
                            "station_id": station_id_short,
                            "wteq_mm": float(value) * 25.4  # Convert inches to mm
                        })

        if not records:
            logger.warning(f"No valid records parsed for station {station_triplet}")
            return None

        df = pd.DataFrame(records)
        logger.info(f"Retrieved {len(df)} records for station {station_id_short}")
        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for station {station_triplet}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing station {station_triplet}: {e}")
        return None


def fetch_all_stations(
    station_ids: List[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    Fetch data for multiple stations and combine into single DataFrame.

    Args:
        station_ids: List of station IDs
        start_date: ISO format date string
        end_date: ISO format date string

    Returns:
        Combined DataFrame with all station data
    """
    all_data = []

    for station_id in station_ids:
        df = fetch_station_data(station_id, start_date, end_date)
        if df is not None and not df.empty:
            all_data.append(df)

    if not all_data:
        logger.error("No data retrieved from any station")
        return pd.DataFrame()

    df_combined = pd.concat(all_data, ignore_index=True)
    df_combined = df_combined.sort_values(["date", "station_id"]).reset_index(drop=True)

    logger.info(f"Combined data: {len(df_combined)} total records from {len(all_data)} stations")
    return df_combined


def save_stage_data(df: pd.DataFrame, data_dir: Path = Path("data")) -> Path:
    """
    Save normalized daily SWE data to stage directory.

    Args:
        df: DataFrame with columns date, station_id, wteq_mm
        data_dir: Root data directory

    Returns:
        Path to saved parquet file
    """
    stage_dir = data_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)

    output_path = stage_dir / "awdb_swe_daily.parquet"

    # Ensure correct dtypes
    df["date"] = pd.to_datetime(df["date"])
    df["station_id"] = df["station_id"].astype(str)
    df["wteq_mm"] = df["wteq_mm"].astype(float)

    df.to_parquet(output_path, index=False, engine="pyarrow")
    logger.info(f"Saved {len(df)} rows to {output_path}")

    # Update manifest
    append_to_manifest(
        artifact_path=output_path,
        source="AWDB",
        artifact_type="parquet",
        notes=f"Daily SWE from {len(df['station_id'].unique())} Sierra SNOTEL stations",
        data_dir=data_dir
    )

    return output_path


def derive_hydro_scenarios(df: pd.DataFrame, data_dir: Path = Path("data")) -> Path:
    """
    Derive monthly hydrology scenarios (dry/median/wet) from daily SWE data.

    Computes 10th, 50th, 90th percentiles of monthly SWE across all stations.

    Args:
        df: Daily SWE DataFrame
        data_dir: Root data directory

    Returns:
        Path to saved scenarios parquet file
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Compute monthly percentiles across all stations and years
    monthly_stats = (
        df.groupby(["month"])["wteq_mm"]
        .quantile([0.1, 0.5, 0.9])
        .unstack()
        .reset_index()
    )

    monthly_stats.columns = ["month", "p10_dry_mm", "p50_median_mm", "p90_wet_mm"]
    monthly_stats["scenario_type"] = "historical_percentile"

    mart_dir = data_dir / "mart"
    mart_dir.mkdir(parents=True, exist_ok=True)

    output_path = mart_dir / "hydro_scenarios.parquet"
    monthly_stats.to_parquet(output_path, index=False, engine="pyarrow")

    logger.info(f"Saved hydrology scenarios to {output_path}")

    # Update manifest
    append_to_manifest(
        artifact_path=output_path,
        source="AWDB",
        artifact_type="parquet",
        notes="Monthly dry/median/wet SWE percentiles for scenario modeling",
        data_dir=data_dir
    )

    return output_path


def main():
    """Main execution: fetch AWDB data and derive scenarios."""
    # Fetch data from 2015 to present
    end_date = datetime.now().date()
    start_date = datetime(2015, 1, 1).date()

    logger.info(f"Fetching AWDB data from {start_date} to {end_date}")
    logger.info(f"Stations: {len(SIERRA_STATIONS)} Sierra Nevada SNOTEL sites")

    # Fetch all station data
    df = fetch_all_stations(
        station_ids=SIERRA_STATIONS,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )

    if df.empty:
        logger.error("No data retrieved. Exiting.")
        return

    # Save stage data
    stage_path = save_stage_data(df)
    logger.info(f"Stage data saved: {stage_path}")

    # Derive scenarios
    scenarios_path = derive_hydro_scenarios(df)
    logger.info(f"Hydro scenarios saved: {scenarios_path}")

    logger.info("AWDB fetch complete")


if __name__ == "__main__":
    main()
