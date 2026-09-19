# Power BI visual specification

This document maps the final four-page Power BI report to the validated exports
in `data/export/` and explains the business purpose of every visual.

## Model layout

The published report uses two long-format tables with the same logical fields:

- `CoffeeRewards`: the original funnel, channel, and segment aggregates.
- `AdditionalMetrics`: executive KPIs, receipt-level response timing, reward
  efficiency, modeled offer economics, and gross-margin scenarios.

Both tables use combinations of `dataset`, `dimension`, `category`, `measure`,
and `value`. They intentionally have no relationship. Each visual is filtered
to one dataset and the required measures, which prevents unrelated rows from
being summed together.

The repository CSV files remain the reproducible source of truth. The portfolio
report uses imported static data and therefore has no scheduled external
connection.

## 1. Executive Summary

The page answers three questions: how well the program converts, how quickly
customers respond, and whether reward spending is allocated efficiently.

| Visual | Source/filter | Purpose |
|---|---|---|
| Completion Rate (%) | `AdditionalMetrics`, `executive_kpis`, `Completion Rate` | Global completed/received rate: 44.02%. |
| Median Time to Complete (Hours) | `AdditionalMetrics`, `executive_kpis`, `Median Time to Complete` | Receipt-level median: 48 hours. |
| Total Reward Cost (USD) | `AdditionalMetrics`, `executive_kpis`, `Total Reward Cost` | Stated reward value for completed offers: $164.68K. |
| Offer Conversion Funnel | Overall received, viewed, and completed values | Shows 76.28K received, 57.73K viewed, and 33.58K completed. |
| Completion Share vs Reward Cost (%) | `AdditionalMetrics`, `reward_efficiency`, BOGO and discount | Exposes the allocation mismatch: discount produces 53% of completions with 31% of reward cost. |

The recommendation favors discount as the default incentive and reserves BOGO
for cases where faster completion is strategically valuable.

## 2. Funnel & Response

| Visual | Source/filter | Purpose |
|---|---|---|
| Volume by Funnel Stage and Offer Type | `funnel_by_type.csv` | Compares received, viewed, and completed volume by BOGO, discount, and informational offer. |
| View and Completion Rates by Channel (%) | `funnel_by_channel.csv` | Separates channel reach from final conversion. Channel attribution is associative because one offer may use multiple channels. |
| View and Completion Rates by Offer Type (%) | `funnel_by_type.csv` | Shows discount leading completion and BOGO leading views; informational offers cannot be completed by design. |
| Median Response Time by Offer Type (Hours) | `AdditionalMetrics`, `response_timing` | Compares time to view and time to complete. BOGO completes in 42 hours versus 60 for discount. |

The page-level takeaway highlights the trade-off: discount converts more often,
while BOGO completes faster. Channel selection changes initial engagement more
than final conversion in this sample.

## 3. Customer Segments

| Visual | Source/filter | Purpose |
|---|---|---|
| Completion Rate by Age Group (%) | `completion_by_segment.csv`, `dimension = age` | Completion rises through age 50 and then stabilizes near 52%. |
| Completion Rate by Income Level (%) | `completion_by_segment.csv`, `dimension = income` | Completion rises from 35% below $40K to 62% at $100K+. |
| Completion Rate by Gender (%) | `completion_by_segment.csv`, `dimension = gender` | Women and the dataset's `O` group complete at 55-56%; men at 43%. |
| Cohorts With vs. Without Demographic Data (%) | `cohort_comparison.csv` | Customers without demographic data view at a similar rate but complete far less often, indicating a targeting or data-quality issue. |

Segment differences are descriptive associations. They should guide further
investigation and experimentation, not be interpreted as causal effects.

## 4. Offer Economics

| Visual | Source/filter | Purpose |
|---|---|---|
| BOGO Reward Cost per Received (USD) | `AdditionalMetrics`, `reward_efficiency`, BOGO | $3.72 per received offer. |
| Discount Reward Cost per Received (USD) | `AdditionalMetrics`, `reward_efficiency`, discount | $1.68 per received offer. |
| BOGO Break-even Margin (%) | `AdditionalMetrics`, `incrementality_model`, BOGO | Estimated break-even contribution margin: 79.28%. |
| Discount Break-even Margin (%) | `AdditionalMetrics`, `incrementality_model`, discount | Estimated break-even contribution margin: 28.14%. |
| Modeled Sales per Reward Dollar | `AdditionalMetrics`, `incrementality_model`, `Sales per Reward Dollar` | Directional comparison: $1.26 for BOGO and $3.55 for discount. |
| Net Contribution by Gross Margin Scenario (USD) | `AdditionalMetrics`, `margin_sensitivity` | Shows how modeled contribution changes from 20% to 80% gross margin, with a zero-dollar reference line. |

The economics page is explicitly directional. The source data does not contain
actual product margins, randomized treatment assignment, or a valid untreated
control group. Informational offers are used only as a behavioral benchmark.

## Rebuilding the inputs

```bash
python3 notebooks/04_powerbi_export.py
python3 notebooks/05_incrementality_analysis.py
```

The scripts regenerate the validated tables under `data/export/`. See
`data/export/README.md` for field definitions and methodological notes.
