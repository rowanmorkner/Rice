# Water-Opt MVP

Desktop-first "Grow vs. Fallow & Sell Water" decision tool for Central California rice growers.

## Installation

### Prerequisites

**macOS:**
```bash
# For camelot-py (PDF table extraction)
brew install ghostscript tcl-tk

# For raster processing (Phase 2: SSEBop ET)
brew install gdal
```

**Linux (Debian/Ubuntu):**
```bash
# For camelot-py
sudo apt-get install ghostscript python3-tk

# For tabula-py
sudo apt-get install default-jre

# For raster processing (Phase 2: SSEBop ET)
sudo apt-get install gdal-bin libgdal-dev python3-gdal
```

**Windows:**
```powershell
# For raster processing (Phase 2: SSEBop ET)
# Install OSGeo4W from https://trac.osgeo.org/osgeo4w/
# Or use conda: conda install -c conda-forge gdal
```

### Python Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Optional API keys (leave blank for MVP):
- `NASS_API_KEY`: USDA NASS QuickStats API key
- `CIMIS_APP_KEY`: CIMIS ETo data API key

## Usage

### Run ETL Pipeline

```bash
make etl
```

This fetches and processes:
- NRCS AWDB/SNOTEL snow water equivalent data
- DWR Bulletin 120 water supply forecasts
- USDA ERS Rice Outlook prices
- CA DWR Statewide Crop Mapping (rice polygons)

### Launch Dashboard

```bash
make app
```

Opens Streamlit dashboard at http://localhost:8501

### Run Tests

```bash
make test
```

### Clean Data

```bash
make clean
```

Removes staged/mart data files and manifest.

## Project Structure

```
water-opt/
├── data/           # Raw, staged, and mart data (gitignored)
├── etl/            # Data fetchers and utilities
├── models/         # Profit and scenario models
├── app/            # Streamlit dashboard
├── tests/          # Unit tests
├── docs/           # Documentation
└── notebooks/      # Analysis notebooks
```

## Documentation

- [Data Sources](data_sources.md) - Complete guide to all data sources with URLs and notes
- [Assumptions](assumptions.md) - Model assumptions, default parameters, and calculation formulas
- [Case Study Template](case_study_template.md) - Template for historical backtest analysis

## Quick Start

1. **Install dependencies**:
   ```bash
   make setup
   ```

2. **Configure API keys** (optional):
   - Get NASS API key: https://quickstats.nass.usda.gov/api
   - Get CIMIS API key: http://et.water.ca.gov/Home/Register
   - Add to `.env` file

3. **Fetch data**:
   ```bash
   make etl
   ```

4. **Run tests**:
   ```bash
   make test
   ```

5. **Launch dashboard**:
   ```bash
   make app
   ```

6. **Open browser**: http://localhost:8501

## Data Refresh Notes

### When to Refresh Data

- **Daily**: AWDB SWE, CIMIS ETo (for current conditions)
- **Monthly**: Bulletin 120 (during snow season Dec-May), ERS Rice Outlook
- **Annually**: DWR Crop Map (released in fall for previous year)
- **As Needed**: NASS data when API recovers

### Refresh Commands

```bash
# Fetch all available data
python -m etl.fetch_all --all

# Fetch specific sources
python -m etl.fetch_all --awdb --b120 --dwr --cimis

# Fetch only hydrology data
python -m etl.fetch_all --awdb --b120

# Check which data is available
ls -lh data/stage/
ls -lh data/mart/
```

### Manifest Tracking

All data artifacts are tracked in `data/manifest.csv` with:
- Timestamp
- File path and type
- Row count and file size
- SHA-256 hash for integrity
- Source and notes

View manifest:
```bash
cat data/manifest.csv
```

## Troubleshooting

### PDF Extraction Issues

If camelot-py fails to extract tables:
- **macOS**: Ensure ghostscript is installed: `brew install ghostscript`
- **Linux**: Ensure ghostscript and python3-tk are installed
- Tabula-py will be used as fallback automatically

### NASS API Timeouts

NASS QuickStats API has known performance issues:
- Full fetcher implementation is ready when API recovers
- Graceful error handling in place
- Use ERS stub data for now

### Missing Data in Dashboard

The Streamlit app gracefully handles missing data:
- Each tab shows helpful messages if data unavailable
- Run `make etl` to fetch required data
- Check sidebar "Data Status" panel for which sources are available

### Memory Issues with Large Files

DWR Crop Map shapefile is ~500MB extracted:
- First run may take several minutes
- Subsequent runs use cached parquet files
- If memory issues, reduce `head_limit` in fetch_dwr_cropmap.py

## Advanced Usage

### Run Individual Fetchers

```bash
# AWDB only
python -m etl.fetch_awdb

# DWR Crop Map only
python -m etl.fetch_dwr_cropmap

# CIMIS ETo (requires API key)
python -m etl.fetch_cimis
```

### Custom Parameter Analysis

Modify parameters in Streamlit Setup tab or use profit model directly:

```python
from models.profit import compare_profit

result = compare_profit(
    acres=250,
    expected_yield_cwt_ac=90,
    price_usd_cwt=21.0,
    var_cost_usd_ac=700,
    fixed_cost_usd=12000,
    cu_af_per_ac=4.2,
    water_price_usd_af=300,
    conveyance_loss_frac=0.12,
    transaction_cost_usd=800
)

print(f"Profit (Grow): ${result['profit_grow']:,.0f}")
print(f"Profit (Fallow): ${result['profit_fallow']:,.0f}")
print(f"Breakeven: ${result['breakeven_water_price_usd_af']:.2f}/af")
```

### Export Results

Use the Export button in the Decision tab to save:
- CSV with all parameters and results to `data/mart/exports/`
- Timestamped for tracking multiple scenarios

## System Requirements

- **Python**: 3.10+
- **Memory**: 2GB minimum (4GB recommended for DWR shapefile processing)
- **Disk**: 1GB for data storage
- **Internet**: Required for initial data fetch, optional afterwards

## License and Disclaimer

This is an educational tool for planning purposes only. Always consult with:
- Your irrigation district for water transfer rules
- A water rights attorney for legal requirements
- The State Water Resources Control Board for permit requirements
- Qualified professionals before making farm management decisions

See Compliance tab in dashboard for detailed regulatory information.
