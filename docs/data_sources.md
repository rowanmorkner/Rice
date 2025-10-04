# Data Sources

This document provides human-readable descriptions and links for all data sources used in Water-Opt MVP.

---

## 1. NRCS AWDB (Air-Water Database) - SNOTEL

**Purpose**: Snow water equivalent (SWE) data for hydrology scenarios

**Type**: REST JSON API

**Endpoint**: https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data

**Documentation**: https://www.nrcs.usda.gov/wps/portal/wcc/home/dataAccessHelp/webService/

**API Key**: Not required

**Data Retrieved**:
- Daily SWE measurements from 12 Sierra Nevada SNOTEL stations
- Date range: 2015-present
- Used to build dry/median/wet hydrology scenarios

**Notes**:
- Uses v1 API (instructions mentioned v3 but it doesn't exist)
- Station IDs verified as active CA SNOTEL stations
- Data normalized to stage/awdb_swe_daily.parquet

**Implementation**: `etl/fetch_awdb.py`

---

## 2. CA DWR Bulletin 120

**Purpose**: Water supply forecasts for California basins

**Type**: PDF download from CDEC website

**URL**: https://cdec.water.ca.gov/snow/bulletin120/

**Documentation**: https://cdec.water.ca.gov/snow/bulletin120/

**API Key**: Not required

**Data Retrieved**:
- Basin-level water supply forecasts (median, p10, p90)
- Latest bulletin (published monthly during snow season)
- 36 California basins

**Notes**:
- Uses camelot-py (stream flavor) for PDF table extraction
- Forecast table typically on pages 3-5
- Published monthly during snow season (Dec-May)

**Implementation**: `etl/fetch_b120.py`

---

## 3. USDA ERS Rice Outlook

**Purpose**: California rice market price data

**Type**: PDF/XLSX narrative reports

**URL**: https://www.ers.usda.gov/publications/

**Search**: "Rice Outlook"

**API Key**: Not required

**Data Retrieved**:
- California medium-grain and short-grain price estimates
- Monthly outlook reports

**Notes**:
- **MVP Limitation**: ERS Rice Outlook PDFs contain limited tabular price data
- Current implementation creates stub data with estimates
- **Recommendation**: For production use, integrate NASS QuickStats API for actual market prices

**Implementation**: `etl/fetch_ers_rice_outlook.py`

---

## 4. USDA NASS QuickStats

**Purpose**: Rice yields, prices, and production by county

**Type**: REST JSON API

**Endpoint**: http://quickstats.nass.usda.gov/api/api_GET/

**Documentation**: https://quickstats.nass.usda.gov/api

**API Key**: **Required** - Register at https://quickstats.nass.usda.gov/api

**Data Retrieved**:
- Rice yields by county (cwt/acre)
- Rice prices ($/cwt)
- Historical production data

**Notes**:
- **Known Issue**: NASS API experiencing severe timeouts (>90 seconds) as of Oct 2025
- Full implementation complete and ready when API recovers
- Includes graceful error handling for API failures

**Implementation**: `etl/fetch_nass.py`

**API Key Configuration**: Set `NASS_API_KEY` in `.env`

---

## 5. USDA AMS MyMarketNews (Optional)

**Purpose**: Weekly market context for rice prices

**Type**: REST JSON API

**Endpoint**: https://mymarketnews.ams.usda.gov/mymarketnews-api

**Documentation**: https://mymarketnews.ams.usda.gov/

**API Key**: Not required for public data

**Notes**:
- Optional data source not yet implemented in MVP
- Could provide additional market context for price forecasts

---

## 6. CA DWR Statewide Crop Mapping

**Purpose**: Rice field polygons and acreage

**Type**: Shapefile download (ArcGIS REST available but not used)

**URL**: https://data.ca.gov/dataset/statewide-crop-mapping

**Direct Download**: https://data.cnra.ca.gov/dataset/6c3d65e3-35bb-49e1-a51e-49d5a2cf09a9/resource/b92e0daf-6e2e-4b5c-a112-09474138d1cd/download/i15_crop_mapping_2022_shp.zip

**Documentation**: https://data.ca.gov/dataset/statewide-crop-mapping

**API Key**: Not required

**Data Retrieved**:
- 2022 rice polygons for Sacramento Valley counties
- Counties: Butte, Glenn, Colusa, Sutter, Yuba
- 4,612 polygons covering 212,597 acres
- CLASS2='R' identifies rice in DWR classification

**Notes**:
- Uses shapefile download instead of ArcGIS REST for reliability
- Large file (~171 MB compressed, ~500 MB extracted)
- Reprojected to WGS84 (EPSG:4326) for GeoJSON output
- Centroids calculated for mapping

**Implementation**: `etl/fetch_dwr_cropmap.py`

---

## 7. CIMIS (California Irrigation Management Information System)

**Purpose**: Reference evapotranspiration (ETo) data

**Type**: REST JSON API

**Endpoint**: http://et.water.ca.gov/api/data

**Station Endpoint**: http://et.water.ca.gov/api/station

**Documentation**: http://et.water.ca.gov/Rest/Index

**API Key**: **Required** - Register at http://et.water.ca.gov/Home/Register

**Data Retrieved**:
- Daily reference ET (ETo) in inches
- 3 Sacramento Valley stations (Durham, Nicolaus, Yuba City)
- Last 1 year of data

**Notes**:
- Uses HTTP (not HTTPS)
- API has date range limitations (1 year maximum tested)
- Station IDs: 131 (Durham), 146 (Nicolaus), 194 (Yuba City)

**Implementation**: `etl/fetch_cimis.py`

**API Key Configuration**: Set `CIMIS_APP_KEY` in `.env`

---

## 8. USGS SSEBop (Operational Simplified Surface Energy Balance)

**Purpose**: Actual evapotranspiration from satellite data

**Type**: Raster downloads (NetCDF/GeoTIFF)

**URL**: https://www.usgs.gov/ (search "SSEBop evapotranspiration CONUS")

**Data Portal**: https://earlywarning.usgs.gov/ssebop

**Alternative**: OpenET API - https://openetdata.org

**API Key**: May be required depending on access method

**Notes**:
- **MVP Status**: Stub implementation only (Phase 2 feature)
- Would provide field-specific actual ET for consumptive use calculations
- Requires zonal statistics over rice polygons
- Alternative: OpenET provides easier API access

**Implementation**: `etl/fetch_ssebop.py` (stub)

**Future Requirements**:
- Additional packages: rasterstats, rasterio, xarray
- Workflow: Download monthly rasters → Zonal stats → Seasonal aggregation

---

## Data Refresh Schedule

### Real-Time / On-Demand
- **AWDB**: Daily updates, historical data stable
- **CIMIS**: Daily updates

### Monthly Updates
- **Bulletin 120**: Monthly during snow season (Dec-May)
- **ERS Rice Outlook**: Monthly reports

### Annual Updates
- **DWR Crop Map**: Annual release (typically fall for previous year)
- **NASS**: Annual and quarterly reports

### Recommended Refresh Workflow

```bash
# Fetch all current data
make etl

# Or fetch specific sources
python -m etl.fetch_all --awdb --b120 --cimis --dwr
```

---

## Data Quality Notes

1. **AWDB SWE Data**:
   - 47,118 records from 12 Sierra SNOTEL stations
   - 10 years of historical data (2015-2025)
   - No missing values in key columns

2. **Bulletin 120**:
   - 36 basin forecasts
   - Median forecasts extracted (p10/p90 available but not used in MVP)

3. **ERS Prices**:
   - Stub data with 2 price points
   - Production use requires NASS API integration

4. **DWR Crop Map**:
   - 4,612 rice polygons
   - 212,597 total acres
   - County distribution: Butte (40%), Sutter (24%), Yuba (17%), Glenn (10%), Colusa (9%)

5. **CIMIS ETo**:
   - 1,098 records (3 stations × 366 days)
   - Mean daily ETo: 0.152 inches
   - Range: 0.000 to 0.330 inches (reasonable for CA)

---

## Licensing and Terms of Use

All data sources used in this project are publicly available U.S. government data or publicly accessible California state data. Users should review the terms of use for each source:

- **USDA (NRCS, ERS, NASS)**: Public domain
- **CA DWR/CDEC**: Public data, attribution requested
- **CIMIS**: Public data with API key registration
- **USGS**: Public domain

Always provide proper attribution when publishing results derived from this data.
