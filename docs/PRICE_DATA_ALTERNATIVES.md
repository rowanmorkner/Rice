# Alternative Rice Price Data Sources

The current ERS Rice Outlook implementation provides only 2 stub price points because the PDFs are narrative reports, not tabular data. This document outlines better alternatives.

---

## Current Situation

**Problem**: ERS Rice Outlook PDFs contain market commentary but minimal structured price data
**Result**: Only 2 data points → Very limited price history chart
**Impact**: Cannot build meaningful price bands or trend analysis

---

## Recommended Solutions (Best to Least Effort)

### 1. ⭐ USDA NASS QuickStats API (BEST - When Available)

**Status**: Fully implemented, API currently timing out

**Why it's the best**:
- Actual prices received by California growers
- Monthly data going back decades
- Free API with your existing key
- By variety (medium-grain, short-grain)
- County-level detail

**API Endpoint**: http://quickstats.nass.usda.gov/api/api_GET/

**Parameters**:
```python
{
    'key': YOUR_API_KEY,
    'commodity_desc': 'RICE',
    'state_alpha': 'CA',
    'statisticcat_desc': 'PRICE RECEIVED',
    'year__GE': 2015,
    'format': 'JSON'
}
```

**How to use**:
```bash
# When API recovers (check periodically)
python -m etl.fetch_nass

# Then update fetch_all.py to include --nass
make etl  # Will include NASS data
```

**Expected data**: 100+ price records from 2015-2025

---

### 2. 🌟 USDA AMS Rice Market News (IMPLEMENTED)

**Status**: Fetcher created (`etl/fetch_ams_rice.py`)

**Why it's good**:
- Weekly market reports with actual CA rice prices
- Free API, no key required
- More current than NASS (weekly vs monthly)
- FOB mill prices (actual market quotes)

**API Endpoint**: https://marsapi.ams.usda.gov/services/v1.2/reports

**What you get**:
- California medium-grain quotes
- California short-grain quotes
- Weekly updates
- Price ranges (low-high)

**How to use**:
```bash
# Test the new AMS fetcher
python -m etl.fetch_ams_rice

# If successful, add to fetch_all.py:
# In etl/fetch_all.py, add "ams" to fetchers dict
```

**Parsing note**: AMS returns unstructured text reports. The fetcher uses regex to extract prices. You may need to adjust patterns based on actual report format.

**Example report text**:
```
California medium-grain #2, FOB mill: $18.50-19.25 per cwt
California short-grain, FOB mill: $19.00-19.75 per cwt
```

---

### 3. CME Rough Rice Futures

**Why it's useful**:
- Forward-looking market expectations
- Daily liquidity and price discovery
- Good for scenario analysis

**Limitations**:
- Southern US rice (not California-specific)
- Rough rice (not milled) - need conversion factor
- Typically trades 10-15% below California medium-grain

**Data sources**:

**Option A: Barchart API** (Free tier available)
- URL: https://www.barchart.com/solutions/data/market
- Free tier: Delayed data (15 minutes)
- Paid tier: Real-time + historical

**Option B: Quandl (now Nasdaq Data Link)**
- URL: https://data.nasdaq.com/
- CME rice futures historical data
- Free with registration

**Option C: CME DataMine** (Official)
- URL: https://www.cmegroup.com/market-data/datamine-historical-data.html
- Most comprehensive
- Requires subscription (~$50-150/month)

**Example implementation**:
```python
# etl/fetch_cme_rice.py
import requests

def fetch_cme_futures():
    # Using Barchart free API
    url = "https://marketdata.websol.barchart.com/getQuote.json"
    params = {
        'apikey': YOUR_BARCHART_KEY,
        'symbols': 'ZR*0'  # Rough rice futures
    }
    response = requests.get(url, params=params)
    # Parse and convert to CA equivalent (multiply by 1.15 as proxy)
```

---

### 4. Manual Data Entry from AMS Reports

**When to use**: If APIs are unavailable

**Process**:
1. Visit https://www.ams.usda.gov/market-news/rice-reports
2. Download "Weekly Rice Market Summary" reports
3. Extract California rice quotes manually
4. Create CSV: `data/raw/manual_rice_prices.csv`

**CSV format**:
```csv
date,variety,price_low,price_high,price_avg
2025-01-01,medium-grain,18.25,18.75,18.50
2025-01-08,medium-grain,18.50,19.00,18.75
2025-01-01,short-grain,19.00,19.50,19.25
```

**Load in app**:
```python
# In models/scenarios.py
def build_price_bands(ers_prices_df=None, manual_path=None):
    if manual_path and Path(manual_path).exists():
        return pd.read_csv(manual_path)
    # ... existing code
```

---

### 5. California Rice Commission Data

**URL**: https://calrice.org/industry-statistics/

**What they have**:
- Industry aggregate statistics
- May have historical price data
- Contact them for data sharing

**Note**: Primarily industry advocacy, not a data API

---

## Recommended Implementation Path

### Phase 1 (Immediate - This Week)

1. **Test AMS fetcher**:
   ```bash
   python -m etl.fetch_ams_rice
   ```

2. **If successful**, update `etl/fetch_all.py`:
   ```python
   fetchers = {
       # ... existing
       "ams": ("AMS Rice Market News", "etl.fetch_ams_rice"),
   }
   ```

3. **Update app** to use AMS data:
   ```python
   # In app/Main.py tab_markets()
   ams_path = data_dir / "stage" / "ams_rice_prices.parquet"
   if ams_path.exists():
       df_ams = pd.read_parquet(ams_path)
       price_bands = build_price_bands(df_ams, data_dir=data_dir)
   ```

### Phase 2 (When NASS Recovers)

1. Monitor NASS API health
2. When working, run `python -m etl.fetch_nass`
3. Compare NASS vs AMS data quality
4. Use whichever has better coverage

### Phase 3 (Production Enhancement)

1. Integrate CME futures for forward curve
2. Combine multiple sources:
   - NASS: Historical monthly averages
   - AMS: Current weekly quotes
   - CME: Forward expectations
3. Weighted average or ensemble approach

---

## Price Data Comparison

| Source | Frequency | Geography | Cost | Latency | Best For |
|--------|-----------|-----------|------|---------|----------|
| **NASS** | Monthly | CA-specific | Free | 30 days | Historical analysis |
| **AMS** | Weekly | CA-specific | Free | 1 week | Current prices |
| **CME** | Daily | US South | Free-Paid | Real-time | Forward outlook |
| **ERS** | Monthly | US aggregate | Free | 30 days | Commentary only |

---

## Converting Between Price Formats

**Rough Rice → Milled Rice**:
```python
milled_price = rough_price * 1.15  # Approximate conversion
```

**Southern US → California**:
```python
ca_price = southern_price * 1.05  # CA premium (5-10%)
```

**FOB Mill → Farm Gate**:
```python
farm_gate = fob_mill - hauling_cost  # Typically $0.50-1.00/cwt
```

---

## Testing Your Price Data

After implementing a new source, verify quality:

```python
import pandas as pd

df = pd.read_parquet('data/stage/[new_source]_prices.parquet')

# Check coverage
print(f"Records: {len(df)}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Price range: ${df['price_usd_cwt'].min():.2f} - ${df['price_usd_cwt'].max():.2f}")

# Check for gaps
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')
date_gaps = df['date'].diff()
large_gaps = date_gaps[date_gaps > pd.Timedelta(days=60)]
print(f"Data gaps >60 days: {len(large_gaps)}")

# Visualize
import matplotlib.pyplot as plt
plt.figure(figsize=(12,6))
plt.plot(df['date'], df['price_usd_cwt'])
plt.title('Rice Price History')
plt.xlabel('Date')
plt.ylabel('Price ($/cwt)')
plt.show()
```

---

## Next Steps

1. **Immediate**: Try the new AMS fetcher
2. **Monitor**: Check NASS API weekly
3. **Consider**: CME futures for production deployment
4. **Document**: Update progress.log with chosen solution

---

*Last Updated: 2025-10-04*
