"""Configuration for Dubai Property Market Intelligence.

Data: real Dubai Land Department (DLD) open data, aggregated and published under
CC BY 4.0 by Dubai Data (datadubai.ae) and dataHabibi (datahabibi.ae). See data/SOURCES.md.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "dubai_property.db"
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "outputs"
REPORT_DIR = ROOT / "reports"

LATEST_MONTH = "2026-08"          # last complete month in the data
N_TERRITORIES = 12                # inside-sales reps covering Dubai communities
FORECAST_HORIZON = 4              # Sep - Dec 2026

# Illustrative commercial assumptions (NOT from the data) used only in the Excel target model
QUARTERLY_REVENUE_GOAL_AED = 10_000_000
DEMAND_WEIGHTS = {"sales": 0.60, "rents": 0.25, "growth": 0.15}

# Developer prospect score weights
DEV_WEIGHTS = {"pipeline_units": 0.40, "sales_volume": 0.30, "sales_growth": 0.20, "handovers_12m": 0.10}
