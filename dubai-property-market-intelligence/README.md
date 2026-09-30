# Dubai Property Market Intelligence for Portal Inside Sales

A commercial analytics project built on **real Dubai Land Department (DLD) open data**. It answers the questions a property portal's inside-sales and commercial teams face: how the market is moving, where to focus reps, how to set and phase targets, which developers to prioritise, and what insight to hand account managers for client meetings.

> **Data:** real, public DLD transactions, Ejari rent contracts and the DLD project registry, aggregated and published under CC BY 4.0 by [Dubai Data](https://github.com/datadubai/dubai-real-estate-dld) and [dataHabibi](https://github.com/dataHabibi/dubai-price-index), through August 2026. See [`data/SOURCES.md`](data/SOURCES.md). The revenue goal in the Excel model is an illustrative assumption.

## Business questions

1. How healthy is the Dubai property market, and what does it mean for portal revenue?
2. Which communities are gaining or losing transaction demand?
3. How should 12 inside-sales reps split Dubai into territories, and which allocation method holds up?
4. How many transactions should we expect in Sep - Dec 2026 to phase Q4 targets?
5. Which developers should key-account managers prioritise for new-project advertising?
6. What community facts should reps bring to client meetings?

## Key results

| Area | Result |
|---|---|
| Scale | 1.16M+ registered sales since 2008, 113 communities, 798 registered projects, 250 developers with active pipelines |
| Market | 173,983 sales in the last 12 months (**-8.5%**); Jan - Aug 2026 **-19.1%** YoY, with May - Aug **-31.7%**; prices flat (AED 1,680/sqft) |
| Territory allocation | Allocating reps by last-12-month demand cut misallocated sales effort from **51.7% to 20.7%** vs an equal split (two-year backtest) |
| Territory design | 12 balanced territories, each within **3.6%** of an equal share of Dubai demand |
| Forecast | Run-rate x seasonality forecast: **13.7% MAPE** in a 12-month rolling backtest vs 26.1% for same-month-last-year; Sep - Dec 2026 expected **19% below** 2025 |
| Developer prospects | Top 20 of 250 developers hold **42.9%** of 289,336 units under construction |
| Demand shift | Growth in Majan (+144%), Dubai South (+112%), Palm Deira (+64%); cooling in Dubai Marina (-54%), Dubai Hills (-52%), Business Bay (-27%) |

Full write-up: [`reports/findings.md`](reports/findings.md) · 7-slide deck: `reports/Dubai_Market_Intelligence_Review.pptx`

## What's inside

```
dubai-property-market-intelligence/
├── config.py                 # dates, territory count, illustrative goal and weights
├── pipeline.py               # runs everything end to end
├── app.py                    # Streamlit self-service dashboard (6 tabs)
├── data/raw/                 # real DLD open-data CSVs (CC BY 4.0) + SOURCES.md
├── sql/                      # 6 SQL analyses: CTEs, window functions, joins
├── src/
│   ├── build_db.py           # loads raw CSVs into SQLite
│   ├── analysis.py           # momentum, territory backtest & design, forecast, developer scoring
│   └── excel_model.py        # live Excel territory target & prospect model (1,299 formulas)
├── outputs/                  # CSV results, metrics.json, Territory_Target_Model.xlsx
├── reports/                  # findings.md and the slide deck
└── tests/test_pipeline.py    # 7 data and model tests (pytest)
```

## Methods

**Community momentum.** Last 12 months vs prior 12 months of registered sales and median AED/sqft per community, split into four quadrants: Hot (volume and price up), Tightening (price up, volume down), Value play and Cooling.

**Territory allocation backtest.** For two test years (Sep 2024 - Aug 2025 and Sep 2025 - Aug 2026), each method predicts every community's share of next year's transactions: equal split, last-12-month share, and momentum-adjusted share. Error = the share of sales effort sent to the wrong communities (half the sum of absolute share errors).

**Territory design.** Communities are assigned to 12 reps with a longest-processing-time greedy algorithm so each territory carries a near-equal share of demand. Territories are demand-balanced, not geographic; a production version would add location constraints.

**Forecast.** Rolling one-month-ahead backtest over Sep 2025 - Aug 2026 comparing damped Holt-Winters (log scale), same-month-last-year, and the average de-seasonalised run-rate of the last 3 months x a 2012-2024 seasonality index. The run-rate method is used for the Sep - Dec 2026 forecast because it adapts fastest to the 2026 slowdown.

**Developer prospect score.** Weighted percentile of pipeline units under construction (40%), sales in the last 12 months (30%), sales growth (20%) and units due for handover in the next 12 months (10%). Top 20 = Tier A key accounts.

## SQL highlights

- `01_market_trend.sql`: rolling 12-month volume with `SUM() OVER (ROWS BETWEEN 11 PRECEDING ...)`, YoY via `LAG(12)`
- `02_community_momentum.sql`: date-bounded CTEs, conditional aggregation, `RANK()`, `NTILE(4)`, share of total with `SUM() OVER ()`
- `03_seasonality.sql`: month-vs-yearly-average index with `AVG() OVER (PARTITION BY year)`
- `04_developer_pipeline.sql`: active-project pipeline and 12-month handovers joined to developer sales
- `05_yield_opportunities.sql`: three-way join of sales, Ejari rents and yields with ranking
- `06_enablement_kit.sql`: community fact cards for account managers

## Excel model

`outputs/Territory_Target_Model.xlsx`: change the Q4 revenue goal or the demand-index weights (yellow cells) and every community, territory and monthly target updates. Monthly targets are phased by the transaction forecast. Also includes a live developer scoring sheet and fact cards.

## How to run

```bash
pip install -r requirements.txt
python pipeline.py        # build DB, run analysis, build Excel model
pytest -q                 # 7 tests
streamlit run app.py      # dashboard
```

To refresh with the latest data, re-download the CSVs from the two source repositories into `data/raw/`, update `LATEST_MONTH` in `config.py`, and re-run the pipeline.

## Notes

- Community-level figures cover the transactions the publisher can attribute to a community with valid price data (about 157K of 174K sales in the last 12 months), so community totals are below the Dubai-wide total.
- All figures are medians from the publishers' cleaned aggregates, with outliers trimmed per their methodology.

## Attribution

Dubai Data (datadubai.ae), Continental Club Property, based on Dubai Land Department open data, data through 2026-09-24 (CC BY 4.0). dataHabibi L.L.C-FZ, Dubai residential price and rent index (CC BY 4.0). Source data © Dubai Land Department. Not an official DLD product.

## Tools

Python (Pandas, NumPy, statsmodels), SQL (SQLite), Excel (openpyxl), Streamlit, Plotly, pytest.
