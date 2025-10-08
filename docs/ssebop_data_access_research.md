# SSEBop Data Access Research

**Date**: 2025-10-04
**Task**: 13.1.1 - Research SSEBop vs OpenET data access options
**Decision**: Use USGS SSEBop direct download (free, no API key required)

---

## Option 1: USGS SSEBop (RECOMMENDED ✅)

### Overview
- **Source**: USGS Early Warning and Environmental Monitoring Program
- **Model**: Operational Simplified Surface Energy Balance (SSEBop) Version 6
- **Coverage**: Global (CONUS included)
- **Resolution**: ~1km (exact resolution to be verified with download)
- **Data Period**: 2012-present (updated monthly)

### Data Access

#### Monthly Data
**URL Pattern**:
```
https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/etav61/downloads/monthly/m{YYYY}{MM}.zip
```

**Example** (May 2022):
```
https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/etav61/downloads/monthly/m202205.zip
```

**File Structure**:
- Format: ZIP archive containing GeoTIFF files
- Contents: Monthly actual ET (ETa) rasters + anomaly rasters
- Units: Millimeters (mm) of ET per month
- Projection: WGS84 Geographic (EPSG:4326) [to be verified]

### Advantages
✅ **Free**: No API key, no subscription required
✅ **Stable URLs**: Predictable filename pattern for scripting
✅ **Long history**: Data from 2012 to present
✅ **USGS trusted source**: Official government data
✅ **Direct download**: No authentication complexity
✅ **Well-documented**: Peer-reviewed methodology

### Disadvantages
❌ **Large files**: Global rasters (~100-500 MB per month)
❌ **Manual filtering**: Must crop to California region
❌ **Monthly only**: No daily data in this archive
❌ **Latency**: ~1-2 month delay for recent data
❌ **No field-level API**: Must do zonal statistics ourselves

### Use Case Fit for Water-Opt
**Excellent fit** - We need:
- Monthly May-September data (5 months) for rice season
- Historical data (2022 available for our crop map)
- Free access for open-source tool
- Ability to process locally (no cloud dependency)

---

## Option 2: OpenET API

### Overview
- **Source**: OpenET Consortium (NASA, Google, USGS partners)
- **Models**: Ensemble of 6 ET models including SSEBop
- **Coverage**: 23 western US states
- **Resolution**: ~30m (Landsat-based, quarter-acre per pixel)
- **Data Period**: 2016-present (monthly), 2016-present (daily)

### Data Access

#### API-Based
**API Documentation**: https://openet.gitbook.io/docs/
**Authentication**: API key required from https://account.etdata.org/settings/api
**Endpoints**: Field-level queries, area of interest queries, raster exports

**Example Workflow**:
1. Create free account at etdata.org
2. Generate API key
3. Submit field polygons
4. Receive JSON response with ET values per field

### Advantages
✅ **Higher resolution**: 30m vs 1km (better for small fields)
✅ **Field-ready**: Returns ET per polygon directly
✅ **Daily data available**: More granular than monthly
✅ **Ensemble models**: Averages 6 ET models for robustness
✅ **Built for agriculture**: Designed for farm management
✅ **Google Earth Engine integration**: Cloud processing available

### Disadvantages
❌ **API key required**: Account creation + key management
❌ **Unknown pricing**: Free tier limits not clearly documented
❌ **Shorter history**: Only from 2016 (vs 2012 for SSEBop)
❌ **Internet dependency**: Requires API calls (no offline)
❌ **Rate limits**: Unknown query limits per account
❌ **Complexity**: More moving parts (auth, API versioning, etc.)

### Use Case Fit for Water-Opt
**Good, but overkill** - Benefits:
- Higher resolution would be more accurate
- Field-level API would simplify our code
- Ensemble models may be more robust

Concerns:
- Unknown cost model (could charge in future)
- Adds external dependency (API uptime)
- 1km resolution may be sufficient for 100+ acre rice fields
- Requires user to create OpenET account

---

## Comparison Matrix

| Feature | USGS SSEBop | OpenET API |
|---------|-------------|------------|
| **Cost** | Free ✅ | Free (with limits?) ⚠️ |
| **Authentication** | None ✅ | API key required ❌ |
| **Resolution** | ~1km ⚠️ | ~30m ✅ |
| **Data Period** | 2012-present ✅ | 2016-present ⚠️ |
| **Access Method** | Direct download ✅ | API calls ❌ |
| **Processing** | Local (zonal stats) ⚠️ | Cloud (pre-computed) ✅ |
| **Dependencies** | None ✅ | Internet required ❌ |
| **Field-level** | Manual ❌ | Built-in ✅ |
| **Offline use** | Yes ✅ | No ❌ |
| **Rate limits** | None ✅ | Unknown ⚠️ |

---

## Decision: Use USGS SSEBop

### Rationale

1. **Simplicity**: Direct HTTP download, no authentication complexity
2. **Cost certainty**: Free forever (government data mandate)
3. **Sufficient resolution**: 1km pixels cover multiple 100-acre fields
4. **Longer history**: 2012 data available if needed
5. **No external dependencies**: Works offline after initial download
6. **Open source friendly**: No account requirements for end users
7. **Established workflow**: Similar to our existing fetchers (AWDB, DWR, etc.)

### Implementation Plan

**Phase 2A (Current)**:
- Use USGS SSEBop monthly data (free, 1km)
- Download May-Sep 2022 rasters (5 files, ~2-3 GB total)
- Perform zonal statistics locally with rasterstats
- Validate results against literature (4.0 af/ac average)

**Phase 2B (Future, optional)**:
- Add OpenET API integration as alternative data source
- Allow user to choose: SSEBop (free, 1km) vs OpenET (API key, 30m)
- Compare results between sources for validation
- Use OpenET for fields <50 acres where resolution matters

---

## Technical Specifications

### SSEBop Data Details

**Model**: Operational Simplified Surface Energy Balance (SSEBop) Version 6
- Based on VIIRS thermal imagery (updated every 10 days)
- Uses GridMET reference ET dataset
- Validated against ground-based measurements

**Units**: Millimeters (mm) of ET per month
**Conversion**:
- 1 mm = 0.0393701 inches
- Seasonal ET (May-Sep): Sum 5 monthly values
- Per acre: ET_af_per_ac = (ET_mm × acres × 43560) / (1000 × 325851)

**File Format**: GeoTIFF (.tif)
**Projection**: WGS84 Geographic (EPSG:4326) [to verify]
**No-data value**: Typically -9999 or NaN

### Data Quality Notes

**Temporal Coverage**:
- Monthly: Feb 2012 to present (~150 files available)
- Updated within 1-2 months of current date
- May-Sep 2022: Available and quality-checked

**Spatial Coverage**:
- Global rasters (we only need California)
- CONUS fully covered
- Sacramento Valley: Lat 38.5-40.5°N, Lon -122.5 to -121.0°W

**Quality Flags**:
- No explicit quality flags in monthly aggregates
- Cloud contamination already handled in processing
- Irrigated agriculture validated with ground data

---

## Next Steps (Task 13.1.2)

1. **Download test file**: May 2022 (m202205.zip)
2. **Inspect contents**:
   - Extract ZIP
   - List GeoTIFF files
   - Check projection with `gdalinfo`
   - Verify data range (expect 50-200 mm for May in CA)
3. **Crop to California**: Use GDAL to subset global raster
4. **Test zonal statistics**: Run on 10 rice polygons
5. **Validate output**: Check ET values are reasonable

---

## References

**USGS SSEBop**:
- Main page: https://earlywarning.usgs.gov/fews/product/460
- Data download: https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/etav61/downloads/monthly/
- Methodology paper: Senay, G.B., et al. (2013). "Operational Evapotranspiration Mapping Using Remote Sensing and Weather Datasets"

**OpenET**:
- Homepage: https://etdata.org/
- API docs: https://openet.gitbook.io/docs/
- Validation paper: Melton et al. (2024). "Assessing the accuracy of OpenET satellite-based evapotranspiration data" Nature Water

**UC Davis Rice ET Studies**:
- Average consumptive use: 3.5-4.5 af/ac (48-60 inches)
- Peak ET: June-July (6-8 inches/month)
- Seasonal total: May-Sep (40-50 inches typical)

---

## Appendix: Alternative Data Sources (Not Recommended)

### Google Earth Engine
- **Access**: Requires GEE account + Python API
- **Pros**: Cloud processing, multiple ET datasets
- **Cons**: Complex setup, internet required, rate limits
- **Decision**: Overkill for our use case

### CIMIS ETo (Reference ET)
- **Already integrated**: We have this in Phase 1
- **Issue**: Reference ET ≠ Actual ET (crop-specific)
- **Use**: Validation/comparison only, not for CU calculation

### Field-Level Sensors
- **Access**: Farmer-installed equipment
- **Pros**: Most accurate, field-specific
- **Cons**: Not available for 4,612 fields, expensive
- **Use**: Ground truth for validation (if available)

---

**Document Status**: ✅ Complete
**Decision**: Proceed with USGS SSEBop monthly data
**Next Task**: 13.1.2 - Test download of sample monthly ET raster
