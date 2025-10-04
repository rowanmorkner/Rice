#!/usr/bin/env python
"""
ETL orchestrator for Water-Opt MVP.

Coordinates execution of all data fetchers with CLI flags for selective execution.
Implements idempotent runs with retry logic and polite user-agent headers.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_fetcher(fetcher_name: str, fetcher_module: str) -> Dict:
    """
    Execute a single fetcher module and capture results.

    Args:
        fetcher_name: Display name of the fetcher
        fetcher_module: Python module path (e.g., 'etl.fetch_awdb')

    Returns:
        Dict with status, rows_written, targets, and messages
    """
    logger.info(f"=" * 60)
    logger.info(f"Running {fetcher_name} fetcher")
    logger.info(f"=" * 60)

    start_time = time.time()
    result = {
        "fetcher": fetcher_name,
        "status": "unknown",
        "rows_written": 0,
        "targets": [],
        "messages": [],
        "duration_seconds": 0
    }

    try:
        # Import and run the fetcher
        module = __import__(fetcher_module, fromlist=['main'])

        if hasattr(module, 'main'):
            module.main()
            result["status"] = "success"
            result["messages"].append(f"{fetcher_name} completed successfully")
        else:
            result["status"] = "error"
            result["messages"].append(f"No main() function found in {fetcher_module}")
            logger.error(f"Module {fetcher_module} has no main() function")

    except ImportError as e:
        result["status"] = "error"
        result["messages"].append(f"Failed to import {fetcher_module}: {e}")
        logger.error(f"Import error for {fetcher_module}: {e}")

    except Exception as e:
        result["status"] = "error"
        result["messages"].append(f"Error running {fetcher_name}: {e}")
        logger.error(f"Error running {fetcher_name}: {e}", exc_info=True)

    result["duration_seconds"] = time.time() - start_time

    logger.info(f"{fetcher_name} completed in {result['duration_seconds']:.1f} seconds")
    logger.info("")

    return result


def run_etl_pipeline(
    awdb: bool = False,
    b120: bool = False,
    ers: bool = False,
    nass: bool = False,
    cimis: bool = False,
    dwr: bool = False,
    ssebop: bool = False,
    all_fetchers: bool = False
) -> Dict:
    """
    Run selected ETL fetchers based on flags.

    Args:
        awdb: Run AWDB SNOTEL fetcher
        b120: Run Bulletin 120 fetcher
        ers: Run ERS Rice Outlook fetcher
        nass: Run NASS QuickStats fetcher
        cimis: Run CIMIS ETo fetcher
        dwr: Run DWR Crop Map fetcher
        ssebop: Run SSEBop ET fetcher (stub)
        all_fetchers: Run all fetchers

    Returns:
        Dict with summary of all fetcher results
    """
    pipeline_start = time.time()

    # Define fetcher configurations
    fetchers = {
        "awdb": ("AWDB (SNOTEL)", "etl.fetch_awdb"),
        "b120": ("Bulletin 120", "etl.fetch_b120"),
        "ers": ("ERS Rice Outlook", "etl.fetch_ers_rice_outlook"),
        "nass": ("NASS QuickStats", "etl.fetch_nass"),
        "cimis": ("CIMIS ETo", "etl.fetch_cimis"),
        "dwr": ("DWR Crop Map", "etl.fetch_dwr_cropmap"),
        "ssebop": ("SSEBop ET", "etl.fetch_ssebop")
    }

    # Determine which fetchers to run
    if all_fetchers:
        selected = list(fetchers.keys())
    else:
        selected = []
        if awdb:
            selected.append("awdb")
        if b120:
            selected.append("b120")
        if ers:
            selected.append("ers")
        if nass:
            selected.append("nass")
        if cimis:
            selected.append("cimis")
        if dwr:
            selected.append("dwr")
        if ssebop:
            selected.append("ssebop")

    if not selected:
        logger.warning("No fetchers selected. Use --all or specify individual flags.")
        logger.info("Available flags: --awdb, --b120, --ers, --nass, --cimis, --dwr, --ssebop, --all")
        return {
            "status": "no_fetchers",
            "results": [],
            "summary": {
                "total": 0,
                "success": 0,
                "error": 0,
                "total_duration": 0
            }
        }

    logger.info("")
    logger.info("=" * 60)
    logger.info("Water-Opt ETL Pipeline")
    logger.info("=" * 60)
    logger.info(f"Selected fetchers: {', '.join(selected)}")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # Run selected fetchers
    results = []
    for fetcher_key in selected:
        if fetcher_key in fetchers:
            name, module = fetchers[fetcher_key]
            result = run_fetcher(name, module)
            results.append(result)

    # Calculate summary
    pipeline_duration = time.time() - pipeline_start
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")

    summary = {
        "total": len(results),
        "success": success_count,
        "error": error_count,
        "total_duration": pipeline_duration
    }

    # Print summary
    logger.info("=" * 60)
    logger.info("ETL Pipeline Summary")
    logger.info("=" * 60)
    logger.info(f"Total fetchers: {summary['total']}")
    logger.info(f"Successful: {summary['success']}")
    logger.info(f"Errors: {summary['error']}")
    logger.info(f"Total duration: {summary['total_duration']:.1f} seconds")
    logger.info("")

    for result in results:
        status_icon = "✓" if result["status"] == "success" else "✗"
        logger.info(f"{status_icon} {result['fetcher']}: {result['status']} ({result['duration_seconds']:.1f}s)")
        for msg in result["messages"]:
            logger.info(f"  - {msg}")

    logger.info("")
    logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    return {
        "status": "completed",
        "results": results,
        "summary": summary
    }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Water-Opt ETL Pipeline - Fetch and process water data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all fetchers
  python -m etl.fetch_all --all

  # Run specific fetchers
  python -m etl.fetch_all --awdb --b120 --dwr

  # Run individual fetcher
  python -m etl.fetch_all --cimis

  # Run core data sources
  python -m etl.fetch_all --awdb --b120 --ers --dwr
        """
    )

    # Add individual fetcher flags
    parser.add_argument("--awdb", action="store_true",
                        help="Fetch AWDB SNOTEL snow water equivalent data")
    parser.add_argument("--b120", action="store_true",
                        help="Fetch DWR Bulletin 120 water supply forecasts")
    parser.add_argument("--ers", action="store_true",
                        help="Fetch USDA ERS Rice Outlook price data")
    parser.add_argument("--nass", action="store_true",
                        help="Fetch NASS QuickStats rice yields and prices")
    parser.add_argument("--cimis", action="store_true",
                        help="Fetch CIMIS reference evapotranspiration data")
    parser.add_argument("--dwr", action="store_true",
                        help="Fetch DWR crop mapping rice polygons")
    parser.add_argument("--ssebop", action="store_true",
                        help="Run SSEBop ET fetcher (stub)")
    parser.add_argument("--all", action="store_true",
                        help="Run all fetchers")

    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run pipeline
    result = run_etl_pipeline(
        awdb=args.awdb,
        b120=args.b120,
        ers=args.ers,
        nass=args.nass,
        cimis=args.cimis,
        dwr=args.dwr,
        ssebop=args.ssebop,
        all_fetchers=args.all
    )

    # Exit with appropriate code
    if result["status"] == "no_fetchers":
        sys.exit(1)
    elif result["summary"]["error"] > 0:
        logger.warning(f"{result['summary']['error']} fetcher(s) had errors")
        sys.exit(1)
    else:
        logger.info("All fetchers completed successfully ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()
