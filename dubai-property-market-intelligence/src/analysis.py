"""Dubai Property Market Intelligence: analysis for a property portal's inside-sales team.

1. Market health: transactions and prices, YoY, seasonality (SQL)
2. Community momentum quadrants: where demand is growing or cooling
3. Territory planning: backtest of demand-share methods + balanced territories for 12 reps
4. Transaction forecast (Holt-Winters) to phase Q4 2026 targets
5. Developer prospect scoring from the DLD project pipeline
6. Rental-yield hotspots and sales-enablement fact cards
"""
import json
import sqlite3
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C  # noqa: E402

warnings.filterwarnings("ignore")

SQL = {"market_trend": "01_market_trend.sql", "community_momentum": "02_community_momentum.sql",
       "seasonality": "03_seasonality.sql", "developer_pipeline": "04_developer_pipeline.sql",
       "yield_opportunities": "05_yield_opportunities.sql", "enablement_kit": "06_enablement_kit.sql"}


def run_sql(con):
    return {k: pd.read_sql((C.SQL_DIR / f).read_text(), con) for k, f in SQL.items()}


# ---------------------------------------------------------------- market health
def market_kpis(trend):
    t = trend.set_index("month")
    last12 = t.loc["2025-09":"2026-08", "sales_count"].sum()
    prev12 = t.loc["2024-09":"2025-08", "sales_count"].sum()
    ytd26 = t.loc["2026-01":"2026-08", "sales_count"].sum()
    ytd25 = t.loc["2025-01":"2025-08", "sales_count"].sum()
    h1 = t.loc["2026-01":"2026-04", "sales_count"].sum() / t.loc["2025-01":"2025-04", "sales_count"].sum() - 1
    h2 = t.loc["2026-05":"2026-08", "sales_count"].sum() / t.loc["2025-05":"2025-08", "sales_count"].sum() - 1
    return {"sales_last_12m": int(last12), "sales_prev_12m": int(prev12), "sales_12m_change": last12 / prev12 - 1,
            "ytd_2026": int(ytd26), "ytd_2025": int(ytd25), "ytd_change": ytd26 / ytd25 - 1,
            "jan_apr_change": h1, "may_aug_change": h2,
            "psf_latest": float(t.loc[C.LATEST_MONTH, "median_aed_per_sqft"]),
            "psf_yoy_latest": float(t.loc[C.LATEST_MONTH, "psf_yoy"]),
            "peak_12m_sales": int(t["sales_rolling_12m"].max()),
            "peak_12m_month": t["sales_rolling_12m"].idxmax()}


# ---------------------------------------------------------------- momentum quadrants
def momentum_quadrants(mom, min_sales=500):
    m = mom[(mom.sales_12m >= min_sales) & mom.sales_growth.notna() & mom.psf_growth.notna()].copy()
    def q(r):
        if r.sales_growth >= 0 and r.psf_growth >= 0:
            return "Hot: volume and price rising"
        if r.sales_growth >= 0:
            return "Value play: volume up, price down"
        if r.psf_growth >= 0:
            return "Tightening: price up, volume down"
        return "Cooling: volume and price down"
    m["quadrant"] = m.apply(q, axis=1)
    return m


# ---------------------------------------------------------------- territory planning
def window_sales(cm, start, end):
    return cm[(cm.month >= start) & (cm.month <= end)].groupby("community")["n_sales"].sum()


def share_backtest(cm):
    """Predict each community's share of next-12-month transactions.

    equal     : every community gets the same share (how many teams split territories)
    last_12m  : share of the previous 12 months
    momentum  : previous share x (1 + damped growth), renormalised
    Error = half the sum of absolute share errors = % of sales effort misallocated.
    """
    tests = [("2022-09", "2023-08", "2023-09", "2024-08", "2024-09", "2025-08"),
             ("2023-09", "2024-08", "2024-09", "2025-08", "2025-09", "2026-08")]
    rows = []
    for p0, p1, b0, b1, t0, t1 in tests:
        prev, base, actual = window_sales(cm, p0, p1), window_sales(cm, b0, b1), window_sales(cm, t0, t1)
        comms = base[base > 0].index.union(actual[actual > 0].index)
        base, prev, actual = (s.reindex(comms).fillna(0) for s in (base, prev, actual))
        act_share = actual / actual.sum()
        equal = pd.Series(1 / len(comms), index=comms)
        last = base / base.sum()
        growth = ((base + 50) / (prev + 50) - 1).clip(-0.6, 1.5)
        mom = last * (1 + 0.5 * growth)
        mom = mom / mom.sum()
        for name, pred in [("Equal split", equal), ("Last 12 months", last), ("Momentum-adjusted", mom)]:
            rows.append({"test_period": f"{t0} to {t1}", "method": name,
                         "misallocated_share": 0.5 * (pred - act_share).abs().sum(),
                         "communities": len(comms)})
    res = pd.DataFrame(rows)
    summary = res.groupby("method")["misallocated_share"].mean().sort_values()
    return res, summary


def design_territories(mom, n=C.N_TERRITORIES):
    """Balance total transaction demand across n reps (longest-processing-time greedy)."""
    d = mom[["community", "sales_12m", "share_of_sales"]].sort_values("sales_12m", ascending=False)
    loads = {i: 0.0 for i in range(1, n + 1)}
    assign = []
    for r in d.itertuples():
        t = min(loads, key=loads.get)
        loads[t] += r.share_of_sales
        assign.append((r.community, f"T{t:02d}", r.sales_12m, r.share_of_sales))
    a = pd.DataFrame(assign, columns=["community", "territory", "sales_12m", "share_of_sales"])
    terr = a.groupby("territory").agg(communities=("community", "count"), sales_12m=("sales_12m", "sum"),
                                      demand_share=("share_of_sales", "sum"),
                                      anchor_community=("community", "first")).reset_index()
    target = 1 / n
    terr["vs_equal_share"] = terr["demand_share"] / target - 1
    return a, terr


# ---------------------------------------------------------------- forecast
def seasonal_index(s, start="2012", end="2024"):
    x = s[start:end]
    df = pd.DataFrame({"y": x.values, "yr": x.index.year, "m": x.index.month})
    df["ratio"] = df["y"] / df.groupby("yr")["y"].transform("mean")
    return df.groupby("m")["ratio"].mean()


def forecast_transactions(trend):
    """Rolling one-month-ahead backtest (Sep 2025 - Aug 2026) of three methods, then a Sep-Dec 2026 forecast.

    holt_winters      : damped additive Holt-Winters on log sales (2012+), refit every month
    seasonal_naive    : same month last year
    run_rate_seasonal : average de-seasonalised sales of the last 3 months x seasonal index
    """
    s = trend.set_index(pd.PeriodIndex(trend["month"], freq="M"))["sales_count"].astype(float)["2012-01":]
    si = seasonal_index(s)

    def hw_fit(series):
        return ExponentialSmoothing(np.log(series), trend="add", damped_trend=True, seasonal="add",
                                    seasonal_periods=12).fit(optimized=True)

    def run_rate(hist, target_months):
        base = np.mean([hist.iloc[-k] / si[hist.index[-k].month] for k in (1, 2, 3)])
        return np.array([base * si[m.month] for m in target_months])

    rows = []
    for t in pd.period_range("2025-09", "2026-08", freq="M"):
        hist = s[:t - 1]
        rows.append({"month": str(t), "actual": s[t],
                     "holt_winters": float(np.exp(hw_fit(hist).forecast(1)).iloc[0]),
                     "seasonal_naive": s[t - 12],
                     "run_rate_seasonal": float(run_rate(hist, [t])[0])})
    bt = pd.DataFrame(rows).set_index("month").round(0)
    mape = {c: float((abs(bt[c] - bt["actual"]) / bt["actual"]).mean())
            for c in ["holt_winters", "seasonal_naive", "run_rate_seasonal"]}
    bias = {c: float(bt[c].sum() / bt["actual"].sum() - 1) for c in mape}

    future = pd.period_range("2026-09", periods=C.FORECAST_HORIZON, freq="M")
    rr = run_rate(s, future)
    hw = np.exp(hw_fit(s).forecast(C.FORECAST_HORIZON)).values
    resid = (bt["run_rate_seasonal"] / bt["actual"]).apply(np.log)
    sd = float(resid.std())
    out = pd.DataFrame({"month": future.astype(str), "forecast": rr.round(0),
                        "low_80": (rr * np.exp(-1.28 * sd)).round(0), "high_80": (rr * np.exp(1.28 * sd)).round(0),
                        "holt_winters": hw.round(0), "same_month_2025": [s[m - 12] for m in future]})
    stats = {"mape": mape, "bias": bias, "best_method": min(mape, key=mape.get),
             "q4_forecast_sep_dec": float(rr.sum()), "same_period_2025": float(out["same_month_2025"].sum())}
    return bt, out, stats


# ---------------------------------------------------------------- developer scoring
def developer_scores(pipe, w=C.DEV_WEIGHTS):
    d = pipe.copy()
    d["sales_yoy_pct"] = d["sales_yoy_pct"].fillna(0).clip(-100, 200)
    def pct_rank(s):
        return s.rank(pct=True, method="max")
    d["score"] = 100 * (w["pipeline_units"] * pct_rank(d["pipeline_units"])
                        + w["sales_volume"] * pct_rank(d["sales_12m"])
                        + w["sales_growth"] * pct_rank(d["sales_yoy_pct"])
                        + w["handovers_12m"] * pct_rank(d["handover_units_12m"]))
    d = d.sort_values("score", ascending=False).reset_index(drop=True)
    d["tier"] = np.where(d.index < 20, "A: key account", np.where(d.index < 60, "B: growth", "C: nurture"))
    return d.round(2)


# ---------------------------------------------------------------- main
def main():
    C.OUT_DIR.mkdir(exist_ok=True)
    C.REPORT_DIR.mkdir(exist_ok=True)
    con = sqlite3.connect(C.DB_PATH)
    res = run_sql(con)
    for k, df in res.items():
        df.to_csv(C.OUT_DIR / f"{k}.csv", index=False)
    cm = pd.read_sql("SELECT community, month, n_sales FROM community_monthly", con)

    kpi = market_kpis(res["market_trend"])
    quad = momentum_quadrants(res["community_momentum"])
    quad.to_csv(C.OUT_DIR / "momentum_quadrants.csv", index=False)
    bt, bt_sum = share_backtest(cm)
    bt.to_csv(C.OUT_DIR / "territory_share_backtest.csv", index=False)
    assign, terr = design_territories(res["community_momentum"])
    assign.to_csv(C.OUT_DIR / "territory_assignment.csv", index=False)
    terr.to_csv(C.OUT_DIR / "territories.csv", index=False)
    fbt, fc, fstats = forecast_transactions(res["market_trend"])
    fbt.to_csv(C.OUT_DIR / "forecast_backtest.csv")
    fc.to_csv(C.OUT_DIR / "forecast_sep_dec_2026.csv", index=False)
    dev = developer_scores(res["developer_pipeline"])
    dev.to_csv(C.OUT_DIR / "developer_prospects.csv", index=False)

    pipe_total = dev["pipeline_units"].sum()
    top20 = dev.head(20)
    seas = res["seasonality"].set_index("calendar_month")["seasonality_index"]
    ylds = res["yield_opportunities"]
    q_counts = quad["quadrant"].value_counts().to_dict()
    top_growth = (quad[quad.sales_12m >= 2000].sort_values("sales_growth", ascending=False)
                  .head(5)[["community", "sales_growth", "psf_growth"]].to_dict("records"))
    top_cooling = (quad[quad.sales_12m >= 2000].sort_values("sales_growth")
                   .head(5)[["community", "sales_growth", "psf_growth"]].to_dict("records"))
    top10_share = res["community_momentum"].head(10)["share_of_sales"].sum()

    metrics = {
        "market": kpi,
        "communities_tracked": int(len(res["community_momentum"])),
        "top10_community_share": float(top10_share),
        "quadrant_counts": q_counts, "top_growth": top_growth, "top_cooling": top_cooling,
        "share_backtest": bt_sum.to_dict(),
        "territory_max_dev": float(terr["vs_equal_share"].abs().max()),
        "forecast": fstats, "forecast_months": fc.to_dict("records"),
        "seasonality_peak": {"month": int(seas.idxmax()), "index": float(seas.max())},
        "seasonality_trough": {"month": int(seas.idxmin()), "index": float(seas.min())},
        "developers_with_pipeline": int(len(dev)), "pipeline_units_total": int(pipe_total),
        "top20_dev_pipeline_share": float(top20["pipeline_units"].sum() / pipe_total),
        "top20_dev_handover_units_12m": int(top20["handover_units_12m"].sum()),
        "top5_developers": dev.head(5)[["developer", "pipeline_units", "sales_12m", "score"]].to_dict("records"),
        "yield_hotspots": ylds.head(5)[["community", "yield_pct", "rent_contracts_12m"]].to_dict("records"),
    }
    (C.OUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2, default=float))
    write_report(metrics, terr)
    print(json.dumps({k: metrics[k] for k in ["market", "share_backtest", "territory_max_dev", "forecast",
                                              "top20_dev_pipeline_share", "quadrant_counts"]},
                     indent=2, default=float))
    return metrics


def pct(x, sign=False):
    return f"{x * 100:+.1f}%" if sign else f"{x * 100:.1f}%"


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def write_report(m, terr):
    k, f, s = m["market"], m["forecast"], m["share_backtest"]
    L = [
        "# Findings: Dubai Property Market Intelligence for Portal Inside Sales",
        "",
        "> Real Dubai Land Department open data (CC BY 4.0) via Dubai Data and dataHabibi, through Aug 2026. "
        "Commercial targets in the Excel model are illustrative assumptions.",
        "",
        "## 1. The market has slowed sharply in 2026",
        f"- Registered sales in the last 12 months (Sep 2025 - Aug 2026): **{k['sales_last_12m']:,}**, "
        f"{pct(k['sales_12m_change'], True)} vs the prior 12 months.",
        f"- Jan - Aug 2026: {k['ytd_2026']:,} sales, {pct(k['ytd_change'], True)} vs Jan - Aug 2025 "
        f"(Jan - Apr {pct(k['jan_apr_change'], True)}, May - Aug {pct(k['may_aug_change'], True)}).",
        f"- Prices are holding: median AED {k['psf_latest']:,.0f}/sqft in Aug 2026 ({pct(k['psf_yoy_latest'], True)} YoY, 5-month average).",
        "- **Commercial impact:** agencies see fewer deals, so budget pressure and churn risk rise. "
        "Targets built on 2025 run-rates will be too high.",
        "",
        "## 2. Where demand is moving",
        f"- {m['communities_tracked']} communities tracked; the top 10 hold {pct(m['top10_community_share'])} of transactions.",
        "- Fastest-growing large communities (2,000+ sales): " + ", ".join(
            f"{r['community']} ({pct(r['sales_growth'], True)})" for r in m["top_growth"]) + ".",
        "- Fastest-cooling large communities: " + ", ".join(
            f"{r['community']} ({pct(r['sales_growth'], True)})" for r in m["top_cooling"]) + ".",
        "- Quadrants (500+ sales): " + "; ".join(f"{v} {q.split(':')[0]}" for q, v in m["quadrant_counts"].items()) + ".",
        "",
        "## 3. Territory planning for 12 inside-sales reps",
        "Backtest: predict each community's share of the next 12 months' transactions (two test years).",
        "",
        "| Method | Sales effort misallocated |",
        "|---|---|",
    ] + [f"| {meth} | {pct(v)} |" for meth, v in s.items()] + [
        "",
        f"- Balanced territories: each of the 12 territories is within {pct(m['territory_max_dev'])} of an equal "
        "share of Dubai demand (`outputs/territories.csv`).",
        "",
        "## 4. Sep - Dec 2026 transaction forecast",
        "Rolling one-month-ahead backtest, Sep 2025 - Aug 2026:",
        "",
        "| Method | MAPE | Bias |",
        "|---|---|---|",
        f"| Run-rate x seasonality | {pct(f['mape']['run_rate_seasonal'])} | {pct(f['bias']['run_rate_seasonal'], True)} |",
        f"| Holt-Winters (damped, log) | {pct(f['mape']['holt_winters'])} | {pct(f['bias']['holt_winters'], True)} |",
        f"| Same month last year | {pct(f['mape']['seasonal_naive'])} | {pct(f['bias']['seasonal_naive'], True)} |",
        "",
        "- History-based methods over-forecast the 2026 slowdown; the recent run-rate adjusted for seasonality tracks it best.",
        "- Forecast (run-rate x seasonality): " + ", ".join(
            f"{r['month']}: {r['forecast']:,.0f} ({r['low_80']:,.0f} - {r['high_80']:,.0f})"
            for r in m["forecast_months"]) + f". Total {f['q4_forecast_sep_dec']:,.0f} vs "
            f"{f['same_period_2025']:,.0f} in Sep - Dec 2025 ({pct(f['q4_forecast_sep_dec'] / f['same_period_2025'] - 1, True)}).",
        f"- Seasonality: {MONTHS[m['seasonality_peak']['month'] - 1]} is the strongest month "
        f"(index {m['seasonality_peak']['index']:.2f}), {MONTHS[m['seasonality_trough']['month'] - 1]} the weakest "
        f"({m['seasonality_trough']['index']:.2f}); phase monthly targets with this index.",
        "",
        "## 5. Developer prospects (new-project advertising)",
        f"- {m['developers_with_pipeline']} developers have {m['pipeline_units_total']:,} units under construction; "
        f"the top 20 by prospect score hold {pct(m['top20_dev_pipeline_share'])} of them and "
        f"{m['top20_dev_handover_units_12m']:,} units due for handover in the next 12 months.",
        "- Top 5: " + ", ".join(f"{r['developer']} ({r['pipeline_units']:,} units)" for r in m["top5_developers"]) + ".",
        "",
        "## 6. Rental-yield hotspots (investor campaigns)",
    ] + [f"- {r['community']}: {r['yield_pct']:.2f}% gross yield, {r['rent_contracts_12m']:,} Ejari contracts"
         for r in m["yield_hotspots"]] + [
        "",
        "## Recommendations",
        "1. Reset Q4 2026 targets to the 2026 run-rate, not 2025 history, and phase them with the seasonality index.",
        "2. Allocate reps by last-12-month community demand using the balanced 12-territory plan.",
        "3. Assign the 20 Tier-A developers to key-account managers ahead of their handover launches.",
        "4. Protect agency revenue in cooling communities with lead-quality reviews before renewal.",
        "5. Arm reps with the community fact cards (`outputs/enablement_kit.csv`) and yield hotspots for investor pitches.",
    ]
    (C.REPORT_DIR / "findings.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()
