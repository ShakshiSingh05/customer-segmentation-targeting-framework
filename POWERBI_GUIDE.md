# Building the Power BI dashboard (about 30-45 minutes)

I could not create a .pbix file, so build it from the CSVs in `powerbi_exports/`.

## 1. Load
Get Data → Text/CSV → load all four files:
`customer_segments.csv`, `segment_summary.csv`, `segment_category_spend.csv`, `targeting_framework.csv`.

## 2. Model
Relate `customer_segments[segment]` to `targeting_framework[segment]` (many-to-one) and to `segment_category_spend[segment]`.

## 3. Measures (DAX)
```
Customers = DISTINCTCOUNT(customer_segments[customer_id])
Total Spend = SUM(customer_segments[total_spend])
Avg Spend per Customer = DIVIDE([Total Spend], [Customers])
% of Customers = DIVIDE([Customers], CALCULATE([Customers], ALL(customer_segments[segment])))
% of Spend = DIVIDE([Total Spend], CALCULATE([Total Spend], ALL(customer_segments[segment])))
Avg Recency (days) = AVERAGE(customer_segments[recency_days])
```

## 4. Pages
**Page 1: Portfolio overview.** KPI cards (Customers, Total Spend, Avg Spend); clustered bar of % of Customers vs % of Spend by segment; slicers for region, age_band, card_tier.
**Page 2: Segment deep-dive.** Matrix of category mix by segment (from `segment_category_spend`, show as % of row total); scatter of txn_count vs total_spend coloured by segment; tenure and recency by segment.
**Page 3: Targeting framework.** Table from `targeting_framework` (segment, objective, offer, channel, KPI) with customer counts, plus a text box with 3 recommendations.

## 5. Publish
Save a .pbix and add screenshots to `charts/` or a `dashboard/` folder in the repo, so recruiters can see it without opening Power BI.
