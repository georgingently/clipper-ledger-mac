"""General Ledger, Cash Book, Bank Book, Journal Book routes."""
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from models.dbf_layer import read_table, fmt_amount, fmt_date, parse_date

bp = Blueprint("ledger", __name__, url_prefix="/ledger")


def get_year():
    return session.get("year", "B1")


def get_accounts(year):
    return {str(r.get("AC_CODE", "")).strip(): str(r.get("AC_HEAD", "")).strip()
            for r in read_table("ACMST", year)}


def get_doctypes(year):
    return {str(r.get("DOCD", "")).strip(): str(r.get("DESC", "")).strip()
            for r in read_table("ACDOC", year)}


# ── General Ledger ─────────────────────────────────────────────────────────────

@bp.route("/gl")
def gl():
    year = get_year()
    accd = request.args.get("accd", "").strip()
    from_dt = parse_date(request.args.get("from_dt", ""))
    to_dt = parse_date(request.args.get("to_dt", ""))
    accounts = get_accounts(year)
    doctypes = get_doctypes(year)

    records = read_table("GL", year)
    if accd:
        records = [r for r in records if str(r.get("ACCD", "")).strip() == accd]
    if from_dt:
        records = [r for r in records if r.get("DATE") and r["DATE"] >= from_dt]
    if to_dt:
        records = [r for r in records if r.get("DATE") and r["DATE"] <= to_dt]
    records.sort(key=lambda r: (r.get("DATE") or "", r.get("VRNO") or ""))

    # Running balance
    running = 0.0
    for r in records:
        amt = float(r.get("AMNT", 0) or 0)
        drcr = str(r.get("DRCR", "D")).strip().upper()
        running += amt if drcr == "D" else -amt
        r["_running"] = running
        r["_ac_name"] = accounts.get(str(r.get("ACCD", "")).strip(), "")
        r["_doc_name"] = doctypes.get(str(r.get("DOCD", "")).strip(), "")
        r["_date_fmt"] = fmt_date(r.get("DATE"))
        r["_amt_fmt"] = fmt_amount(amt)

    acmst_list = read_table("ACMST", year, order_by="AC_CODE")
    return render_template("ledger/gl.html", records=records, accd=accd,
                           acmst_list=acmst_list, accounts=accounts,
                           from_dt=request.args.get("from_dt", ""),
                           to_dt=request.args.get("to_dt", ""),
                           fmt_amount=fmt_amount, year=year)


# ── Cash Book ──────────────────────────────────────────────────────────────────

@bp.route("/cashbook")
def cashbook():
    year = get_year()
    from_dt = parse_date(request.args.get("from_dt", ""))
    to_dt = parse_date(request.args.get("to_dt", ""))
    accounts = get_accounts(year)
    doctypes = get_doctypes(year)

    # CBK01 is the main cash book data file
    records = read_table("CBK01", year)
    if not records:
        records = read_table("CBK", year)
    if from_dt:
        records = [r for r in records if r.get("DATE") and r["DATE"] >= from_dt]
    if to_dt:
        records = [r for r in records if r.get("DATE") and r["DATE"] <= to_dt]
    records.sort(key=lambda r: (r.get("DATE") or "", r.get("VRNO") or ""))

    receipts_total = sum(float(r.get("AMNT", 0) or 0)
                         for r in records if str(r.get("DRCR", "")).strip().upper() == "D")
    payments_total = sum(float(r.get("AMNT", 0) or 0)
                         for r in records if str(r.get("DRCR", "")).strip().upper() == "C")

    for r in records:
        r["_ac_name"] = accounts.get(str(r.get("ACCD", "")).strip(), "")
        r["_doc_name"] = doctypes.get(str(r.get("DOCD", "")).strip(), "")
        r["_date_fmt"] = fmt_date(r.get("DATE"))
        r["_amt_fmt"] = fmt_amount(float(r.get("AMNT", 0) or 0))

    return render_template("ledger/cashbook.html", records=records,
                           receipts_total=fmt_amount(receipts_total),
                           payments_total=fmt_amount(payments_total),
                           from_dt=request.args.get("from_dt", ""),
                           to_dt=request.args.get("to_dt", ""),
                           year=year)


# ── Bank Book ──────────────────────────────────────────────────────────────────

@bp.route("/bankbook")
def bankbook():
    year = get_year()
    bank_no = request.args.get("bank", "27")  # default BBK27
    from_dt = parse_date(request.args.get("from_dt", ""))
    to_dt = parse_date(request.args.get("to_dt", ""))
    accounts = get_accounts(year)

    # Try numbered bank book files
    bbk_tables = []
    for i in range(21, 35):
        cnt_path = f"BBK{i}"
        from models.dbf_layer import count_records
        if count_records(cnt_path, year) > 0:
            bbk_tables.append(str(i))

    records = read_table(f"BBK{bank_no}", year) if bank_no else []
    if from_dt:
        records = [r for r in records if r.get("DATE") and r["DATE"] >= from_dt]
    if to_dt:
        records = [r for r in records if r.get("DATE") and r["DATE"] <= to_dt]
    records.sort(key=lambda r: (r.get("DATE") or "", r.get("VRNO") or ""))

    for r in records:
        r["_ac_name"] = accounts.get(str(r.get("ACCD", "")).strip(), "")
        r["_date_fmt"] = fmt_date(r.get("DATE"))
        r["_amt_fmt"] = fmt_amount(float(r.get("AMNT", 0) or 0))

    receipts = sum(float(r.get("AMNT", 0) or 0)
                   for r in records if str(r.get("DRCR", "")).strip().upper() == "D")
    payments = sum(float(r.get("AMNT", 0) or 0)
                   for r in records if str(r.get("DRCR", "")).strip().upper() == "C")

    return render_template("ledger/bankbook.html", records=records,
                           bbk_tables=bbk_tables, bank_no=bank_no,
                           receipts=fmt_amount(receipts), payments=fmt_amount(payments),
                           from_dt=request.args.get("from_dt", ""),
                           to_dt=request.args.get("to_dt", ""),
                           year=year)


# ── Journal Book ──────────────────────────────────────────────────────────────

@bp.route("/journal")
def journal():
    year = get_year()
    from_dt = parse_date(request.args.get("from_dt", ""))
    to_dt = parse_date(request.args.get("to_dt", ""))
    accounts = get_accounts(year)

    records = read_table("JBK81", year)
    if not records:
        records = read_table("JBK", year)
    if from_dt:
        records = [r for r in records if r.get("DATE") and r["DATE"] >= from_dt]
    if to_dt:
        records = [r for r in records if r.get("DATE") and r["DATE"] <= to_dt]
    records.sort(key=lambda r: (r.get("DATE") or "", r.get("VRNO") or ""))

    for r in records:
        r["_ac_name"] = accounts.get(str(r.get("ACCD", "")).strip(), "")
        r["_date_fmt"] = fmt_date(r.get("DATE"))
        r["_amt_fmt"] = fmt_amount(float(r.get("AMNT", 0) or 0))

    return render_template("ledger/journal.html", records=records,
                           from_dt=request.args.get("from_dt", ""),
                           to_dt=request.args.get("to_dt", ""),
                           year=year)


# ── Sub Ledger ─────────────────────────────────────────────────────────────────

@bp.route("/sl")
def sl():
    year = get_year()
    accd = request.args.get("accd", "").strip()
    from_dt = parse_date(request.args.get("from_dt", ""))
    to_dt = parse_date(request.args.get("to_dt", ""))
    accounts = get_accounts(year)
    doctypes = get_doctypes(year)

    records = read_table("SL", year)
    if accd:
        records = [r for r in records if str(r.get("ACCD", "")).strip() == accd]
    if from_dt:
        records = [r for r in records if r.get("DATE") and r["DATE"] >= from_dt]
    if to_dt:
        records = [r for r in records if r.get("DATE") and r["DATE"] <= to_dt]
    records.sort(key=lambda r: (r.get("DATE") or "", r.get("VRNO") or ""))

    running = 0.0
    for r in records:
        amt = float(r.get("AMNT", 0) or 0)
        drcr = str(r.get("DRCR", "D")).strip().upper()
        running += amt if drcr == "D" else -amt
        r["_running"] = running
        r["_ac_name"] = accounts.get(str(r.get("ACCD", "")).strip(), "")
        r["_doc_name"] = doctypes.get(str(r.get("DOCD", "")).strip(), "")
        r["_date_fmt"] = fmt_date(r.get("DATE"))
        r["_amt_fmt"] = fmt_amount(amt)

    acmst_list = read_table("ACMST", year, order_by="AC_CODE")
    return render_template("ledger/sl.html", records=records, accd=accd,
                           acmst_list=acmst_list, accounts=accounts,
                           from_dt=request.args.get("from_dt", ""),
                           to_dt=request.args.get("to_dt", ""),
                           fmt_amount=fmt_amount, year=year)
