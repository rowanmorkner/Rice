#!/usr/bin/env python
"""
Fetch USDA AMS Rice Market News data for California rice prices.

This provides weekly actual market prices for California medium-grain and
short-grain rice, which is much better than the ERS stub data.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from etl.utils_manifest import append_to_manifest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AMS MyMarketNews API
AMS_BASE_URL = "https://marsapi.ams.usda.gov/services/v1.2/reports"
USER_AGENT = "Water-Opt/0.1.0 (Educational/Research)"

# Rice market report slugs
RICE_REPORT_SLUGS = [
    "2795",  # National Weekly Rice Market Summary
    # Add more specific California reports as discovered
]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_ams_rice_reports(
    days_back: int = 365
) -> pd.DataFrame:
    """
    Fetch rice market reports from AMS MyMarketNews API.

    Args:
        days_back: Number of days of history to fetch

    Returns:
        DataFrame with date, report_type, price_data

    Note:
        AMS API returns unstructured text reports. Parsing requires
        pattern matching on report text.
    """
    headers = {"User-Agent": USER_AGENT}

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    params = {
        "q": "rice california",  # Search for California rice reports
        "publishedDateFrom": start_date.strftime("%m/%d/%Y"),
        "publishedDateTo": end_date.strftime("%m/%d/%Y")
    }

    logger.info(f"Fetching AMS rice market reports from {start_date.date()} to {end_date.date()}")

    try:
        response = requests.get(AMS_BASE_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        reports = []
        for result in data.get("results", []):
            reports.append({
                "date": result.get("published_date"),
                "report_title": result.get("slug_name"),
                "report_id": result.get("slug_id"),
                "report_text": result.get("report_text", "")
            })

        df = pd.DataFrame(reports)
        logger.info(f"Retrieved {len(df)} rice market reports")

        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch AMS reports: {e}")
        raise


def parse_california_rice_prices(df_reports: pd.DataFrame) -> pd.DataFrame:
    """
    Parse California rice prices from AMS report text.

    This uses pattern matching to extract prices from unstructured reports.

    Args:
        df_reports: DataFrame with report text

    Returns:
        DataFrame with parsed price data
    """
    import re

    prices = []

    for _, row in df_reports.iterrows():
        text = row['report_text'].lower()
        date = row['date']

        # Pattern matching for California medium-grain
        # Example: "California medium-grain #2, fob mill: $18.50-19.00/cwt"
        medium_pattern = r'california\s+medium[- ]grain.*?(\$?\d+\.?\d*)\s*[-to]\s*(\$?\d+\.?\d*).*?cwt'
        short_pattern = r'california\s+short[- ]grain.*?(\$?\d+\.?\d*)\s*[-to]\s*(\$?\d+\.?\d*).*?cwt'

        medium_match = re.search(medium_pattern, text)
        if medium_match:
            low = float(medium_match.group(1).replace('$', ''))
            high = float(medium_match.group(2).replace('$', ''))
            avg = (low + high) / 2

            prices.append({
                'date': date,
                'variety': 'medium-grain',
                'price_low': low,
                'price_high': high,
                'price_avg': avg,
                'unit': 'usd_per_cwt',
                'source': 'AMS Market News'
            })

        short_match = re.search(short_pattern, text)
        if short_match:
            low = float(short_match.group(1).replace('$', ''))
            high = float(short_match.group(2).replace('$', ''))
            avg = (low + high) / 2

            prices.append({
                'date': date,
                'variety': 'short-grain',
                'price_low': low,
                'price_high': high,
                'price_avg': avg,
                'unit': 'usd_per_cwt',
                'source': 'AMS Market News'
            })

    df_prices = pd.DataFrame(prices)

    if not df_prices.empty:
        df_prices['date'] = pd.to_datetime(df_prices['date'])
        df_prices = df_prices.sort_values('date').reset_index(drop=True)
        logger.info(f"Parsed {len(df_prices)} price records from reports")
    else:
        logger.warning("No prices could be parsed from reports")

    return df_prices


def save_ams_prices(df: pd.DataFrame, data_dir: Path = Path("data")) -> Path:
    """
    Save AMS rice prices to parquet.

    Args:
        df: Price DataFrame
        data_dir: Root data directory

    Returns:
        Path to saved parquet file
    """
    stage_dir = data_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)

    output_path = stage_dir / "ams_rice_prices.parquet"

    # Use average price for main price column
    df_output = df.copy()
    df_output['price_usd_cwt'] = df_output['price_avg']

    df_output.to_parquet(output_path, index=False, engine="pyarrow")
    logger.info(f"Saved {len(df_output)} records to {output_path}")

    # Update manifest
    append_to_manifest(
        artifact_path=output_path,
        source="AMS_Rice_Market_News",
        artifact_type="parquet",
        notes=f"Weekly California rice prices from USDA AMS Market News",
        data_dir=data_dir
    )

    return output_path


def main():
    """Main execution: fetch AMS rice market data."""
    data_dir = Path("data")

    try:
        # Fetch reports
        logger.info("Step 1: Fetching AMS rice market reports")
        df_reports = fetch_ams_rice_reports(days_back=365)

        if df_reports.empty:
            logger.warning("No reports retrieved")
            logger.info("Note: AMS API may require different search terms or report IDs")
            logger.info("Visit https://www.ams.usda.gov/market-news/rice-reports for report IDs")
            return

        # Parse prices
        logger.info("Step 2: Parsing California rice prices")
        df_prices = parse_california_rice_prices(df_reports)

        if df_prices.empty:
            logger.warning("No prices could be parsed")
            logger.info("Report text may need different parsing patterns")
            logger.info("Check sample reports to adjust regex patterns")
            return

        # Save to parquet
        logger.info("Step 3: Saving to parquet")
        output_path = save_ams_prices(df_prices, data_dir)

        # Summary
        logger.info("\n=== AMS Rice Prices Summary ===")
        logger.info(f"Records: {len(df_prices)}")
        logger.info(f"Date range: {df_prices['date'].min()} to {df_prices['date'].max()}")
        logger.info(f"Varieties: {df_prices['variety'].unique().tolist()}")
        logger.info(f"Price range: ${df_prices['price_avg'].min():.2f} - ${df_prices['price_avg'].max():.2f}/cwt")
        logger.info(f"Output: {output_path}")

        logger.info("\nAMS fetch complete ✓")

    except Exception as e:
        logger.error(f"AMS fetch failed: {e}")
        logger.info("\nAlternatives:")
        logger.info("1. Use NASS API when it recovers")
        logger.info("2. Manually download reports from https://www.ams.usda.gov/market-news/rice-reports")
        logger.info("3. Use CME rough rice futures as proxy")
        raise


if __name__ == "__main__":
    main()
