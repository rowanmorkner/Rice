# Water-Opt MVP - Functionality Report
**Generated:** October 3, 2025
**Status:** Phase 1 Complete (2 of 4 core fetchers implemented)

---

## Executive Summary

The Water-Opt MVP is a desktop tool for California rice growers to compare "grow rice" vs. "fallow & sell water" decisions. Phase 1 establishes the ETL infrastructure and implements hydrology data pipelines.

**Completed:**
- ✓ Project scaffold and dependencies
- ✓ ETL utilities (PDF parsing, manifest tracking)
- ✓ AWDB/SNOTEL snow water equivalent fetcher
- ✓ DWR Bulletin 120 water supply forecast fetcher

**Next Steps:** ERS Rice Outlook (prices), DWR Crop Map (land), profit models, Streamlit dashboard

---

## 1. System Architecture

### Directory Structure
```
water-opt/
├── data/
│   ├── raw/b120/          # Downloaded PDFs
│   ├── stage/             # Normalized parquet files
│   ├── mart/              # Derived analytics datasets
│   └── manifest.csv       # Artifact tracking log
├── etl/
│   ├── fetch_awdb.py      # ✓ SNOTEL snow data
│   ├── fetch_b120.py      # ✓ Bulletin 120 forecasts
│   ├── utils_pdf.py       # ✓ PDF table extraction
│   └── utils_manifest.py  # ✓ Data lineage tracking
├── models/                # (Pending: profit, scenarios)
├── app/                   # (Pending: Streamlit dashboard)
├── tests/                 # (Pending: unit tests)
└── docs/                  # (Partial: README.md)
```

### Technology Stack
- **Data:** pandas, pyarrow (parquet), geopandas (future)
- **ETL:** requests, tenacity (retries), camelot-py/tabula-py (PDF parsing)
- **Viz:** streamlit, plotly (future)
- **Database:** Local parquet files (DuckDB integration possible)

---

## 2. Implemented Features

### 2.1 AWDB/SNOTEL Snow Data Pipeline ✓

**Module:** `etl/fetch_awdb.py`

**Purpose:** Fetch daily snow water equivalent (SWE) from Sierra Nevada SNOTEL stations to assess hydrology scenarios (dry/median/wet years).

**Data Source:** NRCS AWDB REST API v1
**Endpoint:** `https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data`

**Implementation:**
- Queries 12 Sierra Nevada stations (El Dorado, Alpine, Nevada, Mono counties)
- Retrieves daily SWE from January 1, 2015 to present
- Converts inches to millimeters
- Retries with exponential backoff on network failures

**Outputs:**
1. **stage/awdb_swe_daily.parquet**
   - Rows: 47,118 (10+ years × 12 stations × 365 days)
   - Schema: `date, station_id, wteq_mm`
   - Date range: 2015-01-01 to 2025-10-02
   - SWE range: 0 to 2,284 mm (0 to 90 inches)

2. **mart/hydro_scenarios.parquet**
   - Rows: 12 (one per month)
   - Schema: `month, p10_dry_mm, p50_median_mm, p90_wet_mm, scenario_type`
   - Derived from historical percentiles across all stations
   - Example: April p50 = 394 mm (median snowpack)

**Quality Metrics:**
- ✓ All 12 stations have ~3,928 records each
- ✓ No missing values
- ✓ Data freshness: Updated to October 2, 2025

**Command to Run:**
```bash
python -m etl.fetch_awdb
```

---

### 2.2 DWR Bulletin 120 Water Supply Forecasts ✓

**Module:** `etl/fetch_b120.py`

**Purpose:** Download and parse California Department of Water Resources' official water supply forecasts for major watersheds.

**Data Source:** CDEC Bulletin 120 Archive
**URL:** `https://cdec.water.ca.gov/snow/bulletin120/`

**Implementation:**
- Discovers latest PDF from CDEC page (regex pattern matching)
- Downloads to `data/raw/b120/` with timestamped filename
- Extracts forecast table using camelot-py (stream flavor, pages 3-5)
- Parses basin names and April-July runoff forecasts (1000 acre-feet)

**Outputs:**
1. **raw/b120/b120apr22.pdf**
   - Size: 1.6 MB
   - Latest available: April 2022 bulletin

2. **stage/b120_forecast.parquet**
   - Rows: 36 basins/watersheds
   - Schema: `basin, median, p10, p90, report_date`
   - Forecast range: 40 to 2,474 thousand acre-feet
   - Key basins: Sacramento River, Feather River, American River, San Joaquin River

**Quality Metrics:**
- ✓ 36 basins extracted successfully
- ✓ No missing median values
- ✓ Resilient to PDF table variations (uses stream + lattice fallback)
- ⚠ p10/p90 not yet extracted (future enhancement)

**Top 5 Forecasts:**
1. Sacramento River above Bend Bridge: 2,474 KAF
2. Total Inflow to Shasta Lake: 1,767 KAF
3. Feather River at Oroville: 1,710 KAF
4. American River below Folsom Lake: 1,247 KAF
5. San Joaquin River inflow to Millerton Lake: 1,229 KAF

**Command to Run:**
```bash
python -m etl.fetch_b120
```

---

### 2.3 ETL Utilities ✓

**Module:** `etl/utils_pdf.py`

**Functions:**
- `extract_tables_camelot()` - Bordered table extraction
- `extract_tables_tabula()` - Java-based PDF parsing
- `extract_tables_fallback()` - Tries both methods with intelligent fallback
- `clean_table_headers()` - Normalizes column names
- `find_table_with_keyword()` - Searches tables by content

**Module:** `etl/utils_manifest.py`

**Functions:**
- `init_manifest()` - Creates tracking CSV on first run
- `append_to_manifest()` - Logs artifact metadata (timestamp, SHA-256, row count)
- `get_latest_artifact()` - Retrieves most recent file for a source
- `compute_file_hash()` - SHA-256 checksums for data integrity

**Manifest Tracking:**
```
timestamp,artifact_path,artifact_type,row_count,file_size_bytes,sha256_hash,source,notes
```

---

## 3. Data Quality & Validation

### Automated Verification
Run the verification script to check all systems:
```bash
python verify_system.py
```

**Test Results:**
- ✓ All 6 module imports succeed
- ✓ All 3 parquet files present and valid
- ✓ 47,118 AWDB records (no nulls)
- ✓ 36 B120 basin forecasts
- ✓ 12 monthly hydro scenarios
- ✓ 6 artifacts logged in manifest

### Manual Verification Steps

1. **Check Directory Structure:**
   ```bash
   tree data -L 2
   ```
   Expected: `data/{raw/b120, stage, mart}` with parquet files

2. **Verify AWDB Data:**
   ```bash
   python -c "import pandas as pd; df=pd.read_parquet('data/stage/awdb_swe_daily.parquet'); print(f'Rows: {len(df)}, Stations: {df.station_id.nunique()}, Date range: {df.date.min()} to {df.date.max()}')"
   ```
   Expected: ~47,118 rows, 12 stations, 2015-2025

3. **Verify Bulletin 120 Data:**
   ```bash
   python -c "import pandas as pd; df=pd.read_parquet('data/stage/b120_forecast.parquet'); print(df[['basin', 'median']].head(10))"
   ```
   Expected: 36 rows with basin names and forecast values

4. **Check Manifest:**
   ```bash
   cat data/manifest.csv | column -t -s,
   ```
   Expected: 6+ entries with AWDB and Bulletin_120 sources

5. **Re-run Fetchers (Idempotency Test):**
   ```bash
   python -m etl.fetch_awdb
   python -m etl.fetch_b120
   ```
   Expected: Both complete without errors, manifest appends new entries

---

## 4. Known Limitations & Future Work

### Current Limitations

1. **Bulletin 120:** Only extracts median forecast; p10/p90 percentiles need enhanced parsing
2. **AWDB Stations:** Limited to 12 stations; could expand to 36 CA SNOTEL sites
3. **Data Freshness:** Bulletin 120 limited by CDEC archive (latest: April 2022)
4. **No Orchestrator:** Each fetcher runs independently; `fetch_all.py` not yet implemented
5. **No Tests:** Unit tests for profit models and ETL pending
6. **No Dashboard:** Streamlit app not yet built

### Deviations from Spec

1. **AWDB API:** Instructions mention v3, but v1 is the only working endpoint
2. **utils_manifest.py:** Created as separate module (not in original spec, but needed)
3. **PDF Libraries:** Installed camelot-py and tabula-py during build (required for B120)

---

## 5. Next Steps (Priority Order)

### Phase 2: Market Data (Tasks 4-5)
- [ ] **Task 4.1-4.2:** ERS Rice Outlook fetcher (PDF/XLSX scraping for CA rice prices)
- [ ] **Task 5.1-5.2:** DWR Crop Map fetcher (ArcGIS REST query for rice polygons)
- [ ] **Task 5B.1-5B.3:** Stub fetchers for NASS, CIMIS, SSEBop

### Phase 3: Models & Orchestration (Tasks 6-7)
- [ ] **Task 6:** `fetch_all.py` orchestrator with CLI flags
- [ ] **Task 7:** Profit model (`models/profit.py`) and scenario bands (`models/scenarios.py`)

### Phase 4: Application & Testing (Tasks 8-12)
- [ ] **Task 8:** Unit tests for profit math and ETL
- [ ] **Task 9:** Streamlit app with 6 tabs (Setup, Hydrology, Markets, Decision, Map, Compliance)
- [ ] **Task 10:** Documentation (assumptions, data sources, case study template)
- [ ] **Task 11:** Makefile verification (`make etl`, `make app`, `make test`)
- [ ] **Task 12:** Final system verification

---

## 6. How to Use (Current State)

### Installation
```bash
# Clone/navigate to project
cd WaterProj

# Install dependencies
pip install -r requirements.txt

# On macOS, install PDF dependencies
brew install ghostscript tcl-tk
```

### Fetch Data
```bash
# Fetch SNOTEL snow data
python -m etl.fetch_awdb

# Fetch Bulletin 120 forecasts
python -m etl.fetch_b120

# Verify everything works
python verify_system.py
```

### Explore Data
```python
import pandas as pd

# Load AWDB snow data
df_swe = pd.read_parquet("data/stage/awdb_swe_daily.parquet")
print(df_swe.head())

# Load hydrology scenarios
df_scenarios = pd.read_parquet("data/mart/hydro_scenarios.parquet")
print(df_scenarios)

# Load water supply forecasts
df_b120 = pd.read_parquet("data/stage/b120_forecast.parquet")
print(df_b120[['basin', 'median']].head(10))
```

---

## 7. Project Status Summary

| Component | Status | Progress |
|-----------|--------|----------|
| Repo scaffold | ✓ Complete | 100% |
| ETL utilities | ✓ Complete | 100% |
| AWDB fetcher | ✓ Complete | 100% |
| Bulletin 120 fetcher | ✓ Complete | 100% |
| ERS Rice Outlook | ⏳ Pending | 0% |
| DWR Crop Map | ⏳ Pending | 0% |
| Stub fetchers | ⏳ Pending | 0% |
| Orchestrator | ⏳ Pending | 0% |
| Profit models | ⏳ Pending | 0% |
| Tests | ⏳ Pending | 0% |
| Streamlit app | ⏳ Pending | 0% |
| Documentation | 🟡 Partial | 25% |

**Overall Progress:** 4 of 12 major tasks complete (33%)

---

## Appendix: File Inventory

### Code Files (11 files)
```
.gitignore
.env.example
requirements.txt
pyproject.toml
Makefile
etl/__init__.py
etl/fetch_awdb.py (270 lines)
etl/fetch_b120.py (290 lines)
etl/utils_pdf.py (195 lines)
etl/utils_manifest.py (175 lines)
models/__init__.py
app/components/__init__.py
verify_system.py (145 lines)
```

### Data Files (5 files)
```
data/manifest.csv (6 entries)
data/raw/b120/b120apr22.pdf (1.6 MB)
data/stage/awdb_swe_daily.parquet (75 KB, 47,118 rows)
data/stage/b120_forecast.parquet (4.3 KB, 36 rows)
data/mart/hydro_scenarios.parquet (3.6 KB, 12 rows)
```

### Documentation
```
docs/README.md (installation & usage)
CHECKLIST.md (12 sections, 4 complete)
instructions.txt (390 lines)
progress.log (63 lines)
FUNCTIONALITY_REPORT.md (this file)
```

**Total Lines of Code:** ~1,200 lines Python

---

**Report End**
