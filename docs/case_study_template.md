# Case Study Template: Historical Backtest

This template provides a structure for documenting historical "what-if" analyses using Water-Opt. Use this to backtest decisions against actual historical conditions and refine assumptions.

---

## Case Study: [Title]

**Date Prepared**: [YYYY-MM-DD]

**Analyst**: [Name/Organization]

**Study Period**: [Year or Range, e.g., "2021 Water Year" or "2018-2022"]

---

## Executive Summary

[2-3 paragraph summary of the case study purpose, key findings, and recommendations]

**Key Findings**:
- [Finding 1]
- [Finding 2]
- [Finding 3]

**Bottom Line**: [One sentence conclusion - e.g., "Growing rice was the optimal decision in 2021 despite drought conditions due to high rice prices"]

---

## Background and Context

### Study Region

- **Location**: [County, irrigation district, specific field location if applicable]
- **Total Acreage**: [acres]
- **Crop**: Rice (variety: [medium-grain/short-grain/other])
- **Water Source**: [Surface water district, groundwater, mixed]

### Historical Context

**Water Year Type**: [Critically Dry / Dry / Below Normal / Above Normal / Wet]

**Key Events**:
- [e.g., "SWRCB curtailment orders issued June 2021"]
- [e.g., "District allocation reduced to 40% in April"]
- [e.g., "Emergency drought declaration"]

**Market Conditions**:
- **Rice Price Range**: $[low] - $[high]/cwt
- **Water Transfer Prices**: $[low] - $[high]/af
- **Notable Market Factors**: [e.g., export demand, competing crops]

---

## Assumptions and Parameters

### Field Parameters (Actual)

| Parameter | Value | Source |
|-----------|-------|--------|
| Field Size | [X] acres | [Field records] |
| Actual Yield (if grown) | [X] cwt/acre | [Harvest records / district average] |
| Variety | [e.g., M-206, M-401] | [Planting records] |

### Cost Parameters (Actual)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Variable Cost | $[X]/acre | [Actual costs from records] |
| Fixed Cost | $[X] | [Annual overhead allocation] |
| Water District Fees | $[X]/acre | [District assessment] |

**Cost Breakdown** (if available):
- Seed: $[X]/acre
- Fertilizer: $[X]/acre
- Pesticides: $[X]/acre
- Field operations: $[X]/acre
- Irrigation: $[X]/acre
- Harvest: $[X]/acre

### Water Parameters (Actual)

| Parameter | Value | Source |
|-----------|-------|--------|
| District Allocation | [X]% | [District announcement] |
| Applied Water | [X] af/acre | [District delivery records] |
| Consumptive Use (estimated) | [X] af/acre | [ET calculation / SSEBop / default] |
| Conveyance Loss (if transfer) | [X]% | [District estimate / contract terms] |
| Transaction Cost (if transfer) | $[X] | [Actual costs / estimate] |

### Market Parameters (Actual)

| Parameter | Value | Source |
|-----------|-------|--------|
| Rice Price (received/potential) | $[X]/cwt | [Contract price / NASS average] |
| Water Price (available) | $[X]/af | [Transfer offers / district sales] |
| Water Buyer | [Urban district / ag neighbor / environmental] | [If applicable] |

---

## Analysis

### Scenario Modeled

**Decision Point**: [Month/Year, e.g., "May 2021 - planting decision"]

**Information Available at Decision Time**:
- District allocation: [X]%
- SWE forecast: [X] inches ([percentile])
- Bulletin 120 forecast: [X]% of average
- Rice futures price: $[X]/cwt
- Water transfer offers: $[X]/af

### Model Inputs

```
Acres: [X]
Expected Yield: [X] cwt/acre  # Based on [historical average / variety trial / conservative estimate]
Rice Price: $[X]/cwt           # Based on [futures / forward contract / NASS forecast]
Variable Cost: $[X]/acre
Fixed Cost: $[X]
CU: [X] af/acre                # Based on [SSEBop / district estimate / 4.0 default]
Water Price: $[X]/af           # Based on [actual offer / market survey]
Conveyance Loss: [X]%
Transaction Cost: $[X]
```

### Model Results

**Profit (Growing)**: $[X,XXX]

**Profit (Fallowing & Selling Water)**: $[X,XXX]

**Delta**: $[X,XXX] ([Grow / Fallow] advantage)

**Breakeven Water Price**: $[XXX]/af

**Model Recommendation**: [GROW / FALLOW]

---

## Actual Outcome

### Decision Made

**Actual Decision**: [Grew rice / Fallowed / Partial fallow]

**Rationale**: [Why this decision was made - may differ from model due to non-financial factors]

### Financial Results (if available)

| Item | Actual | Model Prediction | Variance |
|------|--------|------------------|----------|
| Yield (if grown) | [X] cwt/acre | [X] cwt/acre | [+/-X]% |
| Rice Price (if grown) | $[X]/cwt | $[X]/cwt | [+/-X]% |
| Water Revenue (if sold) | $[X] | $[X] | [+/-X]% |
| Total Costs | $[X] | $[X] | [+/-X]% |
| **Net Profit** | **$[X]** | **$[X]** | **[+/-X]%** |

**Comments on Variance**:
- [e.g., "Actual yield 15% higher than model due to favorable weather"]
- [e.g., "Water price lower than model due to late-season offer"]
- [e.g., "Costs higher due to unexpected pest pressure"]

---

## Sensitivity Analysis

### Key Sensitivities

**Most Sensitive Parameters** (from model):
1. [Parameter]: ±20% → $[X] delta impact
2. [Parameter]: ±20% → $[X] delta impact
3. [Parameter]: ±20% → $[X] delta impact

### What-If Scenarios

**Scenario 1: Lower Rice Price**
- If rice price had been $[X]/cwt (instead of $[X]/cwt)
- Profit (Growing): $[X]
- Profit (Fallowing): $[X]
- **Result**: [Would have changed / confirmed] decision

**Scenario 2: Higher Water Price**
- If water price had been $[X]/af (instead of $[X]/af)
- Profit (Growing): $[X]
- Profit (Fallowing): $[X]
- **Result**: [Would have changed / confirmed] decision

**Scenario 3: [Custom Scenario]**
- [Description]
- **Result**: [Impact]

---

## Lessons Learned

### Model Performance

**Accuracy**:
- [e.g., "Model predicted profit within 10% of actual"]
- [e.g., "Yield assumption too conservative - actual 15% higher"]
- [e.g., "Water price assumption accurate - actual within $10/af"]

**Model Strengths**:
- [What did the model capture well?]
- [What insights did it provide?]

**Model Limitations**:
- [What did the model miss?]
- [What assumptions proved incorrect?]
- [What external factors weren't captured?]

### Decision-Making Insights

1. **[Insight 1]**
   - [Description]
   - [Implication for future decisions]

2. **[Insight 2]**
   - [Description]
   - [Implication for future decisions]

3. **[Insight 3]**
   - [Description]
   - [Implication for future decisions]

### Recommended Assumption Adjustments

Based on this case study, recommend adjusting:

| Assumption | Current Default | Suggested Adjustment | Rationale |
|------------|----------------|----------------------|-----------|
| [Parameter] | [X] | [Y] | [Why] |
| [Parameter] | [X] | [Y] | [Why] |

---

## Non-Financial Considerations

### Factors Not Captured by Model

**Agronomic Considerations**:
- [e.g., "Fallowing would have led to weed bank buildup"]
- [e.g., "Continuous fallowing impacts soil structure"]
- [e.g., "Water rights: 'use it or lose it' concerns"]

**Business/Operational Considerations**:
- [e.g., "Equipment already purchased for season"]
- [e.g., "Contract obligations to buyer/processor"]
- [e.g., "Labor crew already hired"]

**Regulatory/Legal Considerations**:
- [e.g., "District prohibits >20% fallowing"]
- [e.g., "Environmental impact review required"]
- [e.g., "Endangered species constraints"]

**Community/Social Considerations**:
- [e.g., "Impact on local rice mill operations"]
- [e.g., "Employment considerations"]
- [e.g., "Dust mitigation requirements for dry fields"]

---

## Recommendations

### For This Operation

1. **[Recommendation 1]**
   - [Specific action]
   - [Expected benefit]

2. **[Recommendation 2]**
   - [Specific action]
   - [Expected benefit]

3. **[Recommendation 3]**
   - [Specific action]
   - [Expected benefit]

### For Model Improvement

1. **Data**: [e.g., "Integrate field-specific ET data from SSEBop"]
2. **Assumptions**: [e.g., "Adjust CU default to 3.8 af/ac for this district"]
3. **Features**: [e.g., "Add multi-year optimization capability"]

---

## Appendices

### Appendix A: Data Sources

- [List all data sources used]
- [Include URLs, access dates, specific reports]

### Appendix B: Calculations

[Include detailed calculations if helpful for replication]

```
# Example: Breakeven calculation details
Revenue (Growing) = 100 acres × 85 cwt/ac × $19/cwt = $161,500
Variable Costs = 100 acres × $650/ac = $65,000
...
```

### Appendix C: Supporting Documents

- [District allocation letter]
- [Water transfer contract]
- [Market price quotes]
- [Cost receipts]

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | [YYYY-MM-DD] | Initial draft | [Name] |
| 1.1 | [YYYY-MM-DD] | Updated with actual results | [Name] |

---

*This case study was prepared using Water-Opt MVP v0.1.0*

*Case studies are for educational and planning purposes only. Consult with qualified professionals before making farm management decisions.*
