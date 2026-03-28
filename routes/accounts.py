"""Account Masters, Group Masters, Document Types routes."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.dbf_layer import read_table, write_record, update_record, delete_record, fmt_amount, fmt_date

bp = Blueprint("accounts", __name__, url_prefix="/accounts")


def get_year():
    return session.get("year", "B1")


@bp.route("/")
def index():
    year = get_year()
    accounts = read_table("ACMST", year, order_by="AC_CODE")
    groups = {r["GRCD"]: r["GRHD"] for r in read_table("GRPMST", year)}
    for a in accounts:
        a["_group_name"] = groups.get(str(a.get("AC_GRCD", "") or "").strip(), "")
        a["_yearop_fmt"] = fmt_amount(a.get("YEAROP", 0))
        a["_curbal_fmt"] = fmt_amount(a.get("CURBAL", 0))
    search = request.args.get("q", "").strip().upper()
    if search:
        accounts = [a for a in accounts if search in str(a.get("AC_CODE", "")).upper()
                    or search in str(a.get("AC_HEAD", "")).upper()
                    or search in str(a.get("CITY", "")).upper()]
    return render_template("accounts/index.html", accounts=accounts, year=year, search=search)


@bp.route("/view/<ac_code>")
def view(ac_code):
    year = get_year()
    accounts = read_table("ACMST", year, filters={"AC_CODE": ac_code})
    if not accounts:
        flash("Account not found.", "danger")
        return redirect(url_for("accounts.index"))
    acc = accounts[0]
    groups = read_table("GRPMST", year)
    # Get GL transactions for this account
    gl = read_table("GL", year, filters={"ACCD": ac_code})
    gl.sort(key=lambda r: r.get("DATE") or "")
    return render_template("accounts/view.html", acc=acc, groups=groups, gl=gl,
                           fmt_amount=fmt_amount, fmt_date=fmt_date, year=year)


@bp.route("/add", methods=["GET", "POST"])
def add():
    year = get_year()
    groups = read_table("GRPMST", year)
    if request.method == "POST":
        rec = {
            "AC_CODE": request.form.get("ac_code", "").upper().strip()[:6],
            "AC_HEAD": request.form.get("ac_head", "").upper().strip()[:30],
            "ADDR1": request.form.get("addr1", "").upper().strip()[:30],
            "ADDR2": request.form.get("addr2", "").upper().strip()[:30],
            "CITY": request.form.get("city", "").upper().strip()[:25],
            "REMARK": request.form.get("remark", "").upper().strip()[:20],
            "AC_GRCD": request.form.get("ac_grcd", "").upper().strip()[:4],
            "YEAROP": float(request.form.get("yearop", 0) or 0),
            "CURBAL": float(request.form.get("curbal", 0) or 0),
            "BUDGET": float(request.form.get("budget", 0) or 0),
            "CRLI": int(request.form.get("crli", 0) or 0),
            "AMTRCD": float(request.form.get("amtrcd", 0) or 0),
            "STNO": request.form.get("stno", "").strip()[:25],
        }
        # Check duplicate
        existing = read_table("ACMST", year, filters={"AC_CODE": rec["AC_CODE"]})
        if existing:
            flash(f"Account code {rec['AC_CODE']} already exists.", "danger")
        else:
            if write_record("ACMST", year, rec):
                flash("Account added successfully.", "success")
                return redirect(url_for("accounts.index"))
            else:
                flash("Failed to add account. DBF write error.", "danger")
    return render_template("accounts/form.html", action="Add", groups=groups, acc={}, year=year)


@bp.route("/edit/<ac_code>", methods=["GET", "POST"])
def edit(ac_code):
    year = get_year()
    accounts = read_table("ACMST", year)
    groups = read_table("GRPMST", year)
    acc = next((a for a in accounts if str(a.get("AC_CODE", "")).strip() == ac_code.strip()), None)
    if not acc:
        flash("Account not found.", "danger")
        return redirect(url_for("accounts.index"))
    recno = accounts.index(acc) + 1
    if request.method == "POST":
        updates = {
            "AC_HEAD": request.form.get("ac_head", "").upper().strip()[:30],
            "ADDR1": request.form.get("addr1", "").upper().strip()[:30],
            "ADDR2": request.form.get("addr2", "").upper().strip()[:30],
            "CITY": request.form.get("city", "").upper().strip()[:25],
            "REMARK": request.form.get("remark", "").upper().strip()[:20],
            "AC_GRCD": request.form.get("ac_grcd", "").upper().strip()[:4],
            "YEAROP": float(request.form.get("yearop", 0) or 0),
            "CURBAL": float(request.form.get("curbal", 0) or 0),
            "BUDGET": float(request.form.get("budget", 0) or 0),
            "CRLI": int(request.form.get("crli", 0) or 0),
            "AMTRCD": float(request.form.get("amtrcd", 0) or 0),
            "STNO": request.form.get("stno", "").strip()[:25],
        }
        if update_record("ACMST", year, recno=recno, updates=updates):
            flash("Account updated successfully.", "success")
            return redirect(url_for("accounts.index"))
        else:
            flash("Update failed — showing current data for viewing.", "warning")
    return render_template("accounts/form.html", action="Edit", groups=groups, acc=acc,
                           fmt_amount=fmt_amount, year=year)


# ── Group Masters ──────────────────────────────────────────────────────────────

@bp.route("/groups")
def groups():
    year = get_year()
    grps = read_table("GRPMST", year, order_by="GRCD")
    return render_template("accounts/groups.html", groups=grps, year=year)


@bp.route("/groups/add", methods=["GET", "POST"])
def group_add():
    year = get_year()
    if request.method == "POST":
        rec = {
            "GRCD": request.form.get("grcd", "").upper().strip()[:4],
            "GRHD": request.form.get("grhd", "").upper().strip()[:20],
        }
        existing = read_table("GRPMST", year, filters={"GRCD": rec["GRCD"]})
        if existing:
            flash("Group code already exists.", "danger")
        else:
            write_record("GRPMST", year, rec)
            flash("Group added.", "success")
            return redirect(url_for("accounts.groups"))
    return render_template("accounts/group_form.html", action="Add", grp={}, year=year)


@bp.route("/groups/edit/<grcd>", methods=["GET", "POST"])
def group_edit(grcd):
    year = get_year()
    grps = read_table("GRPMST", year)
    grp = next((g for g in grps if str(g.get("GRCD", "")).strip() == grcd.strip()), None)
    if not grp:
        flash("Group not found.", "danger")
        return redirect(url_for("accounts.groups"))
    recno = grps.index(grp) + 1
    if request.method == "POST":
        updates = {"GRHD": request.form.get("grhd", "").upper().strip()[:20]}
        update_record("GRPMST", year, recno=recno, updates=updates)
        flash("Group updated.", "success")
        return redirect(url_for("accounts.groups"))
    return render_template("accounts/group_form.html", action="Edit", grp=grp, year=year)


# ── Document Types ─────────────────────────────────────────────────────────────

@bp.route("/doctypes")
def doctypes():
    year = get_year()
    docs = read_table("ACDOC", year, order_by="DOCD")
    return render_template("accounts/doctypes.html", docs=docs, year=year)
