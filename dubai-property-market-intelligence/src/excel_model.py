"""Build outputs/Territory_Target_Model.xlsx, a live Excel model built on real DLD data.

Sheets: Read Me, Assumptions, Community Demand, Territory Targets, Forecast, Developer Prospects, Fact Cards.
Blue = input/data, black = formula, green = link to another sheet, yellow fill = key lever.
"""
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C  # noqa: E402

F = "Arial"
BLUE, BLACK, GREEN = Font(name=F, color="0000FF"), Font(name=F), Font(name=F, color="008000")
BOLD, TITLE = Font(name=F, bold=True), Font(name=F, bold=True, size=14, color="13322F")
HEAD, HFILL, YELLOW = Font(name=F, bold=True, color="FFFFFF"), PatternFill("solid", fgColor="13322F"), PatternFill("solid", fgColor="FFFF00")
NOTE = Font(name=F, italic=True, color="7F7F7F")
AED, NUM, PCT = 'AED #,##0;(AED #,##0);"-"', '#,##0;(#,##0);"-"', '0.0%;-0.0%;"-"'


def header(ws, row, labels):
    for i, lab in enumerate(labels, 1):
        c = ws.cell(row=row, column=i, value=lab)
        c.font, c.fill = HEAD, HFILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 32


def widths(ws, w):
    for i, x in enumerate(w, 1):
        ws.column_dimensions[get_column_letter(i)].width = x


def put(ws, r, c, v, font=BLACK, fmt=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = font
    if fmt:
        cell.number_format = fmt
    return cell


def main():
    O = C.OUT_DIR
    mom = pd.read_csv(O / "community_momentum.csv")
    assign = pd.read_csv(O / "territory_assignment.csv")
    rents = pd.read_csv(C.RAW / "rents_by_community.csv")
    fc = pd.read_csv(O / "forecast_sep_dec_2026.csv")
    dev = pd.read_csv(O / "developer_pipeline.csv")
    kit = pd.read_csv(O / "enablement_kit.csv")
    seas = pd.read_csv(O / "seasonality.csv")

    wb = Workbook()
    ws = wb.active
    ws.title = "Read Me"
    lines = [("Dubai Territory Target & Prospect Model", TITLE), ("", None),
             ("Built on real Dubai Land Department open data (CC BY 4.0) from Dubai Data and dataHabibi, through Aug 2026.", BLACK),
             ("The quarterly revenue goal and demand weights are illustrative assumptions you can change.", BLACK), ("", None),
             ("How it works", BOLD),
             ("1. Community Demand: demand index = weighted share of sales, rent contracts and growth-adjusted sales.", BLACK),
             ("2. Territory Targets: each rep's Q4 target = territory demand share x goal, phased by the transaction forecast.", BLACK),
             ("3. Developer Prospects: score = weighted percentile of pipeline units, sales, growth and handovers.", BLACK),
             ("", None), ("Colour legend", BOLD), ("Blue text = input or source data", BLUE), ("Black text = formula", BLACK),
             ("Green text = link to another sheet", GREEN), ("Yellow fill = key lever", BLACK)]
    for i, (t, f) in enumerate(lines, 1):
        c = ws.cell(row=i, column=1, value=t)
        if f:
            c.font = f
    ws["A15"].fill = YELLOW
    ws.column_dimensions["A"].width = 115

    # Assumptions
    wa = wb.create_sheet("Assumptions")
    put(wa, 1, 1, "Assumptions", TITLE)
    header(wa, 2, ["Assumption", "Value", "Note"])
    rows = [(3, "Q4 2026 revenue goal (illustrative)", C.QUARTERLY_REVENUE_GOAL_AED, AED, "Assumption, not from data"),
            (5, "Weight: share of sales transactions", C.DEMAND_WEIGHTS["sales"], PCT, "Demand index weight"),
            (6, "Weight: share of rent contracts", C.DEMAND_WEIGHTS["rents"], PCT, "Demand index weight"),
            (7, "Weight: growth-adjusted sales share", C.DEMAND_WEIGHTS["growth"], PCT, "Demand index weight"),
            (8, "Weights check (must be 100%)", "=SUM(B5:B7)", PCT, "Formula"),
            (10, "Growth cap (upper)", 1.5, PCT, "Limits outliers from tiny bases"),
            (11, "Growth floor (lower)", -0.6, PCT, "Limits outliers"),
            (13, "Developer weight: pipeline units", C.DEV_WEIGHTS["pipeline_units"], PCT, "Prospect score"),
            (14, "Developer weight: sales last 12m", C.DEV_WEIGHTS["sales_volume"], PCT, "Prospect score"),
            (15, "Developer weight: sales growth", C.DEV_WEIGHTS["sales_growth"], PCT, "Prospect score"),
            (16, "Developer weight: handovers next 12m", C.DEV_WEIGHTS["handovers_12m"], PCT, "Prospect score")]
    for r, lab, v, fmt, note in rows:
        put(wa, r, 1, lab)
        put(wa, r, 2, v, BLACK if isinstance(v, str) else BLUE, fmt)
        put(wa, r, 3, note, NOTE)
    for r in (3, 5, 6, 7):
        wa.cell(row=r, column=2).fill = YELLOW
    widths(wa, [42, 18, 34])

    # Community Demand
    wc = wb.create_sheet("Community Demand")
    put(wc, 1, 1, "Community demand index (last 12 months to Aug 2026)", TITLE)
    header(wc, 3, ["Community", "Territory", "Sales last 12m", "Rent contracts 12m", "Sales growth YoY",
                   "Sales share", "Rent share", "Growth-adj. sales", "Growth-adj. share", "Demand index",
                   "Q4 target"])
    d = mom.merge(assign[["community", "territory"]], on="community", how="left").merge(
        rents[["name", "contracts"]].rename(columns={"name": "community"}), on="community", how="left")
    d["contracts"] = d["contracts"].fillna(0)
    d["sales_growth"] = d["sales_growth"].fillna(0)
    s0, s1 = 4, 4 + len(d) - 1
    for i, r in enumerate(d.itertuples(), s0):
        put(wc, i, 1, r.community)
        put(wc, i, 2, r.territory)
        put(wc, i, 3, int(r.sales_12m), BLUE, NUM)
        put(wc, i, 4, int(r.contracts), BLUE, NUM)
        put(wc, i, 5, round(float(r.sales_growth), 4), BLUE, PCT)
        put(wc, i, 6, f"=C{i}/SUM($C${s0}:$C${s1})", fmt=PCT)
        put(wc, i, 7, f"=IFERROR(D{i}/SUM($D${s0}:$D${s1}),0)", fmt=PCT)
        put(wc, i, 8, f"=C{i}*(1+MAX(Assumptions!$B$11,MIN(Assumptions!$B$10,E{i})))", GREEN, NUM)
        put(wc, i, 9, f"=H{i}/SUM($H${s0}:$H${s1})", fmt=PCT)
        put(wc, i, 10, f"=Assumptions!$B$5*F{i}+Assumptions!$B$6*G{i}+Assumptions!$B$7*I{i}", GREEN, "0.00%")
        put(wc, i, 11, f"=J{i}/SUM($J${s0}:$J${s1})*Assumptions!$B$3", GREEN, AED)
    t = s1 + 1
    put(wc, t, 1, "Total", BOLD)
    for col, fmt in [(3, NUM), (4, NUM), (6, PCT), (7, PCT), (9, PCT), (10, "0.00%"), (11, AED)]:
        L = get_column_letter(col)
        put(wc, t, col, f"=SUM({L}{s0}:{L}{s1})", BOLD, fmt)
    wc.freeze_panes = "C4"
    widths(wc, [36, 10, 14, 14, 13, 11, 11, 15, 12, 12, 15])

    # Forecast
    wf = wb.create_sheet("Forecast")
    put(wf, 1, 1, "Dubai transactions forecast, Sep - Dec 2026 (run-rate x seasonality)", TITLE)
    header(wf, 3, ["Month", "Forecast", "Low (80%)", "High (80%)", "Same month 2025", "Change vs 2025"])
    for i, r in enumerate(fc.itertuples(), 4):
        put(wf, i, 1, r.month)
        for col, v in [(2, r.forecast), (3, r.low_80), (4, r.high_80), (5, r.same_month_2025)]:
            put(wf, i, col, float(v), BLUE, NUM)
        put(wf, i, 6, f"=B{i}/E{i}-1", fmt=PCT)
    put(wf, 8, 1, "Total", BOLD)
    for col in (2, 3, 4, 5):
        L = get_column_letter(col)
        put(wf, 8, col, f"=SUM({L}4:{L}7)", BOLD, NUM)
    put(wf, 8, 6, "=B8/E8-1", BOLD, PCT)
    put(wf, 10, 1, "Seasonality index (2010-2025)", BOLD)
    header(wf, 11, ["Calendar month", "Index"])
    for i, r in enumerate(seas.itertuples(), 12):
        put(wf, i, 1, int(r.calendar_month))
        put(wf, i, 2, float(r.seasonality_index), BLUE, "0.000")
    widths(wf, [16, 14, 14, 14, 16, 15])

    # Territory Targets
    wt = wb.create_sheet("Territory Targets")
    put(wt, 1, 1, "Q4 2026 targets by territory (12 inside-sales reps)", TITLE)
    header(wt, 3, ["Territory", "Communities", "Sales last 12m", "Demand index share", "Q4 target",
                   "Oct target", "Nov target", "Dec target", "vs equal share"])
    terrs = sorted(assign["territory"].unique())
    cd = f"'Community Demand'!"
    for i, tname in enumerate(terrs, 4):
        put(wt, i, 1, tname)
        put(wt, i, 2, f'=COUNTIF({cd}$B${s0}:$B${s1},A{i})', GREEN, "0")
        put(wt, i, 3, f'=SUMIF({cd}$B${s0}:$B${s1},A{i},{cd}$C${s0}:$C${s1})', GREEN, NUM)
        put(wt, i, 4, f'=SUMIF({cd}$B${s0}:$B${s1},A{i},{cd}$J${s0}:$J${s1})/SUM({cd}$J${s0}:$J${s1})', GREEN, PCT)
        put(wt, i, 5, f"=D{i}*Assumptions!$B$3", GREEN, AED)
        for col, frow in [(6, 5), (7, 6), (8, 7)]:
            put(wt, i, col, f"=E{i}*Forecast!$B${frow}/SUM(Forecast!$B$5:$B$7)", GREEN, AED)
        put(wt, i, 9, f"=D{i}/(1/COUNTA($A$4:$A${3 + len(terrs)}))-1", fmt=PCT)
    e = 3 + len(terrs)
    put(wt, e + 1, 1, "Total", BOLD)
    for col, fmt in [(2, "0"), (3, NUM), (4, PCT), (5, AED), (6, AED), (7, AED), (8, AED)]:
        L = get_column_letter(col)
        put(wt, e + 1, col, f"=SUM({L}4:{L}{e})", BOLD, fmt)
    put(wt, e + 3, 1, "Check: targets = goal", BOLD)
    put(wt, e + 3, 5, f'=IF(ABS(E{e + 1}-Assumptions!B3)<1,"OK","CHECK")', BOLD)
    widths(wt, [11, 13, 15, 17, 16, 15, 15, 15, 14])

    # Developer Prospects
    wd = wb.create_sheet("Developer Prospects")
    put(wd, 1, 1, "Developer prospect scoring (active DLD project pipeline)", TITLE)
    header(wd, 3, ["Developer", "Active projects", "Pipeline units", "Handover units next 12m", "Sales last 12m",
                   "Sales YoY %", "Prospect score", "Rank"])
    dv = dev.copy()
    dv["sales_yoy_pct"] = dv["sales_yoy_pct"].fillna(0).clip(-100, 200)
    d0, d1 = 4, 4 + len(dv) - 1
    for i, r in enumerate(dv.itertuples(), d0):
        put(wd, i, 1, r.developer)
        for col, v, fmt in [(2, r.active_projects, "0"), (3, r.pipeline_units, NUM), (4, r.handover_units_12m, NUM),
                            (5, r.sales_12m, NUM), (6, round(float(r.sales_yoy_pct), 1), "0.0")]:
            put(wd, i, col, float(v), BLUE, fmt)
        pr = lambda L: f'COUNTIF(${L}${d0}:${L}${d1},"<="&{L}{i})/COUNT(${L}${d0}:${L}${d1})'
        put(wd, i, 7, f"=100*(Assumptions!$B$13*{pr('C')}+Assumptions!$B$14*{pr('E')}"
                      f"+Assumptions!$B$15*{pr('F')}+Assumptions!$B$16*{pr('D')})", GREEN, "0.0")
        put(wd, i, 8, f"=RANK(G{i},$G${d0}:$G${d1})", fmt="0")
    wd.freeze_panes = "B4"
    widths(wd, [44, 10, 13, 14, 13, 11, 12, 8])

    # Fact Cards
    wk = wb.create_sheet("Fact Cards")
    put(wk, 1, 1, "Sales enablement fact cards: top 25 communities (last 12 months)", TITLE)
    cols = ["community", "sales_12m", "price_median", "psf_median", "psf_yoy", "sales_yoy", "offplan_share",
            "rent_contracts_12m", "rent_median", "yield_pct"]
    labels = ["Community", "Sales 12m", "Median price", "Median AED/sqft", "AED/sqft YoY %", "Sales YoY %",
              "Off-plan share %", "Rent contracts", "Median annual rent", "Gross yield %"]
    header(wk, 3, labels)
    fmts = [None, NUM, AED, NUM, "0.0", "0.0", "0.0", NUM, AED, "0.00"]
    for i, r in enumerate(kit[cols].itertuples(index=False), 4):
        for j, (v, fmt) in enumerate(zip(r, fmts), 1):
            put(wk, i, j, None if pd.isna(v) else v, BLACK if j == 1 else BLUE, fmt)
    put(wk, 4 + len(kit) + 1, 1, "Source: Dubai Data (datadubai.ae), DLD open data, CC BY 4.0, data through 2026-09-24.", NOTE)
    widths(wk, [36, 11, 15, 14, 13, 12, 14, 14, 16, 12])

    out = C.OUT_DIR / "Territory_Target_Model.xlsx"
    wb.save(out)
    print(f"Excel model written to {out}")


if __name__ == "__main__":
    main()
