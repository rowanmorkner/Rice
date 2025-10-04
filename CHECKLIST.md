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
