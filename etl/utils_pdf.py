"""
PDF parsing utilities for Bulletin 120 and ERS Rice Outlook.

Provides wrappers around camelot-py and tabula-py with fallback handling.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)


def extract_tables_camelot(
    pdf_path: Path,
    pages: str = "all",
    flavor: str = "lattice",
    **kwargs
) -> List[pd.DataFrame]:
    """
    Extract tables from PDF using camelot-py.

    Args:
        pdf_path: Path to PDF file
        pages: Pages to extract (e.g., "1", "1,2,3", "all")
        flavor: "lattice" (bordered tables) or "stream" (spacing-based)
        **kwargs: Additional camelot arguments (e.g., table_areas, columns)

    Returns:
        List of DataFrames, one per table found

    Raises:
        ImportError: If camelot not installed
        FileNotFoundError: If PDF not found
    """
    try:
        import camelot
    except ImportError:
        logger.error("camelot-py not installed. Run: pip install 'camelot-py[cv]'")
        raise

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(f"Extracting tables from {pdf_path.name} (pages={pages}, flavor={flavor})")

    tables = camelot.read_pdf(
        str(pdf_path),
        pages=pages,
        flavor=flavor,
        **kwargs
    )

    logger.info(f"Found {len(tables)} table(s)")

    dfs = [table.df for table in tables]
    return dfs


def extract_tables_tabula(
    pdf_path: Path,
    pages: str = "all",
    multiple_tables: bool = True,
    **kwargs
) -> List[pd.DataFrame]:
    """
    Extract tables from PDF using tabula-py (Java-based, good for complex layouts).

    Args:
        pdf_path: Path to PDF file
        pages: Pages to extract (e.g., "1", "1,2,3", "all")
        multiple_tables: If True, return list; if False, combine into one DataFrame
        **kwargs: Additional tabula arguments (e.g., area, lattice)

    Returns:
        List of DataFrames

    Raises:
        ImportError: If tabula not installed
        FileNotFoundError: If PDF not found
    """
    try:
        import tabula
    except ImportError:
        logger.error("tabula-py not installed. Run: pip install tabula-py")
        raise

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(f"Extracting tables from {pdf_path.name} with tabula (pages={pages})")

    result = tabula.read_pdf(
        str(pdf_path),
        pages=pages,
        multiple_tables=multiple_tables,
        **kwargs
    )

    # Ensure result is a list
    if not isinstance(result, list):
        result = [result]

    logger.info(f"Found {len(result)} table(s)")
    return result


def extract_tables_fallback(
    pdf_path: Path,
    pages: str = "all",
    prefer: str = "camelot",
    camelot_kwargs: Optional[Dict[str, Any]] = None,
    tabula_kwargs: Optional[Dict[str, Any]] = None
) -> List[pd.DataFrame]:
    """
    Try camelot first, fall back to tabula if camelot fails or returns empty.

    Args:
        pdf_path: Path to PDF file
        pages: Pages to extract
        prefer: "camelot" or "tabula" to try first
        camelot_kwargs: Arguments for camelot
        tabula_kwargs: Arguments for tabula

    Returns:
        List of DataFrames
    """
    camelot_kwargs = camelot_kwargs or {}
    tabula_kwargs = tabula_kwargs or {}

    methods = ["camelot", "tabula"] if prefer == "camelot" else ["tabula", "camelot"]

    for method in methods:
        try:
            if method == "camelot":
                tables = extract_tables_camelot(pdf_path, pages=pages, **camelot_kwargs)
            else:
                tables = extract_tables_tabula(pdf_path, pages=pages, **tabula_kwargs)

            # Check if we got non-empty results
            if tables and any(not df.empty for df in tables):
                logger.info(f"Successfully extracted with {method}")
                return tables
            else:
                logger.warning(f"{method} returned empty tables, trying fallback")

        except Exception as e:
            logger.warning(f"{method} failed: {e}, trying fallback")
            continue

    logger.error(f"All methods failed for {pdf_path.name}")
    return []


def clean_table_headers(df: pd.DataFrame, header_row: int = 0) -> pd.DataFrame:
    """
    Promote a row to column headers and clean up multiline headers.

    Args:
        df: Input DataFrame
        header_row: Row index to use as header

    Returns:
        DataFrame with cleaned headers
    """
    if df.empty:
        return df

    # Use specified row as header
    df_clean = df.copy()
    if header_row > 0:
        df_clean.columns = df_clean.iloc[header_row]
        df_clean = df_clean.iloc[header_row + 1:].reset_index(drop=True)

    # Clean column names: strip whitespace, lowercase, replace spaces with underscores
    df_clean.columns = (
        df_clean.columns
        .astype(str)
        .str.strip()
        .str.replace(r'\s+', '_', regex=True)
        .str.replace(r'[^\w_]', '', regex=True)
        .str.lower()
    )

    return df_clean


def find_table_with_keyword(
    tables: List[pd.DataFrame],
    keyword: str,
    case_sensitive: bool = False
) -> Optional[pd.DataFrame]:
    """
    Find first table containing a keyword in any cell.

    Args:
        tables: List of DataFrames to search
        keyword: String to search for
        case_sensitive: Whether search is case-sensitive

    Returns:
        First matching DataFrame, or None
    """
    for df in tables:
        if df.empty:
            continue

        # Convert all cells to string and search
        search_df = df.astype(str)
        if not case_sensitive:
            search_df = search_df.apply(lambda col: col.str.lower())
            keyword = keyword.lower()

        # Check if keyword appears anywhere
        mask = search_df.apply(lambda col: col.str.contains(keyword, na=False, regex=False))
        if mask.any().any():
            logger.info(f"Found table containing '{keyword}'")
            return df

    logger.warning(f"No table found containing '{keyword}'")
    return None
