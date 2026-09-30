# Findings: Dubai Property Market Intelligence for Portal Inside Sales

> Real Dubai Land Department open data (CC BY 4.0) via Dubai Data and dataHabibi, through Aug 2026. Commercial targets in the Excel model are illustrative assumptions.

## 1. The market has slowed sharply in 2026
- Registered sales in the last 12 months (Sep 2025 - Aug 2026): **173,983**, -8.5% vs the prior 12 months.
- Jan - Aug 2026: 101,862 sales, -19.1% vs Jan - Aug 2025 (Jan - Apr -4.3%, May - Aug -31.7%).
- Prices are holding: median AED 1,680/sqft in Aug 2026 (-0.1% YoY, 5-month average).
- **Commercial impact:** agencies see fewer deals, so budget pressure and churn risk rise. Targets built on 2025 run-rates will be too high.

## 2. Where demand is moving
- 113 communities tracked; the top 10 hold 44.4% of transactions.
- Fastest-growing large communities (2,000+ sales): City Of Arabia (+619.2%), Down Town Jabal Ali (+204.3%), Majan (+143.5%), Dubai South Residential District (+111.5%), Palm Deira (+63.5%).
- Fastest-cooling large communities: Dubai Marina (-53.5%), Dubai Hills Estate (-51.6%), Al Furjan (-33.1%), Silicon Oasis (-29.5%), Business Bay (-27.0%).
- Quadrants (500+ sales): 25 Hot; 17 Tightening; 9 Cooling; 1 Value play.

## 3. Territory planning for 12 inside-sales reps
Backtest: predict each community's share of the next 12 months' transactions (two test years).

| Method | Sales effort misallocated |
|---|---|
| Momentum-adjusted | 20.2% |
| Last 12 months | 20.7% |
| Equal split | 51.7% |

- Balanced territories: each of the 12 territories is within 3.6% of an equal share of Dubai demand (`outputs/territories.csv`).

## 4. Sep - Dec 2026 transaction forecast
Rolling one-month-ahead backtest, Sep 2025 - Aug 2026:

| Method | MAPE | Bias |
|---|---|---|
| Run-rate x seasonality | 13.7% | +7.3% |
| Holt-Winters (damped, log) | 14.3% | +9.4% |
| Same month last year | 26.1% | +9.3% |

- History-based methods over-forecast the 2026 slowdown; the recent run-rate adjusted for seasonality tracks it best.
- Forecast (run-rate x seasonality): 2026-09: 13,111 (10,841 - 15,857), 2026-10: 15,241 (12,602 - 18,432), 2026-11: 14,603 (12,074 - 17,661), 2026-12: 15,414 (12,745 - 18,642). Total 58,369 vs 72,121 in Sep - Dec 2025 (-19.1%).
- Seasonality: Dec is the strongest month (index 1.12), Jan the weakest (0.87); phase monthly targets with this index.

## 5. Developer prospects (new-project advertising)
- 250 developers have 289,336 units under construction; the top 20 by prospect score hold 42.9% of them and 26,645 units due for handover in the next 12 months.
- Top 5: Azizi Developments L.L.C (33,845 units), Binghatti Developers Fze (29,482 units), Ellington Properties Development L.L.C (2,983 units), Danube Properties Development L.L.C (11,681 units), Hre Real Estate Development L.L.C (4,385 units).

## 6. Rental-yield hotspots (investor campaigns)
- International Media Production Zone: 8.62% gross yield, 6,678 Ejari contracts
- International City Phase 1: 8.21% gross yield, 22,615 Ejari contracts
- Dubai Studio City: 8.01% gross yield, 1,931 Ejari contracts
- DAMAC HILLS 2: 7.98% gross yield, 5,359 Ejari contracts
- Dubai Sports City: 7.78% gross yield, 8,665 Ejari contracts

## Recommendations
1. Reset Q4 2026 targets to the 2026 run-rate, not 2025 history, and phase them with the seasonality index.
2. Allocate reps by last-12-month community demand using the balanced 12-territory plan.
3. Assign the 20 Tier-A developers to key-account managers ahead of their handover launches.
4. Protect agency revenue in cooling communities with lead-quality reviews before renewal.
5. Arm reps with the community fact cards (`outputs/enablement_kit.csv`) and yield hotspots for investor pitches.