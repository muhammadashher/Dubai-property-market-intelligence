"""Tests. Run: pytest -q (after python pipeline.py)."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import config as C  # noqa: E402

O = C.OUT_DIR


def test_raw_data_present_and_recent():
    idx = pd.read_csv(C.RAW / "price_index_monthly.csv")
    assert idx["month"].max() >= C.LATEST_MONTH
    assert not idx["month"].duplicated().any()


def test_community_shares_sum_to_one():
    mom = pd.read_csv(O / "community_momentum.csv")
    assert abs(mom["share_of_sales"].sum() - 1) < 0.01


def test_every_community_in_one_territory():
    a = pd.read_csv(O / "territory_assignment.csv")
    mom = pd.read_csv(O / "community_momentum.csv")
    assert set(a["community"]) == set(mom["community"])
    assert not a["community"].duplicated().any()
    assert a["territory"].nunique() == C.N_TERRITORIES


def test_territories_balanced():
    t = pd.read_csv(O / "territories.csv")
    assert t["vs_equal_share"].abs().max() < 0.10


def test_demand_share_beats_equal_split():
    m = json.loads((O / "metrics.json").read_text())
    s = m["share_backtest"]
    assert s["Last 12 months"] < s["Equal split"]


def test_forecast_backtest_complete():
    b = pd.read_csv(O / "forecast_backtest.csv")
    assert len(b) == 12 and b.notna().all().all()


def test_developer_scores_bounded():
    d = pd.read_csv(O / "developer_prospects.csv")
    assert d["score"].between(0, 100).all()
    assert (d["tier"] == "A: key account").sum() == 20
