# Water-Opt MVP – Build Checklist

Legend: [ ] = pending, [x] = done

## 0. Repo & env
[x] 0.1 Create repo scaffold exactly as specified; add .gitignore to exclude /data and .env
[x] 0.2 Write requirements.txt and pyproject.toml; add docs/README.md install notes (macOS/Linux PDF deps)
[x] 0.3 Add .env.example with NASS_API_KEY and CIMIS_APP_KEY placeholders

Acceptance:
- Tree matches instructions; `pip install -r requirements.txt` succeeds
- docs/README.md includes any OS package prerequisites for camelot/tabula

## 1. ETL utilities
[x] 1.1 Create etl/utils_pdf.py (camelot/tabula helpers + fallback)
[x] 1.2 Create data/manifest.csv on first run; implement helper to append rows with hash and counts

Acceptance:
- utils functions import without error; manifest appending tested in a tiny script

## 2. AWDB fetcher (FULL)
[x] 2.1 etl/fetch_awdb.py: fetch small set of Sierra SNOTEL stations; SWE daily since 2015
[x] 2.2 Normalize to stage/awdb_swe_daily.parquet (date, station_id, wteq_mm)
[x] 2.3 Derive mart/hydro_scenarios.parquet (monthly dry/median/wet percentiles)

Acceptance:
- Running module writes both parquet files with > 1000 rows and reasonable columns; manifest updated

## 3. Bulletin 120 fetcher (FULL)
[x] 3.1 etl/fetch_b120.py: discover latest PDF on CDEC page and download to raw/b120/
[x] 3.2 Parse forecast summary table (median, p10, p90) → stage/b120_forecast.parquet

Acceptance:
- File exists and non-empty; resilient to minor table variations; manifest updated

## 4. ERS Rice Outlook fetcher (FULL)
[x] 4.1 etl/fetch_ers_rice_outlook.py: find latest PDF/XLSX links, download to raw/ers/
[x] 4.2 Parse CA medium/short-grain price table → stage/ers_prices.parquet

Acceptance:
- Non-empty prices parquet with date, price_usd_cwt; manifest updated

## 5. DWR Crop Map fetcher (FULL)
[x] 5.1 etl/fetch_dwr_cropmap.py: query 2022 rice polygons for Sacramento Valley counties (Butte, Glenn, Colusa, Sutter, Yuba) → stage/dwr_rice_2022.geojson
[x] 5.2 Write mart/rice_polygons_2022.parquet with centroid_x, centroid_y, acres, county

Acceptance:
- GeoJSON exists; parquet has > 1000 rows; manifest updated

## 5B. Stub fetchers (graceful no-op if missing keys)
[x] 5B.1 etl/fetch_nass.py: FULL implementation with API key support (API timeouts noted)
[x] 5B.2 etl/fetch_cimis.py: FULL implementation with API key support for daily ETo
[x] 5B.3 etl/fetch_ssebop.py: stub with TODOs for ET raster workflows

Acceptance:
- Each stub imports without error; returns gracefully if key/data missing

## 6. Orchestrator
[x] 6.1 etl/fetch_all.py CLI: flags --awdb --b120 --ers --dwr --nass --cimis --ssebop --all
[x] 6.2 Idempotent runs; polite user-agent; retries with backoff

Acceptance:
- `python etl/fetch_all.py --ers --awdb --b120 --dwr` completes without exceptions

## 7. Models
[x] 7.1 models/profit.py: compute profit_grow vs profit_fallow + breakeven_water_price_usd_af
[x] 7.2 models/scenarios.py: build_price_bands() and build_hydro_scenarios()

Acceptance:
- Unit tests (next section) pass; functions have docstrings & unit-consistent math

## 8. Tests
[x] 8.1 tests/test_profit.py covers positive delta & breakeven correctness
[x] 8.2 tests/test_etl_basic.py checks presence of key artifacts after ETL

Acceptance:
- `pytest -q` passes

## 9. Streamlit app
[x] 9.1 app/Main.py with tabs: Setup, Hydrology, Markets, Decision, Map, Compliance
[x] 9.2 components/charts.py and map.py implemented with Plotly + Leaflet/Kepler
[x] 9.3 Export CSV/PNG in data/mart/exports/

Acceptance:
- `streamlit run app/Main.py` renders; missing optional data handled gracefully

## 10. Docs
[x] 10.1 docs/data_sources.md with human-readable links + notes
[x] 10.2 docs/assumptions.md (CU default, costs, conveyance, transaction, price band logic)
[x] 10.3 docs/case_study_template.md
[x] 10.4 README usage: `make etl`, `make app`, `.env` notes

Acceptance:
- Docs exist, are concise, and match current code

## 11. Makefile
[x] 11.1 Targets: setup, etl, app, test, clean

Acceptance:
- `make etl` produces all FULL fetcher artifacts; `make app` launches; `make test` passes

## 12. Final verification
[x] 12.1 Confirm required files exist (list them)
[x] 12.2 Summarize deviations (if any) in progress.log

Acceptance:
- All global criteria met; deviations documented

---

# PHASE 2 - Enhancement Checklist

**Status**: Phase 1 Complete (100%) | Phase 2 Not Started
**See**: instructionsPhase2.txt for detailed specifications

---

## PRIORITY 1: Data Quality Improvements

### 13. SSEBop Actual ET Integration ⭐ HIGHEST PRIORITY

**Goal**: Replace default 4.0 af/ac CU with field-specific ET data

[ ] 13.1 Research & Setup
  [ ] 13.1.1 Investigate SSEBop data access options (USGS vs OpenET)
  [ ] 13.1.2 Test download of sample monthly ET raster (1 month)
  [ ] 13.1.3 Add raster processing packages to requirements.txt (rasterstats, rasterio, xarray)
  [ ] 13.1.4 Install GDAL system dependencies (macOS: brew install gdal, Linux: apt-get install gdal-bin)
  [ ] 13.1.5 Verify raster can be read with rasterio in test script

[ ] 13.2 Download Infrastructure
  [ ] 13.2.1 Implement fetch_ssebop_rasters() in etl/fetch_ssebop.py
  [ ] 13.2.2 Add retry logic with tenacity for large file downloads
  [ ] 13.2.3 Store rasters in data/raw/ssebop/ with date naming (YYYYMM.tif)
  [ ] 13.2.4 Add progress bar for multi-file downloads (tqdm)
  [ ] 13.2.5 Test download of 5 months (May-Sep) for 2022

[ ] 13.3 Zonal Statistics Processing
  [ ] 13.3.1 Implement compute_zonal_stats() function
  [ ] 13.3.2 Load rice polygons from mart/rice_polygons_2022.parquet
  [ ] 13.3.3 Perform zonal statistics (mean ET per polygon) using rasterstats
  [ ] 13.3.4 Handle edge cases: polygons outside raster bounds, nodata values
  [ ] 13.3.5 Test on subset of 100 polygons first

[ ] 13.4 Seasonal Aggregation
  [ ] 13.4.1 Implement aggregate_seasonal_et() function
  [ ] 13.4.2 Sum monthly ET (May-Sep) to seasonal total in mm
  [ ] 13.4.3 Convert mm to inches: inches = mm / 25.4
  [ ] 13.4.4 Convert to acre-feet per acre: af_per_ac = (mm × acres × 43560) / (1000 × 325851)
  [ ] 13.4.5 Add data quality flags (complete, partial, interpolated)

[ ] 13.5 Output & Integration
  [ ] 13.5.1 Write mart/rice_et_seasonal_2022.parquet with schema (polygon_id, county, acres, seasonal_et_*)
  [ ] 13.5.2 Update manifest.csv with ET data provenance
  [ ] 13.5.3 Add CLI flag to fetch_all.py: --ssebop (change from stub to full)
  [ ] 13.5.4 Create validate_et_data() function: check mean ET is 3.5-4.5 af/ac
  [ ] 13.5.5 Document any polygons with missing/invalid ET data

[ ] 13.6 Model Integration
  [ ] 13.6.1 Update models/profit.py to accept field_et_df parameter
  [ ] 13.6.2 Modify compare_profit() to look up ET per polygon_id if available
  [ ] 13.6.3 Add fallback to default 4.0 af/ac if ET data missing
  [ ] 13.6.4 Update dashboard Setup tab with toggle: "Use field-specific ET" vs "Use default"
  [ ] 13.6.5 Display ET source in dashboard (SSEBop vs default)

[ ] 13.7 Testing
  [ ] 13.7.1 Write tests/test_ssebop.py: test zonal stats logic
  [ ] 13.7.2 Test ET conversion formulas (mm → af/ac) with known values
  [ ] 13.7.3 Test edge cases: polygon outside raster, all nodata pixels
  [ ] 13.7.4 Validate full pipeline: download → zonal stats → seasonal total
  [ ] 13.7.5 Verify 4,612 polygons have ET values (>90% coverage)

[ ] 13.8 Documentation
  [ ] 13.8.1 Update docs/data_sources.md with SSEBop details (URL, format, resolution)
  [ ] 13.8.2 Update docs/assumptions.md: replace "TODO: SSEBop" with actual implementation
  [ ] 13.8.3 Document ET conversion formulas with examples
  [ ] 13.8.4 Add troubleshooting section for GDAL/rasterio issues
  [ ] 13.8.5 Update PROJECT_STATUS_REPORT.md: mark SSEBop as complete

Acceptance:
- 5 months of ET rasters downloaded (May-Sep)
- Zonal statistics computed for 4,612 rice polygons (>90% success rate)
- Mean seasonal ET is 3.5-4.5 af/ac (validates against literature)
- Parquet output has all required columns with no nulls
- Dashboard displays field-specific ET when available
- All tests pass; manifest updated

---

### 14. NASS QuickStats Price/Yield Integration

**Goal**: Replace ERS stub data with 20+ years of historical prices

[ ] 14.1 API Monitoring
  [ ] 14.1.1 Create automated test script: scripts/test_nass_api.py
  [ ] 14.1.2 Script pings NASS API daily, logs response time
  [ ] 14.1.3 Alert when API response time < 10 seconds (recovered)
  [ ] 14.1.4 Set up cron job or GitHub Actions for daily check

[ ] 14.2 Data Fetching (when API recovers)
  [ ] 14.2.1 Test existing fetch_nass.py functions with API
  [ ] 14.2.2 Fetch historical rice prices (2000-2024): fetch_rice_prices()
  [ ] 14.2.3 Fetch historical yields (2000-2024): fetch_rice_yields()
  [ ] 14.2.4 Fetch county-level data: fetch_rice_by_county()
  [ ] 14.2.5 Verify outputs: stage/nass_rice_prices.parquet, stage/nass_rice_yields.parquet

[ ] 14.3 Data Normalization
  [ ] 14.3.1 Clean NASS data: remove duplicates, handle nulls
  [ ] 14.3.2 Standardize units: prices in $/cwt, yields in cwt/acre
  [ ] 14.3.3 Filter to California medium/short-grain rice only
  [ ] 14.3.4 Aggregate multi-county data if needed
  [ ] 14.3.5 Validate against known NASS statistics (spot check 2020 prices)

[ ] 14.4 Price Bands Integration
  [ ] 14.4.1 Update models/scenarios.py build_price_bands() to use NASS data
  [ ] 14.4.2 Calculate rolling 12-month p10/median/p90 percentiles
  [ ] 14.4.3 Compare new bands to ERS stub bands (should be similar)
  [ ] 14.4.4 Add confidence intervals from historical volatility
  [ ] 14.4.5 Handle years with missing data (interpolation or flags)

[ ] 14.5 Dashboard Integration
  [ ] 14.5.1 Update Markets tab to display NASS price history (20+ years)
  [ ] 14.5.2 Add interactive chart: hover shows year, price, percentile
  [ ] 14.5.3 Display data source: "NASS QuickStats (2000-2024)" vs "ERS stub"
  [ ] 14.5.4 Add county selector: filter to specific counties if desired
  [ ] 14.5.5 Show yield trends alongside price trends

[ ] 14.6 Testing
  [ ] 14.6.1 Update tests/test_etl_basic.py: check NASS data presence
  [ ] 14.6.2 Test price bands with full NASS data (20+ years)
  [ ] 14.6.3 Verify percentiles are reasonable (p10 < median < p90)
  [ ] 14.6.4 Test graceful fallback to ERS stub if NASS unavailable
  [ ] 14.6.5 Check dashboard renders with both NASS and stub data

[ ] 14.7 Documentation
  [ ] 14.7.1 Update docs/data_sources.md: mark NASS as "FULL" implementation
  [ ] 14.7.2 Document NASS API recovery date in progress.log
  [ ] 14.7.3 Add examples of NASS data queries to docs
  [ ] 14.7.4 Update assumptions.md with NASS price band methodology
  [ ] 14.7.5 Remove "stub data" warnings from documentation

Acceptance:
- NASS API responsive (response time < 10s)
- Historical data fetched: 20+ years of prices and yields
- Price bands updated with robust percentiles
- Dashboard displays NASS data with 20+ year history
- All tests pass; no regressions
- Documentation updated

---

### 15. DWR Crop Map Updates (2023/2024)

**Goal**: Integrate latest crop mapping data when released

[ ] 15.1 Data Monitoring
  [ ] 15.1.1 Check https://data.ca.gov/dataset/statewide-crop-mapping quarterly
  [ ] 15.1.2 Look for 2023 and 2024 provisional/final crop maps
  [ ] 15.1.3 Download metadata: verify rice classification codes unchanged
  [ ] 15.1.4 Check file formats: shapefile vs geodatabase vs API

[ ] 15.2 Fetcher Updates
  [ ] 15.2.1 Update SHAPEFILE_URL in fetch_dwr_cropmap.py to 2023/2024 version
  [ ] 15.2.2 Add --year CLI parameter: python -m etl.fetch_dwr_cropmap --year 2023
  [ ] 15.2.3 Update rice class filter if classification changed (verify CLASS2='R')
  [ ] 15.2.4 Test download and processing of new shapefile
  [ ] 15.2.5 Compare 2022 vs 2023 acreage: document changes

[ ] 15.3 Multi-Year Support
  [ ] 15.3.1 Support multiple years in data directory: rice_polygons_2022.parquet, rice_polygons_2023.parquet
  [ ] 15.3.2 Add year selector to dashboard Setup tab
  [ ] 15.3.3 Load appropriate year's polygons based on user selection
  [ ] 15.3.4 Display year in dashboard title: "2023 Rice Fields"
  [ ] 15.3.5 Allow comparison view: 2022 vs 2023 side-by-side

[ ] 15.4 Year-over-Year Analysis
  [ ] 15.4.1 Create analysis script: scripts/compare_years.py
  [ ] 15.4.2 Calculate county-level acreage changes (2022 vs 2023)
  [ ] 15.4.3 Identify new fields (in 2023, not in 2022)
  [ ] 15.4.4 Identify retired fields (in 2022, not in 2023)
  [ ] 15.4.5 Generate summary report: % change per county

[ ] 15.5 Testing
  [ ] 15.5.1 Test with 2023 data: verify 4,000+ polygons (similar to 2022)
  [ ] 15.5.2 Test year selector in dashboard
  [ ] 15.5.3 Test multi-year manifest tracking
  [ ] 15.5.4 Verify backward compatibility: 2022 data still works
  [ ] 15.5.5 Test edge case: year with no data available

[ ] 15.6 Documentation
  [ ] 15.6.1 Document DWR data release schedule (typically fall)
  [ ] 15.6.2 Add instructions for updating to new years
  [ ] 15.6.3 Document acreage changes in progress.log
  [ ] 15.6.4 Update README with multi-year support instructions

Acceptance:
- 2023 (or latest) crop map integrated
- Multi-year support functional in dashboard
- Year-over-year comparison report generated
- All tests pass with new data
- Documentation updated with new year

---

## PRIORITY 2: Model Enhancements

### 16. Partial Fallowing Optimization

**Goal**: Optimize field-by-field decisions using linear programming

[ ] 16.1 Model Design
  [ ] 16.1.1 Design LP formulation: decision variables x_i ∈ {0,1} per field
  [ ] 16.1.2 Define objective function: maximize Σ(x_i × profit_grow_i + (1-x_i) × profit_fallow_i)
  [ ] 16.1.3 Define constraints: water limits, spatial adjacency (optional)
  [ ] 16.1.4 Choose solver: PuLP (simpler) vs scipy.optimize (faster)
  [ ] 16.1.5 Document mathematical formulation in docs/optimization.md

[ ] 16.2 Implementation
  [ ] 16.2.1 Create models/optimize.py module
  [ ] 16.2.2 Implement optimize_partial_fallow() function
  [ ] 16.2.3 Add constraint options: max_transfer_af, adjacency_penalty, min_block_size
  [ ] 16.2.4 Add solver options: time_limit, gap_tolerance
  [ ] 16.2.5 Return DataFrame: polygon_id, decision, profit, constraint_status

[ ] 16.3 Per-Field Profit Calculation
  [ ] 16.3.1 Extend models/profit.py with compute_field_profit() function
  [ ] 16.3.2 Accept field attributes: acres, yield_estimate, et_af_per_ac
  [ ] 16.3.3 Calculate profit_grow and profit_fallow per field
  [ ] 16.3.4 Store in DataFrame: polygon_id, profit_grow, profit_fallow, delta
  [ ] 16.3.5 Handle fields with missing data (use defaults)

[ ] 16.4 Spatial Constraints (Optional)
  [ ] 16.4.1 Load field adjacency from GeoJSON (touch detection with shapely)
  [ ] 16.4.2 Create adjacency matrix: fields[i] touches fields[j]
  [ ] 16.4.3 Add LP constraint: adjacent fields should have same decision (soft constraint)
  [ ] 16.4.4 Weight adjacency penalty vs profit maximization
  [ ] 16.4.5 Test with and without spatial constraints

[ ] 16.5 Dashboard Integration
  [ ] 16.5.1 Add "Optimization" mode toggle to Setup tab (Simple vs Optimized)
  [ ] 16.5.2 Add constraint inputs: max water transfer (af), enforce adjacency (yes/no)
  [ ] 16.5.3 Run optimization on button click: "Optimize Decision"
  [ ] 16.5.4 Display results: % fields grow, % fields fallow, total profit
  [ ] 16.5.5 Update map: color fields by optimized decision

[ ] 16.6 Results Analysis
  [ ] 16.6.1 Compare optimized vs binary decision: profit improvement %
  [ ] 16.6.2 Display optimization statistics: solve time, gap, constraint violations
  [ ] 16.6.3 Show spatial distribution: map of optimized decisions
  [ ] 16.6.4 Export results: data/mart/exports/optimized_decisions_YYYYMMDD.csv
  [ ] 16.6.5 Generate summary report: fields by decision, total water transferred

[ ] 16.7 Performance Testing
  [ ] 16.7.1 Test optimization with 4,612 fields (full dataset)
  [ ] 16.7.2 Measure solve time: target <10 seconds
  [ ] 16.7.3 Test with larger constraint sets (10,000+ fields if needed)
  [ ] 16.7.4 Profile bottlenecks: solver vs data prep
  [ ] 16.7.5 Add caching: save/load optimization results

[ ] 16.8 Testing
  [ ] 16.8.1 Write tests/test_optimize.py
  [ ] 16.8.2 Test LP solver correctness: simple 10-field example with known optimal
  [ ] 16.8.3 Test constraint handling: verify max_transfer respected
  [ ] 16.8.4 Test edge cases: all fields grow, all fields fallow, infeasible constraints
  [ ] 16.8.5 Test graceful failure: timeout, no solution found

[ ] 16.9 Documentation
  [ ] 16.9.1 Create docs/optimization.md with mathematical formulation
  [ ] 16.9.2 Document constraints and their effects
  [ ] 16.9.3 Add usage examples with screenshots
  [ ] 16.9.4 Document solver choice and performance characteristics
  [ ] 16.9.5 Update assumptions.md with optimization methodology

Acceptance:
- Optimization solves 4,612 fields in <10 seconds
- Profit improvement documented vs binary decision (target: ≥5%)
- All constraints respected (no violations)
- Dashboard integration functional
- Tests pass (correctness, edge cases)
- Documentation complete

---

### 17. Risk Analysis (Monte Carlo Simulation)

**Goal**: Quantify decision confidence with uncertainty analysis

[ ] 17.1 Probability Distribution Design
  [ ] 17.1.1 Define distributions for uncertain parameters:
    - Rice yield: normal(mean=historical_avg, std=historical_std)
    - Rice price: normal(mean=current, std=from_price_bands)
    - Water price: uniform(min=user_low, max=user_high)
    - Consumptive use: normal(mean=4.0, std=0.3) or use ET data
  [ ] 17.1.2 Research historical volatility: NASS data for CA rice
  [ ] 17.1.3 Document distribution choices in docs/assumptions.md
  [ ] 17.1.4 Add user controls for distribution parameters (mean, std, min, max)

[ ] 17.2 Implementation
  [ ] 17.2.1 Create models/risk.py module
  [ ] 17.2.2 Implement monte_carlo_analysis() function
  [ ] 17.2.3 Use numpy.random for sampling (set seed for reproducibility)
  [ ] 17.2.4 Run 10,000 simulations (configurable)
  [ ] 17.2.5 Store results: profit_grow_samples, profit_fallow_samples arrays

[ ] 17.3 Statistical Metrics
  [ ] 17.3.1 Calculate summary statistics: mean, std, min, max
  [ ] 17.3.2 Calculate percentiles: p10, p25, p50, p75, p90
  [ ] 17.3.3 Calculate probability: P(profit_grow > profit_fallow)
  [ ] 17.3.4 Calculate Value-at-Risk (VaR): 5th percentile profit
  [ ] 17.3.5 Calculate expected value: mean profit weighted by probability

[ ] 17.4 Visualization
  [ ] 17.4.1 Add "Risk Analysis" section to Decision tab
  [ ] 17.4.2 Plot profit distributions: histograms for grow vs fallow (Plotly)
  [ ] 17.4.3 Plot probability of success: bar chart or gauge
  [ ] 17.4.4 Plot risk vs return: scatter plot (mean profit vs std dev)
  [ ] 17.4.5 Add confidence intervals: shaded regions on charts

[ ] 17.5 Dashboard Integration
  [ ] 17.5.1 Add "Run Risk Analysis" button in Decision tab
  [ ] 17.5.2 Display metrics: mean profit, std dev, P(grow better), VaR
  [ ] 17.5.3 Add interpretation guide: "High confidence" if P > 0.8
  [ ] 17.5.4 Show distribution of breakeven water prices
  [ ] 17.5.5 Export risk analysis results to CSV

[ ] 17.6 Sensitivity to Distribution Choices
  [ ] 17.6.1 Test with different yield distributions (narrow vs wide std)
  [ ] 17.6.2 Test with different price distributions
  [ ] 17.6.3 Compare normal vs log-normal distributions
  [ ] 17.6.4 Document sensitivity: how much results change
  [ ] 17.6.5 Add "conservative" vs "optimistic" presets

[ ] 17.7 Performance Optimization
  [ ] 17.7.1 Profile simulation speed: target 10,000 runs in <5 seconds
  [ ] 17.7.2 Vectorize profit calculations (numpy arrays, not loops)
  [ ] 17.7.3 Test with 100,000 simulations (for publication-quality)
  [ ] 17.7.4 Add progress bar for long simulations (tqdm)
  [ ] 17.7.5 Cache results: avoid re-running with same parameters

[ ] 17.8 Testing
  [ ] 17.8.1 Write tests/test_risk.py
  [ ] 17.8.2 Test sampling: verify distributions have correct mean/std
  [ ] 17.8.3 Test metrics: verify percentiles calculated correctly
  [ ] 17.8.4 Test edge cases: zero variance, negative prices (should clip)
  [ ] 17.8.5 Test reproducibility: same seed → same results

[ ] 17.9 Documentation
  [ ] 17.9.1 Create docs/risk_analysis.md with methodology
  [ ] 17.9.2 Document probability distributions and sources
  [ ] 17.9.3 Explain VaR and other risk metrics in plain language
  [ ] 17.9.4 Add interpretation guide: when to trust risk analysis
  [ ] 17.9.5 Document limitations: assumes independence, normal distributions

Acceptance:
- Monte Carlo runs 10,000 simulations in <5 seconds
- Distributions are reasonable (no negative yields/prices)
- Metrics calculated correctly (verified against toy examples)
- Dashboard displays risk visualizations clearly
- Tests pass; documentation explains methodology

---

### 18. Multi-Year Planning (OPTIONAL - Phase 3 candidate)

**Goal**: Optimize decisions across multiple years with water banking

[ ] 18.1 Model Design
  [ ] 18.1.1 Research water banking rules in CA (carryover limits, storage costs)
  [ ] 18.1.2 Design state space: (year, stored_water, allocation, prices)
  [ ] 18.1.3 Design action space: grow, fallow_and_store, fallow_and_sell
  [ ] 18.1.4 Define transition dynamics: stored_water[t+1] = stored_water[t] + saved - sold
  [ ] 18.1.5 Document formulation in docs/multiyear_planning.md

[ ] 18.2 Implementation (if prioritized)
  [ ] 18.2.1 Create models/multiyear.py module
  [ ] 18.2.2 Implement optimize_multiyear() function (dynamic programming)
  [ ] 18.2.3 Add discount rate parameter (default 5%)
  [ ] 18.2.4 Calculate NPV across planning horizon
  [ ] 18.2.5 Return optimal policy: action per year

[ ] 18.3 Testing & Documentation
  [ ] 18.3.1 Test with simple 3-year scenario
  [ ] 18.3.2 Verify NPV calculation correctness
  [ ] 18.3.3 Document assumptions about future prices/allocations
  [ ] 18.3.4 Add dashboard integration (if feasible)

Acceptance:
- Multi-year model implemented and tested
- Policy table generated for 3-5 year horizon
- Documentation explains methodology and limitations

**Note**: This is marked OPTIONAL - assess value vs complexity before implementing

---

## PRIORITY 3: User Experience Enhancements

### 19. Field-Level Map Interaction

**Goal**: Click individual fields to see field-specific analysis

[ ] 19.1 Plotly Click Events
  [ ] 19.1.1 Research Plotly click events for scattermapbox
  [ ] 19.1.2 Implement click handler in app/components/map.py
  [ ] 19.1.3 Capture clicked point data: polygon_id, lat, lon
  [ ] 19.1.4 Store clicked_field_id in st.session_state
  [ ] 19.1.5 Test click detection: verify correct field identified

[ ] 19.2 Field Detail Sidebar
  [ ] 19.2.1 Create app/components/field_detail.py module
  [ ] 19.2.2 Add sidebar to Map tab: st.sidebar (conditional on field clicked)
  [ ] 19.2.3 Display field attributes: acres, county, polygon_id
  [ ] 19.2.4 Display ET data: seasonal_et_af_per_ac (if available)
  [ ] 19.2.5 Display profit comparison: grow vs fallow for this field

[ ] 19.3 Per-Field Parameters
  [ ] 19.3.1 Add "Override Parameters" expander in sidebar
  [ ] 19.3.2 Allow user to adjust: yield, rice price, water price for this field
  [ ] 19.3.3 Recalculate profit with field-specific parameters
  [ ] 19.3.4 Show comparison: default params vs overridden params
  [ ] 19.3.5 Store overrides in session state: field_overrides dict

[ ] 19.4 Field-Level Decision
  [ ] 19.4.1 Display recommended decision for clicked field
  [ ] 19.4.2 Show sensitivity: how decision changes with ±10% on key params
  [ ] 19.4.3 Display breakeven water price for this field
  [ ] 19.4.4 Show field on map: highlight with different color/size
  [ ] 19.4.5 Add "Apply to Similar Fields" button (same county, similar size)

[ ] 19.5 Batch Operations
  [ ] 19.5.1 Add multi-select mode: click multiple fields (shift+click)
  [ ] 19.5.2 Display selected field count in sidebar
  [ ] 19.5.3 Show aggregate stats: total acres, average ET, total profit
  [ ] 19.5.4 Allow batch parameter override: apply same changes to all selected
  [ ] 19.5.5 Export selected fields to CSV

[ ] 19.6 Performance Optimization
  [ ] 19.6.1 Test with full 4,612 fields: measure click response time
  [ ] 19.6.2 Add spatial index: speed up "find field by lat/lon"
  [ ] 19.6.3 Limit displayed fields: show only visible map region (viewport filtering)
  [ ] 19.6.4 Add caching: cache profit calculations per field
  [ ] 19.6.5 Test on slower connections: ensure <2 second click response

[ ] 19.7 Testing
  [ ] 19.7.1 Test click detection accuracy: verify correct field selected
  [ ] 19.7.2 Test parameter overrides: verify profit recalculates correctly
  [ ] 19.7.3 Test multi-select: verify all selected fields tracked
  [ ] 19.7.4 Test edge cases: click outside field boundaries, click on water
  [ ] 19.7.5 Test mobile/tablet: touch events work correctly

[ ] 19.8 Documentation
  [ ] 19.8.1 Add "How to Use Field Interaction" section to README
  [ ] 19.8.2 Create animated GIF or video demo
  [ ] 19.8.3 Document field override use cases
  [ ] 19.8.4 Add troubleshooting: "Click not working" scenarios

Acceptance:
- Click field → sidebar appears with field details
- Parameter overrides functional and recalculate instantly
- Multi-select and batch operations work
- Response time <2 seconds on full dataset
- Documentation with demo video

---

### 20. Historical Backtest Tool

**Goal**: Validate model against actual historical outcomes

[ ] 20.1 Historical Data Collection
  [ ] 20.1.1 Identify test years: 2021 (drought), 2019 (normal), 2017 (wet)
  [ ] 20.1.2 Gather historical data: allocation %, rice prices, yields
  [ ] 20.1.3 Research actual grower decisions (surveys, extension reports)
  [ ] 20.1.4 Create data/backtest/ directory with historical scenarios
  [ ] 20.1.5 Format as JSON: {year, allocation, prices, yields, decisions}

[ ] 20.2 Backtest Module
  [ ] 20.2.1 Create app/backtest.py module
  [ ] 20.2.2 Implement run_backtest() function
  [ ] 20.2.3 Load historical scenario by year
  [ ] 20.2.4 Run model with historical parameters
  [ ] 20.2.5 Compare: model recommendation vs actual decision

[ ] 20.3 Comparison Metrics
  [ ] 20.3.1 Calculate model accuracy: % fields with correct recommendation
  [ ] 20.3.2 Calculate profit difference: actual profit vs model-predicted profit
  [ ] 20.3.3 Calculate calibration error: RMSE, MAE on profit predictions
  [ ] 20.3.4 Identify systematic biases: model always too optimistic/pessimistic?
  [ ] 20.3.5 Document model performance per year

[ ] 20.4 Dashboard Integration (New Tab)
  [ ] 20.4.1 Add "Backtest" tab to Streamlit app
  [ ] 20.4.2 Add year selector dropdown: 2021, 2019, 2017, etc.
  [ ] 20.4.3 Display historical scenario: allocation, prices, yields
  [ ] 20.4.4 Show model recommendation vs actual decision (side-by-side table)
  [ ] 20.4.5 Display comparison metrics: accuracy, profit difference

[ ] 20.5 Calibration Adjustments
  [ ] 20.5.1 Implement suggest_adjustments() function
  [ ] 20.5.2 If model consistently wrong, suggest parameter changes
  [ ] 20.5.3 Examples: "Lower default CU by 0.3 af/ac" or "Increase transaction cost"
  [ ] 20.5.4 Display suggested adjustments in dashboard
  [ ] 20.5.5 Allow user to apply adjustments and re-run backtest

[ ] 20.6 Report Generation
  [ ] 20.6.1 Implement generate_backtest_report() function
  [ ] 20.6.2 Use docs/case_study_template.md as structure
  [ ] 20.6.3 Populate template with backtest results
  [ ] 20.6.4 Export as markdown or PDF
  [ ] 20.6.5 Save to data/mart/exports/backtest_report_{year}.md

[ ] 20.7 Testing
  [ ] 20.7.1 Test with known 2021 drought scenario
  [ ] 20.7.2 Verify metrics calculated correctly
  [ ] 20.7.3 Test calibration suggestions: reasonable adjustments
  [ ] 20.7.4 Test report generation: complete and formatted correctly
  [ ] 20.7.5 Test with hypothetical scenario (made-up data)

[ ] 20.8 Documentation
  [ ] 20.8.1 Document backtest methodology in docs/backtest.md
  [ ] 20.8.2 Explain how to add new historical scenarios
  [ ] 20.8.3 Document interpretation of calibration metrics
  [ ] 20.8.4 Add example backtest report to docs/
  [ ] 20.8.5 Update README with backtest instructions

Acceptance:
- Backtest tool runs for ≥2 historical years
- Model performance metrics calculated and displayed
- Calibration suggestions generated
- Report export functional
- Documentation complete

---

### 21. Mobile-Responsive Layout

**Goal**: Usable on tablets for field access

[ ] 21.1 Responsive Design Testing
  [ ] 21.1.1 Test dashboard on iPad (1024x768)
  [ ] 21.1.2 Test on Android tablet
  [ ] 21.1.3 Test on large phone (iPhone Pro Max, etc.)
  [ ] 21.1.4 Document breakpoints where layout breaks
  [ ] 21.1.5 Capture screenshots of issues

[ ] 21.2 Layout Adjustments
  [ ] 21.2.1 Replace fixed-width columns with st.columns([1, 1]) responsive ratios
  [ ] 21.2.2 Hide complex charts on mobile: use st.sidebar.checkbox("Show advanced charts")
  [ ] 21.2.3 Stack sections vertically on narrow screens
  [ ] 21.2.4 Increase touch target sizes: larger buttons, wider sliders
  [ ] 21.2.5 Test font sizes: ensure readable on small screens

[ ] 21.3 Mobile-Specific Features
  [ ] 21.3.1 Add viewport meta tag (if Streamlit allows custom HTML)
  [ ] 21.3.2 Create simplified "Mobile View" toggle in sidebar
  [ ] 21.3.3 Mobile view: hide Hydrology/Markets tabs, focus on Decision
  [ ] 21.3.4 Mobile view: simplified map (fewer fields, larger markers)
  [ ] 21.3.5 Test offline functionality: cached data for field use

[ ] 21.4 Touch Interaction
  [ ] 21.4.1 Test map touch events: pinch-zoom, pan
  [ ] 21.4.2 Test slider touch: ensure smooth dragging
  [ ] 21.4.3 Test dropdown menus: ensure large enough to tap
  [ ] 21.4.4 Test multi-touch gestures: two-finger zoom on map
  [ ] 21.4.5 Add haptic feedback hints (if possible)

[ ] 21.5 Performance on Mobile
  [ ] 21.5.1 Test load time on mobile network (4G/5G)
  [ ] 21.5.2 Optimize image sizes: compress logos, reduce map complexity
  [ ] 21.5.3 Lazy-load charts: only load when tab opened
  [ ] 21.5.4 Test battery usage: ensure not draining quickly
  [ ] 21.5.5 Profile memory usage: ensure doesn't crash on low-end tablets

[ ] 21.6 Testing
  [ ] 21.6.1 Test on real devices (borrow iPads/tablets)
  [ ] 21.6.2 Test landscape vs portrait orientation
  [ ] 21.6.3 Test with different screen sizes: 7", 10", 12" tablets
  [ ] 21.6.4 Test accessibility: font scaling, high contrast mode
  [ ] 21.6.5 Test in field conditions: bright sunlight, glare

[ ] 21.7 Documentation
  [ ] 21.7.1 Document supported devices: "Optimized for iPad 10.2" and above"
  [ ] 21.7.2 Add mobile usage guide to README
  [ ] 21.7.3 Document known limitations on mobile
  [ ] 21.7.4 Add troubleshooting: "Dashboard slow on mobile"

Acceptance:
- Dashboard usable on 1024x768 tablet
- All core features accessible via touch
- Load time <5 seconds on mobile network
- No layout breaks or overlapping elements
- Documentation updated with mobile guidance

---

## PRIORITY 4: Data Integrations

### 22. Real-Time Water Market Data (OPTIONAL)

**Goal**: Integrate live water prices if data source available

[ ] 22.1 Data Source Research
  [ ] 22.1.1 Research CA Water Exchange: check if public API exists
  [ ] 22.1.2 Research local irrigation districts: check for posted prices
  [ ] 22.1.3 Research academic sources: PPIC, UC Davis water market data
  [ ] 22.1.4 Evaluate feasibility: is web scraping legal/ethical?
  [ ] 22.1.5 Document data source options and limitations

[ ] 22.2 Implementation (if feasible)
  [ ] 22.2.1 Create etl/fetch_water_prices.py
  [ ] 22.2.2 Implement scraper or API client
  [ ] 22.2.3 Store in stage/water_market_prices.parquet
  [ ] 22.2.4 Schema: date, region, price_usd_af, volume_af, buyer, seller (if available)
  [ ] 22.2.5 Add to fetch_all.py: --water-prices flag

[ ] 22.3 Manual Input Alternative
  [ ] 22.3.1 Add "Update Water Price" admin interface in dashboard
  [ ] 22.3.2 Allow user to enter: date, region, price
  [ ] 22.3.3 Store in data/manual/water_prices.csv
  [ ] 22.3.4 Merge with automated data (if any)
  [ ] 22.3.5 Display data source: "Manual" vs "Automated"

[ ] 22.4 Dashboard Integration
  [ ] 22.4.1 Display latest water market price in Setup tab
  [ ] 22.4.2 Show price trend: chart of last 30 days
  [ ] 22.4.3 Add alert: "Price up 20% in last week"
  [ ] 22.4.4 Update default water price from market data
  [ ] 22.4.5 Allow user to override: "Use market price" vs "Use custom price"

[ ] 22.5 Testing & Documentation
  [ ] 22.5.1 Test data fetching (if automated)
  [ ] 22.5.2 Test manual input interface
  [ ] 22.5.3 Document data sources and limitations
  [ ] 22.5.4 Add disclaimer: "Market prices are estimates"

Acceptance:
- Water price data integrated (manual or automated)
- Dashboard displays latest market price
- User can choose market vs custom price
- Documentation explains data source and limitations

**Note**: Marked OPTIONAL - implement only if reliable data source found

---

### 23. District-Specific Rules Database

**Goal**: Automate compliance checks per irrigation district

[ ] 23.1 Data Collection
  [ ] 23.1.1 Identify major districts in Sacramento Valley: GCID, RD108, others
  [ ] 23.1.2 Research transfer policies: hearing thresholds, conveyance loss, fees
  [ ] 23.1.3 Compile from district websites, water code, legal sources
  [ ] 23.1.4 Create data/districts_rules.json template
  [ ] 23.1.5 Populate with ≥5 major districts

[ ] 23.2 Data Structure
  [ ] 23.2.1 Define JSON schema: district name, allows_transfers, hearing_threshold_af, etc.
  [ ] 23.2.2 Add fields: conveyance_loss_pct, transaction_fee_usd, contact info
  [ ] 23.2.3 Add legal references: water_code_section, permit_requirements
  [ ] 23.2.4 Validate JSON schema with jsonschema package
  [ ] 23.2.5 Document schema in docs/district_rules_schema.md

[ ] 23.3 Dashboard Integration
  [ ] 23.3.1 Add district selector dropdown in Setup tab
  [ ] 23.3.2 Load district rules from JSON on selection
  [ ] 23.3.3 Auto-populate: conveyance loss, transaction fee
  [ ] 23.3.4 Display: hearing threshold, contact info
  [ ] 23.3.5 Show warning if transfer volume > hearing threshold

[ ] 23.4 Compliance Checks
  [ ] 23.4.1 Implement check_compliance() function in models/compliance.py
  [ ] 23.4.2 Check: transfer volume < hearing threshold (or warn)
  [ ] 23.4.3 Check: district allows transfers (if not, block calculation)
  [ ] 23.4.4 Check: "new water" requirement met (reduced CU documented)
  [ ] 23.4.5 Display compliance status: ✅ Pass, ⚠️ Warning, ❌ Fail

[ ] 23.5 Compliance Tab Enhancement
  [ ] 23.5.1 Update Compliance tab with district-specific info
  [ ] 23.5.2 Display applicable water code sections
  [ ] 23.5.3 Display required documentation for transfer
  [ ] 23.5.4 Add checklist: "Consult district manager", "File petition", etc.
  [ ] 23.5.5 Link to district website and contact info

[ ] 23.6 Expansion & Maintenance
  [ ] 23.6.1 Add more districts over time (target: 10+ districts)
  [ ] 23.6.2 Create update process: verify rules annually
  [ ] 23.6.3 Add "Request District" form: users can request new districts
  [ ] 23.6.4 Version control districts_rules.json: track changes
  [ ] 23.6.5 Add last_updated date per district

[ ] 23.7 Legal Review
  [ ] 23.7.1 Consult water rights attorney: verify accuracy of rules
  [ ] 23.7.2 Add disclaimer: "Informational only, not legal advice"
  [ ] 23.7.3 Document sources for each rule (website URLs, code citations)
  [ ] 23.7.4 Add "Verify with district" warning on compliance checks
  [ ] 23.7.5 Consider liability: ensure tool doesn't give false confidence

[ ] 23.8 Testing & Documentation
  [ ] 23.8.1 Test district selector: verify rules load correctly
  [ ] 23.8.2 Test compliance checks: verify warnings display correctly
  [ ] 23.8.3 Document district rule sources in docs/district_rules_sources.md
  [ ] 23.8.4 Add instructions: "How to add a new district"
  [ ] 23.8.5 Update README with district integration features

Acceptance:
- District rules database with ≥5 districts
- District selector functional in dashboard
- Compliance checks display warnings correctly
- Legal review completed (or disclaimer added)
- Documentation complete with sources

---

### 24. Export and Integration Features

**Goal**: Professional reports and email alerts

[ ] 24.1 PDF Report Generation
  [ ] 24.1.1 Research PDF library: reportlab vs weasyprint
  [ ] 24.1.2 Create app/components/export.py module
  [ ] 24.1.3 Design report layout: logo, sections, charts
  [ ] 24.1.4 Implement generate_pdf_report() function
  [ ] 24.1.5 Include sections: executive summary, parameters, profit comparison, sensitivity, compliance

[ ] 24.2 Report Content
  [ ] 24.2.1 Executive summary: recommendation + key metrics
  [ ] 24.2.2 Parameter assumptions table: all inputs with values
  [ ] 24.2.3 Profit comparison: grow vs fallow with charts
  [ ] 24.2.4 Sensitivity analysis: tornado chart embedded
  [ ] 24.2.5 Compliance notes: district rules + disclaimers
  [ ] 24.2.6 Data sources: footnote with all data sources used
  [ ] 24.2.7 Footer: "Generated by Water-Opt v2.0 on YYYY-MM-DD"

[ ] 24.3 Dashboard Integration
  [ ] 24.3.1 Add "Generate PDF Report" button in Decision tab
  [ ] 24.3.2 Show progress: "Generating report..."
  [ ] 24.3.3 Save to data/mart/exports/report_{YYYYMMDD}.pdf
  [ ] 24.3.4 Provide download link in dashboard
  [ ] 24.3.5 Preview report: show first page thumbnail

[ ] 24.4 Email Alerts (Optional)
  [ ] 24.4.1 Add email configuration to .env: SMTP_HOST, SMTP_USER, SMTP_PASS
  [ ] 24.4.2 Create notifications/ module with send_email() function
  [ ] 24.4.3 Define alert triggers: breakeven change >10%, allocation drops below X%
  [ ] 24.4.4 Implement check_alerts() function: runs periodically
  [ ] 24.4.5 Send email with summary + link to dashboard

[ ] 24.5 Email Content
  [ ] 24.5.1 Subject: "Water-Opt Alert: [Trigger Event]"
  [ ] 24.5.2 Body: Plain text summary of alert
  [ ] 24.5.3 HTML version: formatted with charts (optional)
  [ ] 24.5.4 Attachment: PDF report (optional)
  [ ] 24.5.5 Footer: unsubscribe link, contact info

[ ] 24.6 Scheduling
  [ ] 24.6.1 Research scheduling options: cron, GitHub Actions, or manual
  [ ] 24.6.2 Create scripts/send_alerts.py: standalone alert checker
  [ ] 24.6.3 Run weekly: check for alert conditions
  [ ] 24.6.4 Log alert history: alerts_sent.csv
  [ ] 24.6.5 Dashboard: display last alert date

[ ] 24.7 Testing
  [ ] 24.7.1 Test PDF generation: verify layout on different systems
  [ ] 24.7.2 Test chart embedding: ensure charts render correctly
  [ ] 24.7.3 Test email sending: send test email to developer
  [ ] 24.7.4 Test alert triggers: manually set conditions
  [ ] 24.7.5 Test with no SMTP config: ensure graceful failure

[ ] 24.8 Documentation
  [ ] 24.8.1 Document PDF report contents in README
  [ ] 24.8.2 Document email alert setup in docs/alerts.md
  [ ] 24.8.3 Add examples: sample PDF report, sample email
  [ ] 24.8.4 Document privacy: "Emails sent from local machine only"
  [ ] 24.8.5 Add troubleshooting: SMTP connection issues

Acceptance:
- PDF report generation functional
- Report includes all required sections with charts
- Email alerts functional (if implemented)
- Alert triggers configurable
- Documentation complete with examples

---

## Phase 2 Final Steps

### 25. Integration Testing

**Goal**: Ensure all Phase 2 features work together

[ ] 25.1 Regression Testing
  [ ] 25.1.1 Run all Phase 1 tests: verify 30/30 still pass
  [ ] 25.1.2 Test all Phase 1 features: no functionality broken
  [ ] 25.1.3 Test backward compatibility: Phase 1 data still loads
  [ ] 25.1.4 Test with missing Phase 2 data: graceful degradation
  [ ] 25.1.5 Fix any regressions immediately

[ ] 25.2 End-to-End Testing
  [ ] 25.2.1 Test complete workflow: ETL → model → dashboard → export
  [ ] 25.2.2 Test with fresh data: run make etl from scratch
  [ ] 25.2.3 Test optimization + risk analysis together
  [ ] 25.2.4 Test field interaction + PDF export
  [ ] 25.2.5 Test on clean machine: verify no missing dependencies

[ ] 25.3 Performance Testing
  [ ] 25.3.1 Measure dashboard load time: target <3 seconds
  [ ] 25.3.2 Measure optimization solve time: target <10 seconds
  [ ] 25.3.3 Measure risk analysis time: target <5 seconds for 10K sims
  [ ] 25.3.4 Measure PDF generation time: target <10 seconds
  [ ] 25.3.5 Profile bottlenecks: optimize if targets not met

[ ] 25.4 User Acceptance Testing
  [ ] 25.4.1 Recruit 2-3 test users (growers, consultants, students)
  [ ] 25.4.2 Provide test scenarios and tasks
  [ ] 25.4.3 Collect feedback: usability, clarity, bugs
  [ ] 25.4.4 Prioritize feedback: must-fix vs nice-to-have
  [ ] 25.4.5 Implement critical fixes

[ ] 25.5 Documentation Review
  [ ] 25.5.1 Review all docs: README, assumptions, data_sources, etc.
  [ ] 25.5.2 Verify Phase 2 features documented
  [ ] 25.5.3 Update screenshots/videos if needed
  [ ] 25.5.4 Check for outdated info: remove Phase 1 TODOs
  [ ] 25.5.5 Add Phase 2 changelog to docs/

Acceptance:
- All Phase 1 tests still pass (30/30)
- Phase 2 tests pass (target: 20+ new tests)
- Performance targets met
- User feedback addressed
- Documentation complete and accurate

---

### 26. Deployment and Release

**Goal**: Ship Phase 2 to production

[ ] 26.1 Version Update
  [ ] 26.1.1 Update version in pyproject.toml: 1.0 → 2.0
  [ ] 26.1.2 Update version in app/Main.py title
  [ ] 26.1.3 Update version in docs/README.md
  [ ] 26.1.4 Create CHANGELOG.md with Phase 2 changes
  [ ] 26.1.5 Update PROJECT_STATUS_REPORT.md

[ ] 26.2 Release Notes
  [ ] 26.2.1 Write docs/RELEASE_NOTES_v2.0.md
  [ ] 26.2.2 Summarize new features: SSEBop, optimization, risk analysis, etc.
  [ ] 26.2.3 Document breaking changes (if any)
  [ ] 26.2.4 Document upgrade path from v1.0
  [ ] 26.2.5 Add migration guide if needed

[ ] 26.3 Git Tagging
  [ ] 26.3.1 Commit all Phase 2 changes: git add -A && git commit
  [ ] 26.3.2 Create annotated tag: git tag -a v2.0 -m "Phase 2 release"
  [ ] 26.3.3 Push to GitHub: git push origin main --tags
  [ ] 26.3.4 Create GitHub release: add release notes, attach assets (if any)
  [ ] 26.3.5 Verify release page: https://github.com/rowanmorkner/Rice/releases/tag/v2.0

[ ] 26.4 Communication
  [ ] 26.4.1 Announce Phase 2 completion internally
  [ ] 26.4.2 Notify test users: "Phase 2 is live, please try it"
  [ ] 26.4.3 Post on social media (if applicable): LinkedIn, Twitter
  [ ] 26.4.4 Update project website (if exists)
  [ ] 26.4.5 Consider blog post: "What's New in Water-Opt v2.0"

[ ] 26.5 Monitoring
  [ ] 26.5.1 Monitor GitHub issues: watch for bug reports
  [ ] 26.5.2 Track usage: add analytics (optional, privacy-respecting)
  [ ] 26.5.3 Collect feedback: create survey or feedback form
  [ ] 26.5.4 Plan Phase 3: based on user feedback and priorities
  [ ] 26.5.5 Update roadmap: mark Phase 2 complete, plan Phase 3

Acceptance:
- Version 2.0 tagged and released on GitHub
- Release notes published
- Communication sent to stakeholders
- Monitoring in place for issues
- Phase 3 roadmap drafted

---

## Phase 2 Summary

**Total Tasks**: ~200 individual tasks across 14 major features
**Estimated Timeline**: 3-6 months depending on priorities and resources
**Key Milestones**:
1. SSEBop ET integration (Priority 1.1) - Month 1-2
2. NASS data integration (Priority 1.2) - When API recovers
3. Partial fallowing optimization (Priority 2.1) - Month 3-4
4. Risk analysis (Priority 2.3) - Month 4-5
5. UX enhancements (Priority 3) - Month 5-6
6. Testing and deployment (Tasks 25-26) - Month 6

**Next Steps**:
1. Review this checklist with stakeholders
2. Prioritize top 3-5 features
3. Update CHECKLIST_PHASE2.md with selected priorities only
4. Create project timeline with milestones
5. Begin with highest priority: SSEBop ET integration
