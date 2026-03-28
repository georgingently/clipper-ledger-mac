"""Reports: Trial Balance, Account Ledger, Balance Sheet, Outstanding Bills."""
from flask import Blueprint, render_template, request, session, Response
from models.dbf_layer import read_table, fmt_amount, fmt_date, parse_date
import io, datetime

bp = Blueprint("reports", __name__, url_prefix="/reports")


def get_year():
    return session.get("year", "B1")


# ── Trial Balance ──────────────────────────────────────────────────────────────

@bp.route("/trial-balance")
def trial_balance():
    year = get_year()
    accounts = read_table("ACMST", year, order_by="AC_CODE")
    groups = {str(r.get("GRCD", "")).strip(): str(r.get("GRHD", "")).strip()
              for r in read_table("GRPMST", year)}

    # Compute current balance from GL
    gl_records = read_table("GL", year)
    gl_totals = {}
    for r in gl_records:
        accd = str(r.get("ACCD", "")).strip()
        amt = float(r.get("AMNT", 0) or 0)
        drcr = str(r.get("DRCR", "D")).strip().upper()
        if accd not in gl_totals:
            gl_totals[accd] = 0.0
        gl_totals[accd] += amt if drcr == "D" else -amt

    rows = []
    total_dr = 0.0
    total_cr = 0.0
    for acc in accounts:
        code = str(acc.get("AC_CODE", "")).strip()
        yearop = float(acc.get("YEAROP", 0) or 0)
        gl_bal = gl_totals.get(code, 0.0)
        balance = yearop + gl_bal
        grp = str(acc.get("AC_GRCD", "")).strip()
        row = {
            "code": code,
            "head": str(acc.get("AC_HEAD", "")).strip(),
            "group": groups.get(grp, grp),
            "yearop": yearop,
            "gl_movement": gl_bal,
            "balance": balance,
            "_bal_fmt": fmt_amount(abs(balance)),
            "_drcr": "Dr" if balance >= 0 else "Cr",
        }
        if balance >= 0:
            total_dr += balance
        else:
            total_cr += abs(balance)
        rows.append(row)

    return render_template("reports/trial_balance.html", rows=rows,
                           total_dr=fmt_amount(total_dr),
                           total_cr=fmt_amount(total_cr),
                           fmt_amount=fmt_amount, year=year)


# ── Account Ledger (Statement) ─────────────────────────────────────────────────

@bp.route("/ledger")
def ledger():
    year = get_year()
    accd = request.args.get("accd", "").strip()
    from_dt = parse_date(request.args.get("from_dt", ""))
    to_dt = parse_date(request.args.get("to_dt", ""))

    accounts = {str(r.get("AC_CODE", "")).strip(): r
                for r in read_table("ACMST", year)}
    doctypes = {str(r.get("DOCD", "")).strip(): str(r.get("DESC", "")).strip()
                for r in read_table("ACDOC", year)}

    acc_info = accounts.get(accd, {}) if accd else {}

    gl_records = []
    if accd:
        gl_records = read_table("GL", year, filters={"ACCD": accd})
        sl_records = read_table("SL", year, filters={"ACCD": accd})
        # Merge and deduplicate by VRNO+SRNO
        seen = set()
        all_records = []
        for r in gl_records + sl_records:
            key = (str(r.get("VRNO", "")), str(r.get("SRNO", "")), str(r.get("DOCD", "")))
            if key not in seen:
                seen.add(key)
                all_records.append(r)
        gl_records = all_records

    if from_dt:
        gl_records = [r for r in gl_records if r.get("DATE") and r["DATE"] >= from_dt]
    if to_dt:
        gl_records = [r for r in gl_records if r.get("DATE") and r["DATE"] <= to_dt]
    gl_records.sort(key=lambda r: (r.get("DATE") or datetime.date.min, r.get("VRNO") or ""))

    opening_bal = float(acc_info.get("YEAROP", 0) or 0)
    running = opening_bal
    rows = []
    for r in gl_records:
        amt = float(r.get("AMNT", 0) or 0)
        drcr = str(r.get("DRCR", "D")).strip().upper()
        running += amt if drcr == "D" else -amt
        rows.append({
            **r,
            "_date_fmt": fmt_date(r.get("DATE")),
            "_amt_fmt": fmt_amount(amt),
            "_drcr_label": "Dr" if drcr == "D" else "Cr",
            "_running_fmt": fmt_amount(abs(running)),
            "_running_drcr": "Dr" if running >= 0 else "Cr",
            "_doc_name": doctypes.get(str(r.get("DOCD", "")).strip(), ""),
        })

    acmst_list = read_table("ACMST", year, order_by="AC_CODE")
    return render_template("reports/ledger.html",
                           rows=rows, accd=accd, acc_info=acc_info,
                           opening_bal=fmt_amount(abs(opening_bal)),
                           opening_drcr="Dr" if opening_bal >= 0 else "Cr",
                           closing_bal=fmt_amount(abs(running)),
                           closing_drcr="Dr" if running >= 0 else "Cr",
                           acmst_list=acmst_list,
                           from_dt=request.args.get("from_dt", ""),
                           to_dt=request.args.get("to_dt", ""),
                           year=year)


# ── Outstanding Bills ─────────────────────────────────────────────────────────

@bp.route("/outstanding")
def outstanding():
    year = get_year()
    docd = request.args.get("docd", "").strip()
    accounts = {str(r.get("AC_CODE", "")).strip(): str(r.get("AC_HEAD", "")).strip()
                for r in read_table("ACMST", year)}
    doctypes = read_table("ACDOC", year)

    alloc_records = read_table("ALLOC", year)
    if docd:
        alloc_records = [r for r in alloc_records if str(r.get("DOCD", "")).strip() == docd]

    rows = []
    total_bill = 0.0
    total_rcd = 0.0
    for r in alloc_records:
        bill_amt = float(r.get("BILLAMT", 0) or 0)
        rcd_amt = float(r.get("RCDAMT", 0) or 0)
        balance = bill_amt - rcd_amt
        if abs(balance) > 0.01:
            rows.append({
                **r,
                "_ac_name": accounts.get(str(r.get("PARTYCD", "")).strip(), ""),
                "_billdt_fmt": fmt_date(r.get("BILLDT")),
                "_billamt_fmt": fmt_amount(bill_amt),
                "_rcdamt_fmt": fmt_amount(rcd_amt),
                "_balance_fmt": fmt_amount(balance),
            })
            total_bill += bill_amt
            total_rcd += rcd_amt

    rows.sort(key=lambda r: r.get("_ac_name", ""))
    return render_template("reports/outstanding.html", rows=rows,
                           total_bill=fmt_amount(total_bill),
                           total_rcd=fmt_amount(total_rcd),
                           total_balance=fmt_amount(total_bill - total_rcd),
                           doctypes=doctypes, docd=docd, year=year)


# ── Day Book (All transactions for a date) ─────────────────────────────────────

@bp.route("/daybook")
def daybook():
    year = get_year()
    date_str = request.args.get("date", fmt_date(datetime.date.today()))
    sel_date = parse_date(date_str)

    accounts = {str(r.get("AC_CODE", "")).strip(): str(r.get("AC_HEAD", "")).strip()
                for r in read_table("ACMST", year)}
    doctypes = {str(r.get("DOCD", "")).strip(): str(r.get("DESC", "")).strip()
                for r in read_table("ACDOC", year)}

    all_rows = []
    for tbl in ["GL", "CBK01", "BBK27", "JBK81"]:
        recs = read_table(tbl, year)
        for r in recs:
            if r.get("DATE") == sel_date:
                r["_source"] = tbl
                r["_ac_name"] = accounts.get(str(r.get("ACCD", "")).strip(), "")
                r["_doc_name"] = doctypes.get(str(r.get("DOCD", "")).strip(), "")
                r["_amt_fmt"] = fmt_amount(float(r.get("AMNT", 0) or 0))
                all_rows.append(r)

    all_rows.sort(key=lambda r: (r.get("DOCD") or "", r.get("VRNO") or ""))
    total = sum(float(r.get("AMNT", 0) or 0) for r in all_rows)

    return render_template("reports/daybook.html", rows=all_rows,
                           date_str=date_str, sel_date=sel_date,
                           total=fmt_amount(total), year=year)


# ── Sales Summary ─────────────────────────────────────────────────────────────

@bp.route("/sales-summary")
def sales_summary():
    year = get_year()
    from_dt = parse_date(request.args.get("from_dt", ""))
    to_dt = parse_date(request.args.get("to_dt", ""))
    accounts = {str(r.get("AC_CODE", "")).strip(): str(r.get("AC_HEAD", "")).strip()
                for r in read_table("ACMST", year)}

    records = read_table("SREG41", year)
    if from_dt:
        records = [r for r in records if r.get("RCTDTOTK") and r["RCTDTOTK"] >= from_dt]
    if to_dt:
        records = [r for r in records if r.get("RCTDTOTK") and r["RCTDTOTK"] <= to_dt]

    # Party-wise summary
    summary = {}
    for r in records:
        accd = str(r.get("ACCDOTK", "")).strip()
        if accd not in summary:
            summary[accd] = {"accd": accd, "name": accounts.get(accd, accd),
                             "count": 0, "total": 0.0, "sales": 0.0}
        summary[accd]["count"] += 1
        summary[accd]["total"] += float(r.get("TOTAMTTK", 0) or 0)
        summary[accd]["sales"] += float(r.get("SLSAMTTK", 0) or 0)

    rows = sorted(summary.values(), key=lambda r: r["total"], reverse=True)
    for r in rows:
        r["_total_fmt"] = fmt_amount(r["total"])
        r["_sales_fmt"] = fmt_amount(r["sales"])

    grand_total = sum(r["total"] for r in rows)
    return render_template("reports/sales_summary.html", rows=rows,
                           grand_total=fmt_amount(grand_total),
                           from_dt=request.args.get("from_dt", ""),
                           to_dt=request.args.get("to_dt", ""),
                           year=year)
