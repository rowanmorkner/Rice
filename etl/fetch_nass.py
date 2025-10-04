#!/usr/bin/env python
"""
Fetch USDA NASS QuickStats data for California rice yields and prices.

Requires NASS_API_KEY in .env file.
Get a free key at: https://quickstats.nass.usda.gov/api
"""

import logging
import os
from pathlib import Path
from typing import Optional
import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from etl.utils_manifest import append_to_manifest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

NASS_API_KEY = os.getenv("NASS_API_KEY")
NASS_BASE_URL = "http://quickstats.nass.usda.gov/api/api_GET/"
USER_AGENT = "Water-Opt/0.1.0 (Educational/Research)"


def check_api_key() -> bool:
    """Check if NASS API key is configured."""
    if not NASS_API_KEY or NASS_API_KEY == "YOUR_KEY_HERE":
        logger.warning(
            "NASS API key not configured. "
            "Get a free key at https://quickstats.nass.usda.gov/api"
        )
        return False
    return True


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_rice_prices(
    state: str = "CALIFORNIA",
    start_year: int = 2015,
    end_year: Optional[int] = None
) -> Optional[pd.DataFrame]:
    """
    Fetch California rice prices from NASS QuickStats API.

    Args:
        state: State name
        start_year: Start year for data
        end_year: End year for data (None = current year)

    Returns:
        DataFrame with price data
    """
    if not check_api_key():
        logger.error("Cannot fetch NASS data without API key")
        return None

    if end_year is None:
        from datetime import datetime
        end_year = datetime.now().year

    logger.info(f"Fetching rice prices for {state}, {start_year}-{end_year}")

    params = {
        "key": NASS_API_KEY,
        "source_desc": "SURVEY",
        "sector_desc": "CROPS",
        "group_desc": "FIELD CROPS",
        "commodity_desc": "RICE",
        "statisticcat_desc": "PRICE RECEIVED",
        "state_alpha": "CA",
        "agg_level_desc": "STATE",
        "year__GE": start_year,
        "year__LE": end_year,
        "format": "JSON"
    }

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(NASS_BASE_URL, params=params, headers=headers, timeout=60)
        response.raise_for_status()

        data = response.json()

        if "data" not in data:
            logger.warning(f"No data returned from NASS API")
            logger.debug(f"Response: {data}")
            return None

        records = data["data"]
        logger.info(f"Retrieved {len(records)} price records from NASS")

        if not records:
            return None

        df = pd.DataFrame(records)
        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NASS data: {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_rice_yields(
    state: str = "CALIFORNIA",
    start_year: int = 2015,
    end_year: Optional[int] = None
) -> Optional[pd.DataFrame]:
    """
    Fetch California rice yields from NASS QuickStats API.

    Args:
        state: State name
        start_year: Start year for data
        end_year: End year for data (None = current year)

    Returns:
        DataFrame with yield data
    """
    if not check_api_key():
        logger.error("Cannot fetch NASS data without API key")
        return None

    if end_year is None:
        from datetime import datetime
        end_year = datetime.now().year

    logger.info(f"Fetching rice yields for {state}, {start_year}-{end_year}")

    params = {
        "key": NASS_API_KEY,
        "source_desc": "SURVEY",
        "sector_desc": "CROPS",
        "group_desc": "FIELD CROPS",
        "commodity_desc": "RICE",
        "statisticcat_desc": "YIELD",
        "state_alpha": "CA",
        "agg_level_desc": "STATE",
        "year__GE": start_year,
        "year__LE": end_year,
        "format": "JSON"
    }

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(NASS_BASE_URL, params=params, headers=headers, timeout=60)
        response.raise_for_status()

        data = response.json()

        if "data" not in data:
            logger.warning(f"No data returned from NASS API")
            logger.debug(f"Response: {data}")
            return None

        records = data["data"]
        logger.info(f"Retrieved {len(records)} yield records from NASS")

        if not records:
            return None

        df = pd.DataFrame(records)
        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NASS data: {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_rice_by_county(
    start_year: int = 2015,
    end_year: Optional[int] = None
) -> Optional[pd.DataFrame]:
    """
    Fetch California rice data by county from NASS QuickStats API.

    Args:
        start_year: Start year for data
        end_year: End year for data (None = current year)

    Returns:
        DataFrame with county-level data
    """
    if not check_api_key():
        logger.error("Cannot fetch NASS data without API key")
        return None

    if end_year is None:
        from datetime import datetime
        end_year = datetime.now().year

    logger.info(f"Fetching rice data by county, {start_year}-{end_year}")

    # Get production and yield by county
    params = {
        "key": NASS_API_KEY,
        "source_desc": "SURVEY",
        "sector_desc": "CROPS",
        "group_desc": "FIELD CROPS",
        "commodity_desc": "RICE",
        "statisticcat_desc": "YIELD",
        "state_alpha": "CA",
        "agg_level_desc": "COUNTY",
        "year__GE": start_year,
        "year__LE": end_year,
        "format": "JSON"
    }

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(NASS_BASE_URL, params=params, headers=headers, timeout=60)
        response.raise_for_status()

        data = response.json()

        if "data" not in data:
            logger.warning(f"No county data returned from NASS API")
            logger.debug(f"Response: {data}")
            return None

        records = data["data"]
        logger.info(f"Retrieved {len(records)} county records from NASS")

        if not records:
            return None

        df = pd.DataFrame(records)
        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NASS county data: {e}")
        raise


def normalize_nass_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize NASS price data to standard schema.

    Args:
        df: Raw NASS DataFrame

    Returns:
        Normalized DataFrame with columns: year, month, price_usd_cwt, class_desc
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # Extract relevant columns
    df_clean = df[[
        "year", "reference_period_desc", "class_desc", "Value", "unit_desc"
    ]].copy()

    # Clean price values (remove commas, convert to float)
    df_clean["price"] = df_clean["Value"].str.replace(",", "").astype(float)

    # Rename columns
    df_clean = df_clean.rename(columns={
        "reference_period_desc": "period",
        "class_desc": "rice_class"
    })

    # Create date column
    df_clean["year"] = df_clean["year"].astype(int)

    # Extract month from period if available
    df_clean["month"] = df_clean["period"].str.extract(r'(\w+)')[0]

    # Keep relevant columns
    df_out = df_clean[["year", "month", "rice_class", "price", "unit_desc"]].copy()
    df_out = df_out.rename(columns={
        "price": "price_usd_cwt",
        "unit_desc": "unit"
    })

    logger.info(f"Normalized {len(df_out)} price records")
    return df_out


def normalize_nass_yields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize NASS yield data to standard schema.

    Args:
        df: Raw NASS DataFrame

    Returns:
        Normalized DataFrame with columns: year, county, yield_cwt_acre, class_desc
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # Extract relevant columns
    cols_to_keep = ["year", "class_desc", "Value", "unit_desc"]
    if "county_name" in df.columns:
        cols_to_keep.insert(1, "county_name")

    df_clean = df[cols_to_keep].copy()

    # Clean yield values
    df_clean["yield_value"] = df_clean["Value"].str.replace(",", "").astype(float)

    # Rename columns
    rename_map = {
        "class_desc": "rice_class",
        "unit_desc": "unit"
    }
    if "county_name" in df_clean.columns:
        rename_map["county_name"] = "county"

    df_clean = df_clean.rename(columns=rename_map)

    # Keep relevant columns
    out_cols = ["year", "rice_class", "yield_value", "unit"]
    if "county" in df_clean.columns:
        out_cols.insert(1, "county")

    df_out = df_clean[out_cols].copy()
    df_out["year"] = df_out["year"].astype(int)

    # Rename yield_value to yield_cwt_acre if unit is cwt
    df_out = df_out.rename(columns={"yield_value": "yield_cwt_acre"})

    logger.info(f"Normalized {len(df_out)} yield records")
    return df_out


def save_stage_data(
    df_prices: Optional[pd.DataFrame],
    df_yields: Optional[pd.DataFrame],
    df_county: Optional[pd.DataFrame],
    data_dir: Path = Path("data")
) -> list:
    """
    Save NASS data to stage directory.

    Args:
        df_prices: Price DataFrame
        df_yields: Yield DataFrame
        df_county: County-level DataFrame
        data_dir: Root data directory

    Returns:
        List of saved file paths
    """
    stage_dir = data_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []

    # Save prices
    if df_prices is not None and not df_prices.empty:
        output_path = stage_dir / "nass_rice_prices.parquet"
        df_prices.to_parquet(output_path, index=False, engine="pyarrow")
        logger.info(f"Saved {len(df_prices)} price rows to {output_path}")

        append_to_manifest(
            artifact_path=output_path,
            source="NASS",
            artifact_type="parquet",
            notes="California rice prices from USDA NASS QuickStats",
            data_dir=data_dir
        )
        saved_files.append(output_path)

    # Save yields
    if df_yields is not None and not df_yields.empty:
        output_path = stage_dir / "nass_rice_yields.parquet"
        df_yields.to_parquet(output_path, index=False, engine="pyarrow")
        logger.info(f"Saved {len(df_yields)} yield rows to {output_path}")

        append_to_manifest(
            artifact_path=output_path,
            source="NASS",
            artifact_type="parquet",
            notes="California rice yields from USDA NASS QuickStats",
            data_dir=data_dir
        )
        saved_files.append(output_path)

    # Save county data
    if df_county is not None and not df_county.empty:
        output_path = stage_dir / "nass_rice_county.parquet"
        df_county.to_parquet(output_path, index=False, engine="pyarrow")
        logger.info(f"Saved {len(df_county)} county rows to {output_path}")

        append_to_manifest(
            artifact_path=output_path,
            source="NASS",
            artifact_type="parquet",
            notes="California rice data by county from USDA NASS QuickStats",
            data_dir=data_dir
        )
        saved_files.append(output_path)

    return saved_files


def main():
    """Main execution: fetch NASS rice data for California."""
    if not check_api_key():
        logger.error(
            "NASS API key not found in .env file. "
            "Get a free key at https://quickstats.nass.usda.gov/api "
            "and add it to .env as NASS_API_KEY=your_key_here"
        )
        return

    logger.info("Starting NASS data fetch")
    logger.info(
        "NOTE: NASS QuickStats API can be slow and may timeout. "
        "This is a known issue with the NASS service. "
        "If timeouts occur, the fetcher will gracefully skip NASS data."
    )

    # Fetch data with error handling
    df_prices_raw = None
    df_yields_raw = None
    df_county_raw = None

    try:
        df_prices_raw = fetch_rice_prices()
    except Exception as e:
        logger.error(f"Failed to fetch price data: {e}")
        logger.warning("Continuing without price data...")

    try:
        df_yields_raw = fetch_rice_yields()
    except Exception as e:
        logger.error(f"Failed to fetch yield data: {e}")
        logger.warning("Continuing without yield data...")

    try:
        df_county_raw = fetch_rice_by_county()
    except Exception as e:
        logger.error(f"Failed to fetch county data: {e}")
        logger.warning("Continuing without county data...")

    # Normalize data
    df_prices = normalize_nass_prices(df_prices_raw) if df_prices_raw is not None else None
    df_yields = normalize_nass_yields(df_yields_raw) if df_yields_raw is not None else None
    df_county = normalize_nass_yields(df_county_raw) if df_county_raw is not None else None

    # Save stage data
    saved_files = save_stage_data(df_prices, df_yields, df_county)

    if saved_files:
        logger.info(f"NASS fetch complete: {len(saved_files)} files saved")
        for path in saved_files:
            logger.info(f"  - {path}")
    else:
        logger.warning(
            "No NASS data saved. "
            "This may be due to NASS API timeouts or service issues. "
            "The NASS QuickStats API is known to have performance problems. "
            "Consider using cached data or alternative sources for production use."
        )


if __name__ == "__main__":
    main()
