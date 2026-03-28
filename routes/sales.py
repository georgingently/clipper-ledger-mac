"""Sales Register and Purchase Register routes."""
from flask import Blueprint, render_template, request, session
from models.dbf_layer import read_table, fmt_amount, fmt_date, parse_date

bp = Blueprint("sales", __name__, url_prefix="/sales")


def get_year():
    return session.get("year", "B1")


def get_accounts(year):
    return {str(r.get("AC_CODE", "")).strip(): str(r.get("AC_HEAD", "")).strip()
            for r in read_table("ACMST", year)}


def get_items(year):
    return {str(r.get("ITCD", "")).strip(): str(r.get("ITDESC", "")).strip()
            for r in read_table("ITMST", year)}


# ── Sales Register ─────────────────────────────────────────────────────────────

@bp.route("/")
def index():
    year = get_year()
    from_dt = parse_date(request.args.get("from_dt", ""))
    to_dt = parse_date(request.args.get("to_dt", ""))
    accd = request.args.get("accd", "").strip()
    accounts = get_accounts(year)

    # SREG41 is the main sales register
    records = read_table("SREG41", year)
    if not records:
        records = read_table("SREG", year)

    if from_dt:
        records = [r for r in records if r.get("RCTDTOTK") and r["RCTDTOTK"] >= from_dt]
    if to_dt:
        records = [r for r in records if r.get("RCTDTOTK") and r["RCTDTOTK"] <= to_dt]
    if accd:
        records = [r for r in records if str(r.get("ACCDOTK", "")).strip() == accd]

    records.sort(key=lambda r: (r.get("RCTDTOTK") or "", r.get("SBILLNOTK") or ""))

    total_amt = sum(float(r.get("TOTAMTTK", 0) or 0) for r in records)
    total_sls = sum(float(r.get("SLSAMTTK", 0) or 0) for r in records)

    for r in records:
        r["_ac_name"] = accounts.get(str(r.get("ACCDOTK", "")).strip(), "")
        r["_date_fmt"] = fmt_date(r.get("RCTDTOTK"))
        r["_totamt_fmt"] = fmt_amount(r.get("TOTAMTTK", 0))
        r["_slsamt_fmt"] = fmt_amount(r.get("SLSAMTTK", 0))

    acmst_list = read_table("ACMST", year, order_by="AC_CODE")
    return render_template("sales/index.html", records=records,
                           total_amt=fmt_amount(total_amt),
                           total_sls=fmt_amount(total_sls),
                           acmst_list=acmst_list, accd=accd,
                           from_dt=request.args.get("from_dt", ""),
                           to_dt=request.args.get("to_dt", ""),
                           year=year)


@bp.route("/detail/<bill_no>")
def detail(bill_no):
    year = get_year()
    accounts = get_accounts(year)
    items = get_items(year)

    bills = read_table("SREG41", year, filters={"SBILLNOTK": bill_no})
    if not bills:
        bills = read_table("SREG", year, filters={"SBILLNOTK": bill_no})
    bill = bills[0] if bills else {}

    # Get line items from SRPRFL
    lines = read_table("SRPRFL", year, filters={"SBILLNO": bill_no})
    for line in lines:
        line["_item_name"] = items.get(str(line.get("PRODCD", "")).strip(), "")
        line["_value_fmt"] = fmt_amount(line.get("VALUE", 0))
        line["_rate_fmt"] = fmt_amount(line.get("RATE", 0))

    if bill:
        bill["_ac_name"] = accounts.get(str(bill.get("ACCDOTK", "")).strip(), "")
        bill["_date_fmt"] = fmt_date(bill.get("RCTDTOTK"))
        bill["_totamt_fmt"] = fmt_amount(bill.get("TOTAMTTK", 0))
        bill["_slsamt_fmt"] = fmt_amount(bill.get("SLSAMTTK", 0))

    return render_template("sales/detail.html", bill=bill, lines=lines,
                           fmt_amount=fmt_amount, year=year)


# ── Purchase Register ──────────────────────────────────────────────────────────

@bp.route("/purchase")
def purchase():
    year = get_year()
    from_dt = parse_date(request.args.get("from_dt", ""))
    to_dt = parse_date(request.args.get("to_dt", ""))
    accounts = get_accounts(year)

    records = read_table("PREG61", year)
    if not records:
        records = read_table("PREG", year)

    if from_dt:
        records = [r for r in records if r.get("RCTDT") and r["RCTDT"] >= from_dt]
    if to_dt:
        records = [r for r in records if r.get("RCTDT") and r["RCTDT"] <= to_dt]

    records.sort(key=lambda r: (r.get("RCTDT") or "", r.get("PBILLNO") or ""))
    total = sum(float(r.get("PURAMT", 0) or 0) for r in records)

    for r in records:
        r["_ac_name"] = accounts.get(str(r.get("ACCD", "")).strip(), "")
        r["_rctdt_fmt"] = fmt_date(r.get("RCTDT"))
        r["_billdt_fmt"] = fmt_date(r.get("BILLDT"))
        r["_puramt_fmt"] = fmt_amount(r.get("PURAMT", 0))

    acmst_list = read_table("ACMST", year, order_by="AC_CODE")
    return render_template("sales/purchase.html", records=records,
                           total=fmt_amount(total),
                           acmst_list=acmst_list,
                           from_dt=request.args.get("from_dt", ""),
                           to_dt=request.args.get("to_dt", ""),
                           year=year)


# ── Stock / Item Sales Analysis ────────────────────────────────────────────────

@bp.route("/itemwise")
def itemwise():
    year = get_year()
    from_dt = parse_date(request.args.get("from_dt", ""))
    to_dt = parse_date(request.args.get("to_dt", ""))
    items = get_items(year)

    lines = read_table("SRPRFL", year)
    if from_dt:
        lines = [r for r in lines if r.get("RCTDT") and r["RCTDT"] >= from_dt]
    if to_dt:
        lines = [r for r in lines if r.get("RCTDT") and r["RCTDT"] <= to_dt]

    # Aggregate by item
    summary = {}
    for line in lines:
        itcd = str(line.get("PRODCD", "")).strip()
        if itcd not in summary:
            summary[itcd] = {"itcd": itcd, "name": items.get(itcd, itcd),
                             "qty": 0.0, "value": 0.0, "count": 0}
        summary[itcd]["qty"] += float(line.get("NETQTY", 0) or 0)
        summary[itcd]["value"] += float(line.get("VALUE", 0) or 0)
        summary[itcd]["count"] += 1

    rows = sorted(summary.values(), key=lambda r: r["value"], reverse=True)
    for r in rows:
        r["_qty_fmt"] = "{:,.3f}".format(r["qty"])
        r["_val_fmt"] = fmt_amount(r["value"])

    return render_template("sales/itemwise.html", rows=rows,
                           from_dt=request.args.get("from_dt", ""),
                           to_dt=request.args.get("to_dt", ""),
                           year=year)
