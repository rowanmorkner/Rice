#!/usr/bin/env python
"""
Fetch CA DWR Statewide Crop Mapping data for rice polygons.

Downloads 2022 crop mapping shapefile and extracts rice polygons
for Sacramento Valley counties (Butte, Glenn, Colusa, Sutter, Yuba).
"""

import logging
import zipfile
from pathlib import Path
from typing import Optional
import pandas as pd
import geopandas as gpd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from etl.utils_manifest import append_to_manifest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sacramento Valley counties for rice production
SACRAMENTO_VALLEY_COUNTIES = ["Butte", "Glenn", "Colusa", "Sutter", "Yuba"]

# DWR Crop Mapping URLs
DWR_SHAPEFILE_URL = "https://data.cnra.ca.gov/dataset/6c3d65e3-35bb-49e1-a51e-49d5a2cf09a9/resource/b92e0daf-6e2e-4b5c-a112-09474138d1cd/download/i15_crop_mapping_2022_shp.zip"
USER_AGENT = "Water-Opt/0.1.0 (Educational/Research)"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def download_shapefile(url: str, output_dir: Path) -> Path:
    """
    Download DWR crop mapping shapefile.

    Args:
        url: Shapefile ZIP URL
        output_dir: Directory to save file

    Returns:
        Path to downloaded ZIP file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = "i15_crop_mapping_2022.zip"
    output_path = output_dir / filename

    # Check if already downloaded
    if output_path.exists():
        logger.info(f"Shapefile already downloaded: {output_path}")
        return output_path

    logger.info(f"Downloading shapefile from {url}")
    logger.info("Note: This is a large file (~500 MB), download may take several minutes")

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=300, stream=True)
        response.raise_for_status()

        # Download with progress
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0 and downloaded % (10 * 1024 * 1024) == 0:  # Log every 10 MB
                    progress = (downloaded / total_size) * 100
                    logger.info(f"Downloaded {downloaded / 1024 / 1024:.1f} MB ({progress:.1f}%)")

        logger.info(f"Downloaded {output_path.stat().st_size / 1024 / 1024:.1f} MB")
        return output_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download shapefile: {e}")
        raise


def extract_shapefile(zip_path: Path, extract_dir: Path) -> Path:
    """
    Extract shapefile from ZIP archive.

    Args:
        zip_path: Path to ZIP file
        extract_dir: Directory to extract to

    Returns:
        Path to extracted shapefile (.shp)
    """
    extract_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Extracting {zip_path.name} to {extract_dir}")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    # Find the .shp file
    shp_files = list(extract_dir.glob("**/*.shp"))

    if not shp_files:
        raise FileNotFoundError(f"No .shp file found in {extract_dir}")

    shp_path = shp_files[0]
    logger.info(f"Found shapefile: {shp_path.name}")
    return shp_path


def load_and_filter_rice(
    shp_path: Path,
    counties: list = SACRAMENTO_VALLEY_COUNTIES
) -> gpd.GeoDataFrame:
    """
    Load shapefile and filter for rice in specified counties.

    Args:
        shp_path: Path to shapefile
        counties: List of county names to filter

    Returns:
        GeoDataFrame with rice polygons
    """
    logger.info(f"Loading shapefile: {shp_path.name}")
    logger.info("Note: Loading large shapefile may take several minutes")

    gdf = gpd.read_file(shp_path)
    logger.info(f"Loaded {len(gdf):,} total polygons")

    # Inspect columns
    logger.info(f"Columns: {list(gdf.columns)}")

    # Filter for rice
    # DWR uses CLASS1/CLASS2 with codes: R = Rice, G = Grain, F = Field crops, etc.
    # Rice is typically in CLASS2='R'

    county_col = None
    for col in gdf.columns:
        col_lower = col.lower()
        if 'county' in col_lower:
            county_col = col
            logger.info(f"Found county column: {col}")
            break

    if county_col is None:
        logger.warning("Could not find county column, will not filter by county")

    # Filter for rice using CLASS2='R'
    if 'CLASS2' in gdf.columns:
        rice_mask = gdf['CLASS2'] == 'R'
        gdf_rice = gdf[rice_mask].copy()
        logger.info(f"Filtered by CLASS2='R'")
    elif 'CLASS1' in gdf.columns:
        rice_mask = gdf['CLASS1'] == 'R'
        gdf_rice = gdf[rice_mask].copy()
        logger.info(f"Filtered by CLASS1='R'")
    else:
        logger.error("Could not find CLASS1 or CLASS2 column")
        raise ValueError("Cannot identify rice classification column")

    logger.info(f"Found {len(gdf_rice):,} rice polygons")

    # Filter by county if available
    if county_col and counties:
        county_mask = gdf_rice[county_col].isin(counties)
        gdf_rice = gdf_rice[county_mask].copy()
        logger.info(f"Filtered to {len(gdf_rice):,} rice polygons in {counties}")

    if len(gdf_rice) == 0:
        logger.error("No rice polygons found after filtering")
        return gdf_rice

    # Calculate area if not present
    if 'acres' not in gdf_rice.columns:
        # Reproject to California Albers (EPSG:3310) for accurate area calculation
        if gdf_rice.crs != 'EPSG:3310':
            logger.info("Reprojecting to California Albers (EPSG:3310) for area calculation")
            gdf_rice = gdf_rice.to_crs('EPSG:3310')

        gdf_rice['acres'] = gdf_rice.geometry.area / 4046.86  # sq meters to acres

    logger.info(f"Total rice acres: {gdf_rice['acres'].sum():,.0f}")

    return gdf_rice


def save_geojson(gdf: gpd.GeoDataFrame, data_dir: Path = Path("data")) -> Path:
    """
    Save rice polygons as GeoJSON.

    Args:
        gdf: GeoDataFrame with rice polygons
        data_dir: Root data directory

    Returns:
        Path to saved GeoJSON file
    """
    stage_dir = data_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)

    output_path = stage_dir / "dwr_rice_2022.geojson"

    # Reproject to WGS84 for GeoJSON standard
    if gdf.crs != 'EPSG:4326':
        logger.info("Reprojecting to WGS84 (EPSG:4326) for GeoJSON")
        gdf = gdf.to_crs('EPSG:4326')

    gdf.to_file(output_path, driver='GeoJSON')
    logger.info(f"Saved {len(gdf)} polygons to {output_path}")

    # Update manifest
    append_to_manifest(
        artifact_path=output_path,
        source="DWR_Crop_Map",
        artifact_type="geojson",
        notes=f"2022 rice polygons for Sacramento Valley counties",
        data_dir=data_dir
    )

    return output_path


def create_mart_data(gdf: gpd.GeoDataFrame, data_dir: Path = Path("data")) -> Path:
    """
    Create simplified mart dataset with centroids and key attributes.

    Args:
        gdf: GeoDataFrame with rice polygons
        data_dir: Root data directory

    Returns:
        Path to saved parquet file
    """
    mart_dir = data_dir / "mart"
    mart_dir.mkdir(parents=True, exist_ok=True)

    # Calculate centroids
    if gdf.crs != 'EPSG:4326':
        gdf = gdf.to_crs('EPSG:4326')

    gdf_copy = gdf.copy()
    centroids = gdf_copy.geometry.centroid

    # Extract key attributes
    df_mart = pd.DataFrame({
        'centroid_x': centroids.x,
        'centroid_y': centroids.y,
        'acres': gdf_copy['acres'],
    })

    # Add county if available
    county_cols = [col for col in gdf_copy.columns if 'county' in col.lower()]
    if county_cols:
        df_mart['county'] = gdf_copy[county_cols[0]].values

    # Add any district info if available
    district_cols = [col for col in gdf_copy.columns if 'district' in col.lower()]
    if district_cols:
        df_mart['district'] = gdf_copy[district_cols[0]].values

    output_path = mart_dir / "rice_polygons_2022.parquet"
    df_mart.to_parquet(output_path, index=False, engine="pyarrow")

    logger.info(f"Saved {len(df_mart)} rows to {output_path}")

    # Update manifest
    append_to_manifest(
        artifact_path=output_path,
        source="DWR_Crop_Map",
        artifact_type="parquet",
        notes=f"Rice polygon centroids and attributes for Sacramento Valley",
        data_dir=data_dir
    )

    return output_path


def main():
    """Main execution: download and process DWR crop mapping data."""
    data_dir = Path("data")
    raw_dir = data_dir / "raw" / "dwr_cropmap"

    # Download shapefile
    zip_path = download_shapefile(DWR_SHAPEFILE_URL, raw_dir)

    # Extract shapefile
    extract_dir = raw_dir / "extracted"
    shp_path = extract_shapefile(zip_path, extract_dir)

    # Load and filter for rice
    gdf_rice = load_and_filter_rice(shp_path, SACRAMENTO_VALLEY_COUNTIES)

    if gdf_rice.empty:
        logger.error("No rice data to save. Exiting.")
        return

    # Save GeoJSON
    geojson_path = save_geojson(gdf_rice, data_dir)
    logger.info(f"GeoJSON saved: {geojson_path}")

    # Create mart data
    mart_path = create_mart_data(gdf_rice, data_dir)
    logger.info(f"Mart data saved: {mart_path}")

    logger.info("DWR Crop Map fetch complete")


if __name__ == "__main__":
    main()
