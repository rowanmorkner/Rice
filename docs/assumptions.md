# Model Assumptions and Defaults

This document details all assumptions, default parameters, and modeling logic used in Water-Opt MVP profit calculations and scenario analysis.

---

## Default Parameters

### Field and Production

| Parameter | Default Value | Unit | Justification |
|-----------|--------------|------|---------------|
| **Acres** | 100 | acres | Typical small-to-medium rice operation in Sacramento Valley |
| **Expected Yield** | 85 | cwt/acre | California average rice yield (NASS historical average 2015-2024) |
| **Rice Price** | $19.00 | $/cwt | Medium-grain average based on ERS Rice Outlook and NASS data |

**Source**: USDA NASS California rice statistics, USDA ERS Rice Outlook reports

**Notes**:
- Yield assumptions do not account for:
  - Year-to-year weather variability
  - Field-specific soil conditions
  - Irrigation water quality
  - Pest pressure variations
- Users should adjust based on their historical yields

---

## Cost Assumptions

### Variable Costs

| Parameter | Default Value | Unit | Justification |
|-----------|--------------|------|---------------|
| **Variable Cost** | $650 | $/acre | Typical per-acre costs for CA rice production |

**Components** (approximate breakdown):
- Seed: $80/acre
- Fertilizer: $200/acre
- Pesticides/Herbicides: $100/acre
- Field operations (fuel, labor): $150/acre
- Irrigation labor and maintenance: $70/acre
- Harvest costs: $50/acre

**Source**: UC Davis Cost and Return Studies for Sacramento Valley rice production

**Notes**:
- Costs vary significantly by:
  - Field size (economies of scale)
  - Water district fees and delivery costs
  - Organic vs. conventional production
  - Direct seeding vs. transplanting
- Does not include land rent or water rights costs

### Fixed Costs

| Parameter | Default Value | Unit | Justification |
|-----------|--------------|------|---------------|
| **Fixed Cost** | $5,000 | $ | Annual fixed costs independent of acreage |

**Components** (approximate):
- Equipment depreciation: $2,000
- Insurance: $1,500
- Property taxes: $800
- General farm overhead: $700

**Notes**:
- Fixed costs are incurred whether growing or fallowing
- Fallowing may allow some equipment deferral but insurance and property taxes remain
- Scale with farm size (100-acre default)

---

## Water Parameters

### Consumptive Use (CU)

| Parameter | Default Value | Unit | Justification |
|-----------|--------------|------|---------------|
| **Consumptive Use** | 4.0 | acre-feet/acre | Typical CA rice consumptive use |

**Source**: California rice water use studies, DWR Bulletin 113

**Range**: 3.5 to 4.5 af/acre depending on:
- Climate (hot vs. moderate summer)
- Soil type (clay holds water better)
- Rice variety
- Field management practices

**Important Notes**:
- ⚠️ **TODO**: Replace with SSEBop actual ET data for field-specific estimates
- Current default is a Sacramento Valley average
- Consumptive use ≠ applied water (which includes conveyance losses and operational spills)
- Only consumptive use can be transferred under CA water law

**Methodology** (when SSEBop implemented):
1. Download monthly SSEBop ET rasters (May-September)
2. Perform zonal statistics over rice polygons
3. Sum seasonal ET for each field
4. Convert mm to acre-feet: `ET_af = (ET_mm × acres × 43560) / (1000 × 325851)`

---

### Water Market Parameters

| Parameter | Default Value | Unit | Justification |
|-----------|--------------|------|---------------|
| **Water Price** | $200 | $/acre-foot | Typical short-term transfer price in CA Central Valley |
| **Conveyance Loss** | 10% | % | Conservative estimate for conveyance losses |
| **Transaction Cost** | $500 | $ | Legal and administrative costs for water transfer |

**Water Price Notes**:
- Highly variable by:
  - Transfer duration (short-term vs. long-term)
  - Hydrologic year type (drought vs. wet year)
  - Buyer location and urgency
  - Conveyance path availability
- Historical range: $50-$500/af for short-term transfers
- Drought years can see $800+/af for urban M&I supplies

**Conveyance Loss Notes**:
- Represents water lost in transit from seller to buyer
- Includes:
  - Evaporation from canals
  - Seepage into groundwater
  - Operational spills
  - Measurement error
- Range typically 5-20% depending on:
  - Distance and infrastructure quality
  - Canal vs. pipeline conveyance
  - Season (higher in summer)

**Transaction Cost Notes**:
- Includes:
  - Legal review and documentation: $200-400
  - District approval fees: $100-200
  - SWRCB processing fees: $0-200 (short-term)
  - Hydrologic analysis (if required): variable
- Does not include:
  - Opportunity costs
  - Foregone subsidies or program payments
  - Long-term water right impacts

---

## Price Band Logic

### ERS Price Bands

**Method**: Rolling percentile bands

| Percentile | Label | Meaning |
|------------|-------|---------|
| **p10** | Low | Pessimistic price scenario (10th percentile) |
| **p50** | Median | Typical price scenario (50th percentile) |
| **p90** | High | Optimistic price scenario (90th percentile) |

**Window Size**: 12 months (rolling)

**MVP Limitation**:
- With only 2 ERS price points (stub data), synthetic bands are created using:
  - Mean price ± 1.28 standard deviations
  - Typical rice price volatility: 15-20%

**Production Implementation**:
- Integrate NASS QuickStats API for historical monthly prices
- Use 3-5 years of data for percentile calculation
- Update monthly as new data becomes available

---

## Hydrology Scenario Logic

### Water Year Classifications

| Scenario | Allocation Index | Percentile | Description |
|----------|------------------|------------|-------------|
| **Dry** | 40% | p10 SWE | Drought conditions, limited water availability |
| **Median** | 75% | p50 SWE | Normal water year, typical allocation |
| **Wet** | 100% | p90 SWE | Abundant water, full allocation |

**Allocation Index** represents simplified water supply availability:
- 0.4 = 40% of normal water supply
- 0.75 = 75% of normal water supply
- 1.0 = 100% of normal water supply

**Method**:
1. Calculate monthly SWE percentiles from 10 years of SNOTEL data
2. Map percentiles to allocation indices
3. Generate scenario matrix: 12 months × 3 scenarios = 36 rows

**Notes**:
- Allocation index is a **simplified proxy** for actual water district allocations
- Real allocations depend on:
  - Reservoir storage levels
  - Regulatory requirements (delta flows, fisheries)
  - Water rights priority (pre-1914 vs. post-1914)
  - Groundwater conditions
  - District-specific operating rules

**Production Refinement**:
- Integrate actual water district allocation announcements
- Add reservoir storage data (Shasta, Oroville, Folsom)
- Include regulatory constraints (CVP/SWP allocations)

---

## Profit Calculation Formulas

### Profit from Growing

```
Revenue = Acres × Yield × Price
Variable Costs = Acres × Variable Cost per Acre
Total Cost = Variable Costs + Fixed Cost
Profit (Growing) = Revenue - Total Cost
```

**Example** (default parameters):
```
Revenue = 100 acres × 85 cwt/acre × $19/cwt = $161,500
Variable Costs = 100 acres × $650/acre = $65,000
Total Cost = $65,000 + $5,000 = $70,000
Profit = $161,500 - $70,000 = $91,500
```

---

### Profit from Fallowing and Selling Water

```
Water Saved = Acres × CU (af/acre)
Deliverable Water = Water Saved × (1 - Conveyance Loss)
Revenue = (Deliverable Water × Water Price) - Transaction Cost
Profit (Fallowing) = Revenue - Fixed Cost
```

**Example** (default parameters with $200/af water price):
```
Water Saved = 100 acres × 4.0 af/acre = 400 af
Deliverable Water = 400 af × (1 - 0.10) = 360 af
Revenue = (360 af × $200/af) - $500 = $71,500
Profit = $71,500 - $5,000 = $66,500
```

---

### Breakeven Water Price

**Definition**: Water price at which Profit(Growing) = Profit(Fallowing)

**Formula**:
```
Breakeven Price = [Revenue(Growing) - Variable Costs + Transaction Cost] / Deliverable Water
```

**Example** (default parameters):
```
Breakeven = [($161,500 - $65,000) + $500] / 360 af
Breakeven = $97,000 / 360 af
Breakeven = $269.44/af
```

**Interpretation**:
- If market price **< $269.44/af**: Growing is more profitable
- If market price **> $269.44/af**: Fallowing and selling water is more profitable
- At exactly $269.44/af: Indifferent (equal profits)

---

## Sensitivity Analysis

### Parameters Tested

The tornado chart varies each parameter by ±20% while holding others constant:

| Parameter | Base | -20% | +20% |
|-----------|------|------|------|
| Rice Price | $19.00/cwt | $15.20/cwt | $22.80/cwt |
| Yield | 85 cwt/ac | 68 cwt/ac | 102 cwt/ac |
| Water Price | $200/af | $160/af | $240/af |
| Consumptive Use | 4.0 af/ac | 3.2 af/ac | 4.8 af/ac |
| Variable Cost | $650/ac | $520/ac | $780/ac |

**Output**: Change in profit delta (Grow - Fallow)

**Typical Sensitivity Ranking** (most to least sensitive):
1. Rice Price (highest leverage on growing profit)
2. Yield (directly multiplies rice revenue)
3. Water Price (affects fallow profit linearly)
4. Consumptive Use (affects amount of water available to sell)
5. Variable Cost (reduces growing profit)

---

## Limitations and Caveats

### Model Simplifications

1. **Uniform Application**: Map tab applies same decision to all fields
   - Reality: Field-level decisions depend on soil quality, water rights, location
   - Future: Field-specific ET, yields, water rights analysis

2. **Static Costs**: Costs don't vary by year or market conditions
   - Reality: Input prices (fuel, fertilizer) fluctuate significantly
   - Future: Dynamic cost modeling based on commodity prices

3. **No Risk Analysis**: Model uses point estimates, not probability distributions
   - Reality: Yields and prices are uncertain
   - Future: Monte Carlo simulation with distributions

4. **Single-Year Horizon**: No multi-year optimization
   - Reality: Water rights, soil health, equipment investments span years
   - Future: Dynamic programming for multi-year decisions

5. **No Environmental Constraints**: Doesn't model habitat impacts, water quality
   - Reality: Regulatory constraints on fallowing (endangered species, air quality)
   - Future: Environmental compliance module

### Data Limitations

1. **ERS Stub Data**: Only 2 price points in MVP
   - **Mitigation**: Use NASS QuickStats API for production

2. **Default CU**: 4.0 af/acre is a regional average
   - **Mitigation**: Implement SSEBop zonal statistics

3. **Allocation Index**: Simplified proxy for actual district allocations
   - **Mitigation**: Integrate district allocation announcements

4. **No Groundwater**: Doesn't model groundwater availability or SGMA impacts
   - **Mitigation**: Add groundwater data from DWR GSP monitoring

---

## Recommended Parameter Adjustments

### Conservative (Risk-Averse) Assumptions

For growers who prefer conservative estimates:
- **Yield**: Use 10th percentile of historical yields (not mean)
- **Price**: Use p10 price band (pessimistic)
- **Water Price**: Use lower quartile of recent transfers
- **Conveyance Loss**: Use 15% (higher than default)

### Optimistic (Risk-Tolerant) Assumptions

For growers comfortable with risk:
- **Yield**: Use 90th percentile of historical yields
- **Price**: Use p90 price band (optimistic)
- **Water Price**: Use upper quartile of recent transfers
- **Conveyance Loss**: Use 5% (lower than default)

---

## References

1. **UC Davis Cost and Return Studies**
   - https://coststudies.ucdavis.edu/
   - Sacramento Valley rice production costs

2. **CA Department of Water Resources, Bulletin 113**
   - Water use studies for various crops
   - https://water.ca.gov/Programs/Water-Use-And-Efficiency

3. **USDA NASS**
   - California rice statistics
   - https://quickstats.nass.usda.gov/

4. **Water Transfer Literature**
   - Hanak, E., et al. (2019). "Water and the Future of the San Joaquin Valley"
   - Public Policy Institute of California

---

*Last Updated: October 2025*
