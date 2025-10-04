#!/usr/bin/env python
"""
Fetch and parse DWR Bulletin 120 water supply forecasts.

Discovers the latest PDF from CDEC, downloads to raw/b120/,
and parses forecast summary table into stage/b120_forecast.parquet.
"""

import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from etl.utils_pdf import extract_tables_fallback, find_table_with_keyword
from etl.utils_manifest import append_to_manifest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CDEC_B120_URL = "https://cdec.water.ca.gov/snow/bulletin120/"
CDEC_BASE_URL = "https://cdec.water.ca.gov"
USER_AGENT = "Water-Opt/0.1.0 (Educational/Research)"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def discover_latest_pdf() -> Optional[str]:
    """
    Discover the latest Bulletin 120 PDF URL from CDEC page.

    Returns:
        URL to latest PDF, or None if not found
    """
    logger.info(f"Discovering latest Bulletin 120 PDF from {CDEC_B120_URL}")

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(CDEC_B120_URL, headers=headers, timeout=30)
        response.raise_for_status()

        # Look for PDF links in the HTML
        # Pattern: b120feb25.pdf, b120mar25.pdf, etc. (most recent year)
        # Also check for historical: FebHistory.pdf, MarHistory.pdf
        pdf_pattern = r'(b120[a-z]{3}\d{2}\.pdf|[A-Z][a-z]+History\.pdf|WSFCastDiscussion\.pdf)'
        matches = re.findall(pdf_pattern, response.text, re.IGNORECASE)

        if not matches:
            logger.warning("No PDF links found on CDEC page")
            return None

        # Get unique matches
        unique_pdfs = list(set(matches))
        logger.info(f"Found {len(unique_pdfs)} PDF(s): {unique_pdfs[:5]}")

        # Try to extract dates from b120 pattern files
        dated_pdfs = []
        for pdf in unique_pdfs:
            # Pattern: b120feb25.pdf -> feb 2025
            date_match = re.search(r'b120([a-z]{3})(\d{2})\.pdf', pdf, re.IGNORECASE)
            if date_match:
                try:
                    month_str = date_match.group(1)
                    year_str = date_match.group(2)
                    # Convert to full year (assume 21st century for 00-30, 20th century for 31-99)
                    year_short = int(year_str)
                    year = 2000 + year_short if year_short <= 30 else 1900 + year_short
                    # Parse month
                    month_abbrev = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5}
                    month = month_abbrev.get(month_str.lower(), 1)
                    date_obj = datetime(year, month, 1)
                    dated_pdfs.append((date_obj, pdf))
                except (ValueError, KeyError):
                    continue

        if dated_pdfs:
            # Sort by date, most recent first
            dated_pdfs.sort(reverse=True)
            latest_pdf = dated_pdfs[0][1]
            logger.info(f"Latest Bulletin 120: {latest_pdf} ({dated_pdfs[0][0].strftime('%B %Y')})")
        else:
            # Fall back to WSFCastDiscussion.pdf or first match
            for pdf in unique_pdfs:
                if "wsf" in pdf.lower() or "discussion" in pdf.lower():
                    latest_pdf = pdf
                    logger.info(f"Using forecast discussion PDF: {latest_pdf}")
                    break
            else:
                latest_pdf = unique_pdfs[0]
                logger.info(f"Using first PDF found: {latest_pdf}")

        # Construct full URL
        if latest_pdf.startswith("http"):
            return latest_pdf
        elif latest_pdf.startswith("/"):
            return f"{CDEC_BASE_URL}{latest_pdf}"
        else:
            return f"{CDEC_B120_URL}{latest_pdf}"

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to discover PDF: {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def download_pdf(url: str, output_dir: Path) -> Path:
    """
    Download PDF from URL to output directory with timestamped filename.

    Args:
        url: PDF URL
        output_dir: Directory to save PDF

    Returns:
        Path to downloaded PDF
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract filename from URL or create timestamped one
    filename = url.split("/")[-1]
    if not filename.endswith(".pdf"):
        filename = f"b120_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    output_path = output_dir / filename

    logger.info(f"Downloading {url} to {output_path}")

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded {output_path.stat().st_size:,} bytes")
        return output_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download PDF: {e}")
        raise


def parse_forecast_table(pdf_path: Path) -> Optional[pd.DataFrame]:
    """
    Parse forecast summary table from Bulletin 120 PDF.

    Looks for table with basin names and April-July runoff forecasts.

    Args:
        pdf_path: Path to PDF file

    Returns:
        DataFrame with columns: basin, median, p10, p90, report_date
    """
    logger.info(f"Parsing forecast table from {pdf_path.name}")

    try:
        # Try stream flavor on pages 3-5 (where forecast table typically is)
        import camelot
        tables = camelot.read_pdf(str(pdf_path), pages="3-5", flavor="stream")

        if not tables:
            # Fall back to lattice
            logger.info("Stream extraction failed, trying lattice")
            tables = camelot.read_pdf(str(pdf_path), pages="1-5", flavor="lattice")

        if not tables:
            logger.warning("No tables extracted from PDF")
            return None

        # Find the largest table (likely the forecast table)
        forecast_table = None
        max_rows = 0
        for i, table in enumerate(tables):
            df = table.df if hasattr(table, 'df') else table
            if len(df) > max_rows:
                max_rows = len(df)
                forecast_table = df

        if forecast_table is None or forecast_table.empty:
            logger.error("No suitable forecast table found")
            return None

        df = forecast_table.copy()
        logger.info(f"Using table with {len(df)} rows and {len(df.columns)} columns")

        # Bulletin 120 tables have basin names in column 0
        # We'll extract basin names and try to get a single forecast value (30yr avg or forecast)
        output_rows = []

        for idx, row in df.iterrows():
            basin = str(row[0]).strip() if len(row) > 0 else ""

            # Skip header rows and empty basins
            if not basin or len(basin) < 3:
                continue

            # Skip obvious headers
            if any(kw in basin.lower() for kw in ["hydrologic", "watershed", "april", "runoff", "avg", "probability"]):
                continue

            # Skip section headers (all caps, no numbers in row)
            if basin.isupper() and not any(str(row[i]).replace(",", "").replace("-", "").replace("\n", "").strip().isdigit() for i in range(1, min(len(row), 5))):
                continue

            # Try to extract numeric values from any column
            # Look for a reasonable forecast value (usually in thousands of acre-feet)
            forecast_val = None
            for i in range(1, min(len(row), 8)):
                val_str = str(row[i]).replace(",", "").replace("\n", " ").strip()
                if val_str and val_str != "--":
                    # Try to extract first number
                    numbers = re.findall(r'\d+', val_str)
                    if numbers:
                        try:
                            forecast_val = float(numbers[0])
                            break
                        except ValueError:
                            continue

            if forecast_val and forecast_val > 0:
                # For now, use the forecast value as median
                # p10 and p90 can be derived or left as None
                output_rows.append({
                    "basin": basin,
                    "median": forecast_val,
                    "p10": None,  # TODO: extract from range if available
                    "p90": None   # TODO: extract from range if available
                })

        if not output_rows:
            logger.error("No valid forecast rows extracted")
            return None

        # Extract report date from filename
        date_match = re.search(r'(\d{8})', pdf_path.name)
        if date_match:
            try:
                report_date = datetime.strptime(date_match.group(1), "%Y%m%d").date()
            except ValueError:
                report_date = datetime.now().date()
        else:
            report_date = datetime.now().date()

        df_output = pd.DataFrame(output_rows)
        df_output["report_date"] = report_date

        logger.info(f"Parsed {len(df_output)} forecast entries")
        return df_output

    except Exception as e:
        logger.error(f"Error parsing forecast table: {e}")
        return None


def save_stage_data(df: pd.DataFrame, data_dir: Path = Path("data")) -> Path:
    """
    Save forecast data to stage directory.

    Args:
        df: DataFrame with forecast data
        data_dir: Root data directory

    Returns:
        Path to saved parquet file
    """
    stage_dir = data_dir / "stage"
    stage_dir.mkdir(parents=True, exist_ok=True)

    output_path = stage_dir / "b120_forecast.parquet"

    # Ensure correct dtypes
    df["basin"] = df["basin"].astype(str)
    df["report_date"] = pd.to_datetime(df["report_date"])

    df.to_parquet(output_path, index=False, engine="pyarrow")
    logger.info(f"Saved {len(df)} rows to {output_path}")

    # Update manifest
    append_to_manifest(
        artifact_path=output_path,
        source="Bulletin_120",
        artifact_type="parquet",
        notes=f"Water supply forecasts from DWR Bulletin 120",
        data_dir=data_dir
    )

    return output_path


def main():
    """Main execution: discover, download, parse Bulletin 120."""
    data_dir = Path("data")
    raw_dir = data_dir / "raw" / "b120"

    # Discover latest PDF
    pdf_url = discover_latest_pdf()
    if not pdf_url:
        logger.error("Could not discover latest PDF. Exiting.")
        return

    # Download PDF
    pdf_path = download_pdf(pdf_url, raw_dir)

    # Parse forecast table
    df = parse_forecast_table(pdf_path)
    if df is None or df.empty:
        logger.error("Could not parse forecast table. Exiting.")
        return

    # Save stage data
    stage_path = save_stage_data(df)
    logger.info(f"Bulletin 120 fetch complete: {stage_path}")


if __name__ == "__main__":
    main()
