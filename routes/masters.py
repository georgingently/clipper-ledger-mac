"""Item Master, Agent Master, Address Book, Tax Master routes."""
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from models.dbf_layer import read_table, write_record, update_record, fmt_amount

bp = Blueprint("masters", __name__, url_prefix="/masters")


def get_year():
    return session.get("year", "B1")


# ── Item Master ────────────────────────────────────────────────────────────────

@bp.route("/items")
def items():
    year = get_year()
    search = request.args.get("q", "").strip().upper()
    itype = request.args.get("type", "").strip().upper()

    records = read_table("ITMST", year, order_by="ITCD")
    if search:
        records = [r for r in records if search in str(r.get("ITCD", "")).upper()
                   or search in str(r.get("ITDESC", "")).upper()
                   or search in str(r.get("GNAME", "")).upper()]
    if itype:
        records = [r for r in records if str(r.get("TYPE", "")).strip().upper() == itype]

    for r in records:
        r["_curqty_fmt"] = "{:,.3f}".format(float(r.get("CURQTY", 0) or 0))
        r["_opstk_fmt"] = "{:,.3f}".format(float(r.get("OPSTK", 0) or 0))
        r["_salrate_fmt"] = fmt_amount(r.get("SALRATE", 0))
        r["_purrate_fmt"] = fmt_amount(r.get("PURRATE", 0))

    return render_template("masters/items.html", records=records,
                           search=search, itype=itype, year=year)


@bp.route("/items/view/<itcd>")
def item_view(itcd):
    year = get_year()
    all_items = read_table("ITMST", year)
    item = next((i for i in all_items if str(i.get("ITCD", "")).strip() == itcd.strip()), None)
    if not item:
        flash("Item not found.", "danger")
        return redirect(url_for("masters.items"))

    # Get sales history for this item
    lines = read_table("SRPRFL", year, filters={"PRODCD": itcd})
    lines.sort(key=lambda r: r.get("RCTDT") or "")
    from models.dbf_layer import fmt_date
    for line in lines:
        line["_date_fmt"] = fmt_date(line.get("RCTDT"))
        line["_val_fmt"] = fmt_amount(line.get("VALUE", 0))

    return render_template("masters/item_view.html", item=item, lines=lines,
                           fmt_amount=fmt_amount, year=year)


# ── Agent Master ───────────────────────────────────────────────────────────────

@bp.route("/agents")
def agents():
    year = get_year()
    records = read_table("AGMST", year, order_by="AGCD")
    accounts = {str(r.get("AC_CODE", "")).strip(): str(r.get("AC_HEAD", "")).strip()
                for r in read_table("ACMST", year)}
    for r in records:
        r["_ac_name"] = accounts.get(str(r.get("ACCD", "")).strip(), "")
    return render_template("masters/agents.html", records=records, year=year)


@bp.route("/agents/add", methods=["GET", "POST"])
def agent_add():
    year = get_year()
    acmst_list = read_table("ACMST", year, order_by="AC_CODE")
    if request.method == "POST":
        rec = {
            "AGCD": request.form.get("agcd", "").upper().strip()[:6],
            "AGNM": request.form.get("agnm", "").upper().strip()[:30],
            "ACCD": request.form.get("accd", "").upper().strip()[:6],
            "PHONE": request.form.get("phone", "").strip()[:15],
        }
        write_record("AGMST", year, rec)
        flash("Agent added.", "success")
        return redirect(url_for("masters.agents"))
    return render_template("masters/agent_form.html", action="Add", agent={},
                           acmst_list=acmst_list, year=year)


# ── Address Book ───────────────────────────────────────────────────────────────

@bp.route("/addresses")
def addresses():
    year = get_year()
    search = request.args.get("q", "").strip().upper()
    records = read_table("ADDRES", year, order_by="NAME")
    if search:
        records = [r for r in records if search in str(r.get("NAME", "")).upper()
                   or search in str(r.get("PLACE", "")).upper()
                   or search in str(r.get("MOBILE", "")).upper()]
    return render_template("masters/addresses.html", records=records,
                           search=search, year=year)


# ── Tax Master ─────────────────────────────────────────────────────────────────

@bp.route("/tax")
def tax():
    year = get_year()
    records = read_table("TAXMST", year)
    accounts = {str(r.get("AC_CODE", "")).strip(): str(r.get("AC_HEAD", "")).strip()
                for r in read_table("ACMST", year)}
    for r in records:
        r["_ac_name"] = accounts.get(str(r.get("ACCD", "")).strip(), "")
    return render_template("masters/tax.html", records=records, year=year)


# ── Bill Allocation ────────────────────────────────────────────────────────────

@bp.route("/allocation")
def allocation():
    year = get_year()
    accd = request.args.get("accd", "").strip()
    accounts = {str(r.get("AC_CODE", "")).strip(): str(r.get("AC_HEAD", "")).strip()
                for r in read_table("ACMST", year)}

    records = read_table("ALLOC", year)
    if accd:
        records = [r for r in records if str(r.get("PARTYCD", "")).strip() == accd]
    records.sort(key=lambda r: r.get("BILLDT") or "")

    from models.dbf_layer import fmt_date
    for r in records:
        r["_ac_name"] = accounts.get(str(r.get("PARTYCD", "")).strip(), "")
        r["_billdt_fmt"] = fmt_date(r.get("BILLDT"))
        r["_billamt_fmt"] = fmt_amount(r.get("BILLAMT", 0))
        r["_rcdamt_fmt"] = fmt_amount(r.get("RCDAMT", 0))
        r["_balance"] = fmt_amount(
            float(r.get("BILLAMT", 0) or 0) - float(r.get("RCDAMT", 0) or 0))

    acmst_list = read_table("ACMST", year, order_by="AC_CODE")
    return render_template("masters/allocation.html", records=records,
                           acmst_list=acmst_list, accd=accd, year=year)
