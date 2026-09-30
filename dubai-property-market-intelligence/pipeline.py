"""Run everything: raw DLD CSVs -> SQLite -> SQL + Python analysis -> Excel model."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import analysis     # noqa: E402
import build_db     # noqa: E402
import excel_model  # noqa: E402

if __name__ == "__main__":
    print("1/3 Building SQLite database from real DLD open data ...")
    build_db.main()
    print("2/3 Running SQL and Python analysis ...")
    analysis.main()
    print("3/3 Building Excel territory & prospect model ...")
    excel_model.main()
    print("Done. Findings: reports/findings.md | Dashboard: streamlit run app.py")
