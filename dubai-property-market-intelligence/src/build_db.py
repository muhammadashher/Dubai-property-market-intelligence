"""Load the raw DLD open-data CSVs into SQLite (data/dubai_property.db)."""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C  # noqa: E402

TABLES = {
    "index_monthly": "price_index_monthly.csv", "rent_index_monthly": "rent_index_monthly.csv",
    "market_monthly": "market_monthly.csv", "market_yearly": "market_yearly.csv",
    "community_monthly": "community_monthly.csv", "community_yearly": "community_yearly.csv",
    "communities": "communities.csv", "community_bedrooms": "community_bedrooms.csv",
    "rents_by_community": "rents_by_community.csv", "yields_by_community": "yields_by_community.csv",
    "areas": "areas.csv", "developers": "developers.csv", "projects": "projects.csv",
}


def main():
    if C.DB_PATH.exists():
        C.DB_PATH.unlink()
    with sqlite3.connect(C.DB_PATH) as con:
        for table, f in TABLES.items():
            df = pd.read_csv(C.RAW / f)
            df.columns = [c.strip() for c in df.columns]
            df.to_sql(table, con, index=False)
        con.execute("CREATE INDEX idx_cm ON community_monthly(community, month)")
    print(f"SQLite database written to {C.DB_PATH} ({len(TABLES)} tables)")


if __name__ == "__main__":
    main()
