"""
DBF Data Layer - Read/Write all dBase tables from the GEORGIN data directory.
Supports multi-year and multi-branch data with prefix-based table resolution.
"""
import os
import struct
import datetime
import re
from dbfread import DBF, FieldParser

_env_data_dir = os.environ.get("GEORGIN_DATA", "").strip()
DATA_DIR = os.path.abspath(_env_data_dir) if _env_data_dir else os.path.expanduser("~")

# Year prefix map: year code -> file prefix  (empty = current year)
YEAR_PREFIXES = {
    "current": "",
    "A1": "A1", "A2": "A2", "A3": "A3", "A4": "A4",
    "A5": "A5", "A6": "A6", "A7": "A7", "A8": "A8", "A9": "A9",
    "AY": "AY",
    "B1": "B1", "B2": "B2", "B3": "B3",
}

_YEAR_PREFIX_PATTERN = re.compile(r"^(A[1-9Y]|B[1-3])(.*)$", re.IGNORECASE)

class MyFieldParser(FieldParser):
    def parseC(self, field, data):
        try:
            return data.decode("cp1252", errors="replace").rstrip()
        except Exception:
            return data.decode("latin-1", errors="replace").rstrip()

    def parseD(self, field, data):
        try:
            s = data.decode("ascii", errors="ignore").strip()
            if s and len(s) == 8 and s != "00000000":
                return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except Exception:
            pass
        return None

    def parseN(self, field, data):
        try:
            s = data.decode("ascii", errors="ignore").strip()
            if s:
                return float(s) if "." in s else int(s)
        except Exception:
            pass
        return 0

    def parseL(self, field, data):
        return data in (b"T", b"t", b"Y", b"y")

    def parseM(self, field, data):
        return ""


def set_data_dir(path):
    """Update the active data directory for all DBF operations."""
    global DATA_DIR
    if not path:
        return False
    DATA_DIR = os.path.abspath(path)
    os.environ["GEORGIN_DATA"] = DATA_DIR
    return True


def _has_georgin_dbfs(path):
    """Return True when a folder looks like a GEORGIN DBF data directory."""
    if not path or not os.path.isdir(path):
        return False
    try:
        files = {name.upper() for name in os.listdir(path) if name.upper().endswith(".DBF")}
    except Exception:
        return False
    has_branch = any(name.endswith("BRMST.DBF") for name in files)
    has_master = any(name.endswith("ACMST.DBF") for name in files)
    return has_branch and has_master


def find_data_dir(start_path):
    """
    Find the actual GEORGIN DBF folder from a selected folder.
    Accepts either the data folder itself or a parent folder containing it.
    """
    if not start_path:
        return None
    start_path = os.path.abspath(start_path)
    if _has_georgin_dbfs(start_path):
        return start_path

    try:
        for root, dirs, _ in os.walk(start_path):
            if _has_georgin_dbfs(root):
                return root
            dirs[:] = [d for d in dirs if not d.startswith(".")]
    except Exception:
        return None
    return None


def list_table_bases(year=None):
    """
    Return sorted DBF table base names available in DATA_DIR.
    If year is provided, include files for that year prefix plus global files.
    """
    try:
        files = [name for name in os.listdir(DATA_DIR) if name.upper().endswith(".DBF")]
    except Exception:
        return []

    selected_prefix = YEAR_PREFIXES.get(year, "") if year else None
    bases = set()
    for name in files:
        stem = os.path.splitext(name)[0].upper()
        match = _YEAR_PREFIX_PATTERN.match(stem)
        if match:
            prefix, base = match.groups()
            if selected_prefix is None or prefix.upper() == selected_prefix.upper():
                bases.add(base.upper())
        elif selected_prefix in (None, ""):
            bases.add(stem.upper())
        elif selected_prefix:
            bases.add(stem.upper())
    return sorted(bases)


def dbf_path(table_name, year="current"):
    """Resolve the full path for a DBF file given table name and year prefix."""
    prefix = YEAR_PREFIXES.get(year, "")
    filename = (prefix + table_name + ".DBF").upper()
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        return path
    # Try lowercase
    path_lower = os.path.join(DATA_DIR, filename.lower())
    if os.path.exists(path_lower):
        return path_lower
    return path


def read_table(table_name, year="current", filters=None, order_by=None, limit=None):
    """
    Read all records from a DBF table.
    filters: dict of {field: value} for simple equality filtering
    order_by: field name string to sort by
    Returns list of dicts.
    """
    path = dbf_path(table_name, year)
    if not os.path.exists(path):
        return []
    try:
        table = DBF(path, parserclass=MyFieldParser, ignore_missing_memofile=True, encoding="cp1252")
        records = []
        raw_index = 0
        for rec in table:
            row = dict(rec)
            raw_index += 1
            if filters:
                match = all(str(row.get(k, "")).strip() == str(v).strip() for k, v in filters.items())
                if not match:
                    continue
            row["_recno"] = raw_index
            records.append(row)
        if order_by and records:
            records.sort(key=lambda r: str(r.get(order_by, "") or "").strip())
        if limit:
            records = records[:limit]
        return records
    except Exception as e:
        return []


def get_table_fields(table_name, year="current"):
    """Return list of (name, type, length, decimal) for a table."""
    path = dbf_path(table_name, year)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "rb") as f:
            f.read(32)
            fields = []
            while True:
                fd = f.read(32)
                if not fd or fd[0] == 0x0D:
                    break
                name = fd[:11].replace(b"\x00", b"").decode("ascii", errors="ignore").strip()
                ftype = chr(fd[11])
                flen = fd[16]
                fdec = fd[17]
                if name:
                    fields.append({"name": name, "type": ftype, "length": flen, "decimal": fdec})
        return fields
    except Exception:
        return []


def count_records(table_name, year="current"):
    """Fast count of records in a DBF file from header."""
    path = dbf_path(table_name, year)
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "rb") as f:
            header = f.read(8)
            return struct.unpack("<I", header[4:8])[0]
    except Exception:
        return 0


def write_record(table_name, year="current", record=None):
    """Append a new record to a DBF file using raw struct writes."""
    if record is None:
        return False
    import dbf as dbflib
    path = dbf_path(table_name, year)
    if not os.path.exists(path):
        return False
    try:
        t = dbflib.Table(path, codepage="cp1252")
        t.open(mode=dbflib.READ_WRITE)
        t.append(record)
        t.close()
        return True
    except Exception as e:
        return False


def update_record(table_name, year="current", recno=None, updates=None):
    """Update a record in a DBF file by record number (1-based)."""
    if recno is None or updates is None:
        return False
    import dbf as dbflib
    path = dbf_path(table_name, year)
    if not os.path.exists(path):
        return False
    try:
        t = dbflib.Table(path, codepage="cp1252")
        t.open(mode=dbflib.READ_WRITE)
        rec = t[recno - 1]
        dbflib.write(rec, **updates)
        t.close()
        return True
    except Exception as e:
        return False


def delete_record(table_name, year="current", recno=None):
    """Soft-delete a record in a DBF file."""
    if recno is None:
        return False
    import dbf as dbflib
    path = dbf_path(table_name, year)
    if not os.path.exists(path):
        return False
    try:
        t = dbflib.Table(path, codepage="cp1252")
        t.open(mode=dbflib.READ_WRITE)
        dbflib.delete(t[recno - 1])
        t.close()
        return True
    except Exception as e:
        return False


DEFAULT_YEAR = "B1"  # Most recently updated year prefix

def get_available_years():
    """Return list of year codes that have data files present."""
    available = []
    for code, prefix in YEAR_PREFIXES.items():
        if not prefix:
            continue  # skip empty prefix — no unprefixed files exist
        test_path = os.path.join(DATA_DIR, (prefix + "ACMST.DBF").upper())
        if os.path.exists(test_path):
            available.append(code)
    return available


def get_branch_list():
    """Read BRMST table for company/branch information."""
    records = read_table("BRMST")
    if not records:
        # Try NEWCO which has same structure
        records = read_table("NEWCO")
    return records


def fmt_amount(val):
    """Format a numeric value as Indian currency string."""
    try:
        v = float(val or 0)
        if v < 0:
            return "({:,.2f})".format(abs(v))
        return "{:,.2f}".format(v)
    except Exception:
        return "0.00"


def fmt_date(d):
    """Format a date value as DD-MM-YYYY string."""
    if not d:
        return ""
    if isinstance(d, datetime.date):
        return d.strftime("%d-%m-%Y")
    return str(d)


def parse_date(s):
    """Parse DD-MM-YYYY or YYYY-MM-DD string to date."""
    if not s:
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.datetime.strptime(s.strip(), fmt).date()
        except Exception:
            pass
    return None
