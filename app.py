"""
GEORGIN Accounting System - Mac Edition
Flask web application to replace the original Clipper/DOS software.
All data is read from the original DBF files — nothing is migrated or changed.
"""
import os
import datetime
from flask import Flask, render_template, request, session, redirect, url_for, flash
from models.dbf_layer import (read_table, get_available_years, get_branch_list,
                               fmt_amount, fmt_date, DATA_DIR, DEFAULT_YEAR)

app = Flask(__name__)
app.secret_key = os.urandom(32)

# Register blueprints
from routes.accounts import bp as accounts_bp
from routes.ledger import bp as ledger_bp
from routes.sales import bp as sales_bp
from routes.masters import bp as masters_bp
from routes.reports import bp as reports_bp

app.register_blueprint(accounts_bp)
app.register_blueprint(ledger_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(masters_bp)
app.register_blueprint(reports_bp)


@app.context_processor
def inject_globals():
    return {
        "current_year": session.get("year", DEFAULT_YEAR),
        "app_title": "GEORGIN Accounting",
        "today": fmt_date(datetime.date.today()),
    }


@app.route("/")
def dashboard():
    year = session.get("year", "B1")
    # Summary stats
    from models.dbf_layer import count_records
    stats = {
        "accounts": count_records("ACMST", year),
        "gl_entries": count_records("GL", year),
        "sales_bills": count_records("SREG41", year),
        "purchase_bills": count_records("PREG61", year),
        "items": count_records("ITMST", year),
        "cashbook": count_records("CBK01", year),
    }

    # Recent GL entries (last 10)
    gl_recent = read_table("GL", year)
    gl_recent.sort(key=lambda r: r.get("DATE") or "", reverse=True)
    gl_recent = gl_recent[:10]
    accounts = {str(r.get("AC_CODE", "")).strip(): str(r.get("AC_HEAD", "")).strip()
                for r in read_table("ACMST", year)}
    for r in gl_recent:
        r["_ac_name"] = accounts.get(str(r.get("ACCD", "")).strip(), "")
        r["_date_fmt"] = fmt_date(r.get("DATE"))
        r["_amt_fmt"] = fmt_amount(float(r.get("AMNT", 0) or 0))

    # Recent sales (last 5)
    sales_recent = read_table("SREG41", year)
    sales_recent.sort(key=lambda r: r.get("RCTDTOTK") or "", reverse=True)
    sales_recent = sales_recent[:5]
    for r in sales_recent:
        r["_ac_name"] = accounts.get(str(r.get("ACCDOTK", "")).strip(), "")
        r["_date_fmt"] = fmt_date(r.get("RCTDTOTK"))
        r["_totamt_fmt"] = fmt_amount(r.get("TOTAMTTK", 0))

    available_years = get_available_years()
    branches = get_branch_list()

    return render_template("dashboard.html", stats=stats,
                           gl_recent=gl_recent, sales_recent=sales_recent,
                           available_years=available_years,
                           branches=branches,
                           data_dir=DATA_DIR, year=year)


@app.route("/set-year", methods=["POST"])
def set_year():
    year = request.form.get("year", "current")
    session["year"] = year
    flash(f"Switched to year: {year}", "info")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/data-info")
def data_info():
    from models.dbf_layer import count_records
    year = session.get("year", "B1")
    tables = [
        "ACMST", "GRPMST", "ACDOC", "GL", "SL", "CBK01", "CBK02",
        "BBK21", "BBK22", "BBK23", "BBK24", "BBK25", "BBK26", "BBK27", "BBK28", "BBK29", "BBK30",
        "JBK81", "SREG41", "SRPRFL", "PREG61", "ITMST", "ITGMST",
        "AGMST", "ADDRES", "ALLOC", "ALOCFL", "TAXMST", "LETTER",
        "CHQRCT", "CHQISU", "BRMST",
    ]
    info = []
    for t in tables:
        cnt = count_records(t, year)
        info.append({"table": t, "count": cnt, "has_data": cnt > 0})
    return render_template("data_info.html", info=info, year=year, data_dir=DATA_DIR)


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("  GEORGIN Accounting System - Mac Edition")
    print(f"  Data directory: {DATA_DIR}")
    print(f"  Open your browser at: http://localhost:5050")
    print(f"{'='*60}\n")
    app.run(host="127.0.0.1", port=5050, debug=False)
