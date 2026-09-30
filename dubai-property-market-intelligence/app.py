"""Self-service dashboard on real DLD data. Run:  streamlit run app.py"""
import json

import pandas as pd
import plotly.express as px
import streamlit as st

import config as C

st.set_page_config(page_title="Dubai Property Market Intelligence", page_icon="🏙️", layout="wide")


@st.cache_data
def load(name):
    return pd.read_csv(C.OUT_DIR / f"{name}.csv")


if not (C.OUT_DIR / "metrics.json").exists():
    st.error("Outputs not found. Run `python pipeline.py` first.")
    st.stop()

m = json.loads((C.OUT_DIR / "metrics.json").read_text())
trend, mom, quad = load("market_trend"), load("community_momentum"), load("momentum_quadrants")
terr, assign = load("territories"), load("territory_assignment")
fbt, fc = load("forecast_backtest"), load("forecast_sep_dec_2026")
dev, ylds, kit, seas = load("developer_prospects"), load("yield_opportunities"), load("enablement_kit"), load("seasonality")

st.title("Dubai Property Market Intelligence for Portal Inside Sales")
st.caption("Real Dubai Land Department open data (CC BY 4.0) via Dubai Data and dataHabibi, through Aug 2026.")
k = m["market"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sales, last 12 months", f"{k['sales_last_12m']:,}", f"{k['sales_12m_change']:.1%}")
c2.metric("Jan-Aug 2026 vs 2025", f"{k['ytd_2026']:,}", f"{k['ytd_change']:.1%}")
c3.metric("Median AED/sqft (Aug 2026)", f"{k['psf_latest']:,.0f}", f"{k['psf_yoy_latest']:.1%}")
c4.metric("Sep-Dec 2026 forecast", f"{m['forecast']['q4_forecast_sep_dec']:,.0f}",
          f"{m['forecast']['q4_forecast_sep_dec'] / m['forecast']['same_period_2025'] - 1:.1%}")

tabs = st.tabs(["Market", "Community momentum", "Territories", "Forecast", "Developer prospects", "Fact cards"])
with tabs[0]:
    t = trend[trend.month >= "2016-01"]
    st.plotly_chart(px.bar(t, x="month", y="sales_count", title="Registered sales per month"), width="stretch")
    st.plotly_chart(px.line(t, x="month", y="median_aed_per_sqft", title="Median AED per sqft"), width="stretch")
    st.plotly_chart(px.bar(seas, x="calendar_month", y="seasonality_index", title="Seasonality index (2010-2025)"),
                    width="stretch")
with tabs[1]:
    min_sales = st.slider("Minimum sales in last 12 months", 200, 5000, 500, 100)
    q = quad[quad.sales_12m >= min_sales]
    fig = px.scatter(q, x="sales_growth", y="psf_growth", size="sales_12m", color="quadrant", hover_name="community",
                     title="Volume growth vs price growth (last 12m vs prior 12m)")
    fig.add_hline(y=0, line_dash="dot"); fig.add_vline(x=0, line_dash="dot")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(mom, width="stretch", hide_index=True)
with tabs[2]:
    st.subheader("Backtest: share of sales effort misallocated")
    st.dataframe(pd.Series(m["share_backtest"], name="misallocated").to_frame(), width="stretch")
    st.plotly_chart(px.bar(terr, x="territory", y="demand_share", hover_data=["anchor_community", "communities"],
                           title="Balanced territories: share of Dubai demand"), width="stretch")
    pick = st.selectbox("Territory", terr.territory)
    st.dataframe(assign[assign.territory == pick], width="stretch", hide_index=True)
with tabs[3]:
    b = fbt.melt(id_vars="month", value_vars=["actual", "run_rate_seasonal", "holt_winters", "seasonal_naive"])
    st.plotly_chart(px.line(b, x="month", y="value", color="variable",
                            title="One-month-ahead backtest, Sep 2025 - Aug 2026"), width="stretch")
    st.dataframe(pd.DataFrame({"MAPE": m["forecast"]["mape"], "Bias": m["forecast"]["bias"]}), width="stretch")
    st.dataframe(fc, width="stretch", hide_index=True)
with tabs[4]:
    tier = st.multiselect("Tier", sorted(dev.tier.unique()), default=["A: key account"])
    st.dataframe(dev[dev.tier.isin(tier)], width="stretch", hide_index=True)
    st.plotly_chart(px.scatter(dev.head(60), x="pipeline_units", y="sales_12m", size="handover_units_12m",
                               color="tier", hover_name="developer", title="Top 60 developer prospects"), width="stretch")
with tabs[5]:
    st.dataframe(kit, width="stretch", hide_index=True)
    st.subheader("Rental-yield hotspots")
    st.dataframe(ylds, width="stretch", hide_index=True)
