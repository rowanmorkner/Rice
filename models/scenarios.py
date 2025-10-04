"""
Scenario modeling for hydrology and market price bands.

Builds dry/median/wet hydrology scenarios and price percentile bands
for decision support.
"""

from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np


def build_hydro_scenarios(
    awdb_df: Optional[pd.DataFrame] = None,
    b120_df: Optional[pd.DataFrame] = None,
    data_dir: Path = Path("data")
) -> pd.DataFrame:
    """
    Build monthly dry/median/wet hydrology scenarios.

    Combines AWDB historical SWE percentiles with B120 forecast data to create
    water supply scenarios for decision modeling.

    Args:
        awdb_df: DataFrame with AWDB SWE data (date, station_id, wteq_mm)
                 If None, loads from data/stage/awdb_swe_daily.parquet
        b120_df: DataFrame with B120 forecast data (basin, median, p10, p90)
                 If None, loads from data/stage/b120_forecast.parquet
        data_dir: Root data directory

    Returns:
        DataFrame with columns:
            month: Month number (1-12)
            scenario: 'dry', 'median', or 'wet'
            allocation_index: Simplified allocation multiplier (0-1)
            swe_percentile: SWE percentile (p10, p50, p90)
            description: Human-readable scenario description

    Notes:
        - Allocation index is a simplified proxy for water availability
        - Dry = p10 (10th percentile, drought conditions)
        - Median = p50 (50th percentile, normal conditions)
        - Wet = p90 (90th percentile, abundant water)
        - TODO: Refine allocation logic with actual water district allocations
    """
    # Load AWDB data if not provided
    if awdb_df is None:
        awdb_path = data_dir / "mart" / "hydro_scenarios.parquet"
        if awdb_path.exists():
            awdb_df = pd.read_parquet(awdb_path)
        else:
            # Create default scenarios if no data available
            return _create_default_hydro_scenarios()

    # Check if awdb_df is already the hydro_scenarios output
    if 'scenario' in awdb_df.columns and 'allocation_index' in awdb_df.columns:
        # Already processed, return as-is
        return awdb_df

    # If raw AWDB data, compute percentiles
    if 'date' in awdb_df.columns and 'wteq_mm' in awdb_df.columns:
        awdb_df = awdb_df.copy()
        awdb_df['date'] = pd.to_datetime(awdb_df['date'])
        awdb_df['month'] = awdb_df['date'].dt.month

        # Calculate monthly percentiles across all stations
        monthly_percentiles = awdb_df.groupby('month')['wteq_mm'].quantile([0.1, 0.5, 0.9]).unstack()
        monthly_percentiles.columns = ['p10', 'p50', 'p90']
        monthly_percentiles = monthly_percentiles.reset_index()

        # Build scenarios
        scenarios = []

        for _, row in monthly_percentiles.iterrows():
            month = row['month']

            # Dry scenario (p10)
            scenarios.append({
                'month': month,
                'scenario': 'dry',
                'allocation_index': 0.4,  # 40% allocation in drought
                'swe_percentile': row['p10'],
                'description': f'Drought conditions (p10 SWE)'
            })

            # Median scenario (p50)
            scenarios.append({
                'month': month,
                'scenario': 'median',
                'allocation_index': 0.75,  # 75% allocation in normal year
                'swe_percentile': row['p50'],
                'description': f'Normal conditions (p50 SWE)'
            })

            # Wet scenario (p90)
            scenarios.append({
                'month': month,
                'scenario': 'wet',
                'allocation_index': 1.0,  # 100% allocation in wet year
                'swe_percentile': row['p90'],
                'description': f'Abundant water (p90 SWE)'
            })

        df_scenarios = pd.DataFrame(scenarios)
        return df_scenarios

    else:
        # Unknown format, return defaults
        return _create_default_hydro_scenarios()


def _create_default_hydro_scenarios() -> pd.DataFrame:
    """
    Create default hydrology scenarios when no data is available.

    Returns:
        DataFrame with default monthly scenarios
    """
    scenarios = []

    for month in range(1, 13):
        scenarios.extend([
            {
                'month': month,
                'scenario': 'dry',
                'allocation_index': 0.4,
                'swe_percentile': 0.0,
                'description': 'Drought conditions (default)'
            },
            {
                'month': month,
                'scenario': 'median',
                'allocation_index': 0.75,
                'swe_percentile': 0.0,
                'description': 'Normal conditions (default)'
            },
            {
                'month': month,
                'scenario': 'wet',
                'allocation_index': 1.0,
                'swe_percentile': 0.0,
                'description': 'Abundant water (default)'
            }
        ])

    return pd.DataFrame(scenarios)


def build_price_bands(
    ers_prices_df: Optional[pd.DataFrame] = None,
    data_dir: Path = Path("data"),
    window_size: int = 12  # Rolling window in months
) -> pd.DataFrame:
    """
    Build rolling price percentile bands (p10, median, p90).

    Creates price bands for scenario analysis using historical rice prices.

    Args:
        ers_prices_df: DataFrame with ERS price data (date, price_usd_cwt)
                       If None, loads from data/stage/ers_prices.parquet
        data_dir: Root data directory
        window_size: Number of periods for rolling window (default 12)

    Returns:
        DataFrame with columns:
            date: Date
            price_usd_cwt: Current price
            p10: 10th percentile (low price scenario)
            median: 50th percentile (medium price scenario)
            p90: 90th percentile (high price scenario)
            band_width: Spread between p10 and p90

    Notes:
        - Uses rolling window to capture recent price trends
        - Band width indicates price volatility
        - For stub ERS data (2 rows), creates expanded bands
    """
    # Load ERS data if not provided
    if ers_prices_df is None:
        ers_path = data_dir / "stage" / "ers_prices.parquet"
        if ers_path.exists():
            ers_prices_df = pd.read_parquet(ers_path)
        else:
            # Create default price bands if no data available
            return _create_default_price_bands()

    if ers_prices_df.empty:
        return _create_default_price_bands()

    # Ensure date column is datetime
    if 'date' in ers_prices_df.columns:
        ers_prices_df = ers_prices_df.copy()
        ers_prices_df['date'] = pd.to_datetime(ers_prices_df['date'])
        ers_prices_df = ers_prices_df.sort_values('date').reset_index(drop=True)

    # Handle stub data (very few rows)
    if len(ers_prices_df) < window_size:
        # Create synthetic bands based on mean price
        mean_price = ers_prices_df['price_usd_cwt'].mean()
        std_price = ers_prices_df['price_usd_cwt'].std() if len(ers_prices_df) > 1 else mean_price * 0.15

        # Use standard deviation to create reasonable bands
        # Typical rice price volatility is ~15-20%
        if std_price == 0 or pd.isna(std_price):
            std_price = mean_price * 0.15

        result_df = ers_prices_df.copy()
        result_df['p10'] = mean_price - 1.28 * std_price  # ~10th percentile
        result_df['median'] = mean_price
        result_df['p90'] = mean_price + 1.28 * std_price  # ~90th percentile
        result_df['band_width'] = result_df['p90'] - result_df['p10']

        return result_df

    # Calculate rolling percentiles for real data
    result_df = ers_prices_df.copy()

    result_df['p10'] = result_df['price_usd_cwt'].rolling(
        window=window_size, min_periods=1
    ).quantile(0.1)

    result_df['median'] = result_df['price_usd_cwt'].rolling(
        window=window_size, min_periods=1
    ).quantile(0.5)

    result_df['p90'] = result_df['price_usd_cwt'].rolling(
        window=window_size, min_periods=1
    ).quantile(0.9)

    result_df['band_width'] = result_df['p90'] - result_df['p10']

    return result_df


def _create_default_price_bands() -> pd.DataFrame:
    """
    Create default price bands when no data is available.

    Returns:
        DataFrame with default price band (CA rice averages)
    """
    return pd.DataFrame([{
        'date': pd.Timestamp('2025-01-01'),
        'price_usd_cwt': 19.0,  # CA medium-grain typical
        'p10': 16.5,  # Low price scenario
        'median': 19.0,  # Medium price scenario
        'p90': 21.5,  # High price scenario
        'band_width': 5.0
    }])


def get_scenario_summary(
    hydro_scenarios_df: pd.DataFrame,
    price_bands_df: pd.DataFrame,
    target_month: int = 5  # May (planting decision time)
) -> dict:
    """
    Get scenario summary for decision time.

    Args:
        hydro_scenarios_df: Hydrology scenarios DataFrame
        price_bands_df: Price bands DataFrame
        target_month: Month for decision (default May = 5)

    Returns:
        Dict with scenario combinations and recommendations
    """
    # Filter hydro scenarios for target month
    hydro_month = hydro_scenarios_df[
        hydro_scenarios_df['month'] == target_month
    ]

    # Get latest price bands
    latest_prices = price_bands_df.iloc[-1] if not price_bands_df.empty else None

    summary = {
        'decision_month': target_month,
        'hydro_scenarios': hydro_month.to_dict('records') if not hydro_month.empty else [],
        'price_scenarios': {
            'low': latest_prices['p10'] if latest_prices is not None else 16.5,
            'medium': latest_prices['median'] if latest_prices is not None else 19.0,
            'high': latest_prices['p90'] if latest_prices is not None else 21.5
        },
        'scenario_matrix': []
    }

    # Create scenario matrix (hydro × price)
    if not hydro_month.empty and latest_prices is not None:
        for _, hydro in hydro_month.iterrows():
            for price_scenario, price in summary['price_scenarios'].items():
                summary['scenario_matrix'].append({
                    'hydro': hydro['scenario'],
                    'price': price_scenario,
                    'allocation_index': hydro['allocation_index'],
                    'price_usd_cwt': price,
                    'description': f"{hydro['scenario'].capitalize()} water, {price_scenario} price"
                })

    return summary
