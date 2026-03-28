#!/usr/bin/env python3
"""GEORGIN Accounting System — Complete Mac Desktop Application (PyQt6)"""
import sys, os, csv, datetime, shutil, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QDateEdit, QDoubleSpinBox,
    QMenuBar, QMenu, QStatusBar, QToolBar, QFrame, QSplitter,
    QStackedWidget, QGroupBox, QScrollArea, QTextEdit, QSizePolicy,
    QMessageBox, QFileDialog, QInputDialog, QCheckBox, QListWidget,
    QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QDate, QSize, QSortFilterProxyModel, QRectF, QMarginsF
from PyQt6.QtGui import (
    QFont, QColor, QAction, QKeySequence, QTextDocument, QTextCursor,
    QPainter, QPen, QBrush, QPdfWriter, QPageSize, QPixmap
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

import models.dbf_layer as dbf_layer
from models.dbf_layer import (
    read_table, write_record, update_record, delete_record,
    count_records, fmt_amount, fmt_date, parse_date, get_available_years,
    set_data_dir, find_data_dir, get_table_fields, list_table_bases
)


def _read_app_version():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    version_path = os.path.join(base_dir, "VERSION")
    try:
        with open(version_path, "r", encoding="utf-8") as fh:
            version = fh.read().strip()
            return version or "0.1.0"
    except Exception:
        return "0.1.0"


APP_VERSION = _read_app_version()

# ─────────────────────────────────────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────────────────────────────────────
APP_STYLE = """
QMainWindow, QWidget {
    background:#000000;
    color:#f2f2f2;
    font-size:13px;
    font-family:'Menlo','Courier New',monospace;
}
QDialog { background:#000000; color:#f2f2f2; }
QMenuBar { background:#000000; color:#d8d8d8; padding:2px; }
QMenuBar::item { padding:4px 10px; }
QMenuBar::item:selected, QMenuBar::item:pressed { background:#800000; color:#ffffff; }
QMenu { background:#000000; color:#efefef; border:2px solid #c9c9c9; }
QMenu::item { padding:5px 28px 5px 12px; }
QMenu::item:selected { background:#0f8f96; color:#ffffff; }
QMenu::separator { height:1px; background:#787878; margin:4px 0; }
QTableWidget {
    background:#000000;
    alternate-background-color:#000000;
    color:#ffffff;
    gridline-color:#d0d0d0;
    selection-background-color:#0f8f96;
    selection-color:#ffffff;
    border:2px solid #d0d0d0;
    outline:none;
}
QTableWidget::item { padding:5px 8px; }
QHeaderView::section {
    background:#000000;
    color:#ffffff;
    font-weight:normal;
    padding:7px 10px;
    border:none;
    border-right:2px solid #d0d0d0;
    border-bottom:2px solid #d0d0d0;
}
QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox, QTextEdit {
    background:#d4d4d4;
    color:#000000;
    border:2px solid #d0d0d0;
    padding:4px 6px;
    border-radius:0;
    selection-background-color:#0f8f96;
}
QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus { border:2px solid #0f8f96; }
QLineEdit:read-only { background:#a0a0a0; color:#333; }
QLabel { color:#f2f2f2; }
QLabel.title { color:#ffffff; font-size:15px; font-weight:bold; }
QLabel.section { color:#ffffff; font-weight:bold; }
QPushButton {
    background:#000000;
    color:#f0f0f0;
    border:2px solid #d0d0d0;
    padding:4px 12px;
    border-radius:0;
    font-size:13px;
    min-width:70px;
}
QPushButton:hover { background:#181818; color:#ffffff; }
QPushButton:pressed { background:#0f8f96; }
QPushButton.primary { background:#000000; color:#ffffff; border:2px solid #d0d0d0; }
QPushButton.primary:hover { background:#181818; }
QPushButton.danger { background:#000000; color:#ffb0b0; border:2px solid #d0d0d0; }
QPushButton.danger:hover { background:#330000; color:#ffffff; }
QStatusBar { background:#000000; color:#ffffff; padding:2px 8px; font-size:12px; border-top:2px solid #d0d0d0; }
QGroupBox {
    border:2px solid #d0d0d0;
    border-radius:0;
    margin-top:14px;
    padding-top:14px;
    color:#f2f2f2;
}
QGroupBox::title {
    color:#000000;
    background:#d0d0d0;
    subcontrol-origin:margin;
    subcontrol-position:top center;
    padding:1px 12px;
}
QScrollBar:vertical { background:#000000; width:10px; }
QScrollBar::handle:vertical { background:#666666; border-radius:0; min-height:20px; }
QFrame.separator { color:#d0d0d0; }
QComboBox QAbstractItemView { background:#000000; color:#ffffff; selection-background-color:#0f8f96; }
QToolBar { background:#000000; border-bottom:2px solid #d0d0d0; spacing:4px; padding:3px; }
QToolBar QLabel { color:#aaaaaa; font-size:11px; padding:0 4px; }
QListWidget {
    background:#000000;
    color:#ffffff;
    border:2px solid #d0d0d0;
    outline:none;
}
QListWidget::item {
    padding:4px 10px;
}
QListWidget::item:selected {
    background:#800000;
    color:#ffffff;
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_company_info(year):
    for r in read_table("BRMST"):
        if str(r.get("BRCOD","")).strip() == year:
            name = str(r.get("BRNAME","")).strip()
            opdt, cldt = r.get("YEROPDT"), r.get("YERCLDT")
            return f"{name}  {opdt.year}-{cldt.year}" if opdt and cldt else name
    return year

def get_books(year):
    return [(str(r.get("DOCD","")).strip(), str(r.get("DESC","")).strip(),
             str(r.get("SHFM","")).strip(), str(r.get("ACCD","")).strip())
            for r in read_table("ACDOC", year) if r.get("DESC","").strip()]

def get_cash_books(year):
    skip = {"41","61","81"}
    return [(d,n,s,a) for d,n,s,a in get_books(year) if d not in skip]


def get_cash_book_choices(year):
    books = []
    for docd, desc, shfm, accd in get_cash_books(year):
        desc_u = desc.upper().strip()
        if "CASH" in desc_u or accd.startswith("10") or (str(docd).isdigit() and int(docd) <= 9):
            books.append((docd, desc, shfm, accd))
    seen = set()
    unique = []
    for book in books:
        key = (book[0], book[1].strip().upper(), get_cbk_file(book[0]).upper())
        if key not in seen:
            seen.add(key)
            unique.append(book)
    unique.sort(key=lambda item: (0 if item[1].strip().upper() == "CASH BOOK" else 1, item[1].strip().upper()))
    return unique


def get_bank_book_choices(year):
    books = []
    for docd, desc, shfm, accd in get_cash_books(year):
        desc_u = desc.upper().strip()
        is_cash = "CASH" in desc_u or accd.startswith("10") or (str(docd).isdigit() and int(docd) <= 9)
        if not is_cash:
            books.append((docd, desc, shfm, accd))
    seen = set()
    unique = []
    for book in books:
        key = (book[0], book[1].strip().upper(), get_cbk_file(book[0]).upper())
        if key not in seen:
            seen.add(key)
            unique.append(book)
    unique.sort(key=lambda item: item[1].strip().upper())
    return unique

def get_cbk_file(docd):
    try:
        num = int(docd)
        if 1 <= num <= 9:  return f"CBK{num:02d}"
        if 10 <= num <= 39: return f"BBK{num}"
    except: pass
    return f"CBK{str(docd).zfill(2)}"

def get_accounts_dict(year):
    return {str(r.get("AC_CODE","")).strip(): str(r.get("AC_HEAD","")).strip()
            for r in read_table("ACMST", year)}

def cash_balance(year, docd):
    tbl = get_cbk_file(docd)
    rows = read_table(tbl, year)
    accd_main = ""
    for d in read_table("ACDOC", year):
        if str(d.get("DOCD","")).strip() == docd:
            accd_main = str(d.get("ACCD","")).strip(); break
    opening = 0.0
    for a in read_table("ACMST", year):
        if str(a.get("AC_CODE","")).strip() == accd_main:
            opening = float(a.get("YEAROP", 0) or 0); break
    receipts = sum(float(r.get("AMNT",0) or 0) for r in rows
                   if str(r.get("DRCR","D")).strip().upper() in ("D",""))
    payments = sum(float(r.get("AMNT",0) or 0) for r in rows
                   if str(r.get("DRCR","")).strip().upper() == "C")
    return opening + receipts - payments

def next_vrno(year, docd):
    for d in read_table("ACDOC", year):
        if str(d.get("DOCD","")).strip() == docd:
            last = str(d.get("LASTNO","") or d.get("RLASTNO","") or "").strip()
            if last and len(last)>1 and last[1:].isdigit():
                return f"{last[0]}{int(last[1:])+1:05d}"
            elif last.isdigit():
                return str(int(last)+1).zfill(6)
    rows = read_table(get_cbk_file(docd), year)
    return str(len(rows)+1).zfill(6)


def next_numeric_code(records, *keys, width=6):
    max_value = 0
    for record in records:
        value = str(rec_value(record, *keys, default="")).strip()
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            max_value = max(max_value, int(digits))
    return f"{max_value + 1:0{width}d}"


def rec_value(record, *keys, default=""):
    """Return the first present, non-empty value from a record."""
    for key in keys:
        if key in record:
            value = record.get(key)
            if value not in (None, ""):
                return value
    return default


def configure_entry_dialog(dialog, min_width=900, min_height=700):
    """Make data-entry dialogs open as page-sized maximized windows."""
    dialog.setMinimumSize(min_width, min_height)
    dialog.resize(max(min_width, 1200), max(min_height, 820))
    dialog.setWindowState(dialog.windowState() | Qt.WindowState.WindowMaximized)


APP_FOOTER_TEXT = "GEORGIN Accounting Package. Developers INFO_NET-Aluva   F1-Help Alt_C-Clc Esc-Exit"


def _menu_preview_model(section, item_label):
    section = (section or "").upper()
    item_label = (item_label or "").upper()
    if section == "ENTRIES" and item_label == "CASH BOOK":
        return [
            ("Select Book", [
                "CASH BOOK",
                "CASH (CREDIT SALES)",
                "GEORGIN GLASS WORK",
                "FEDERAL BANK KALADY G",
                "BELORA FEDERAL BANK LOAN A/C",
            ], 0)
        ]
    if section == "ENTRIES" and item_label == "BANK BOOK":
        return [
            ("Select Book", [
                "EKM DIST.CO BANK 006241000008839 KLD",
                "FEDERAL BANK BOLERO CAR LOAN",
                "FEDERAL BANK KALADY",
                "BANK OF INDIA KALADY",
                "SBT,KALADY GEN",
                "BANK OF INDIA PBR",
            ], 0)
        ]
    if section == "REPORTS" and item_label in {"ACCOUNT LEDGER", "LEDGER"}:
        return [
            ("Option(s)", ["GENERAL", "CUSTOMERS", "SUPPLIERS"], 0),
            ("Parameter(s)", [
                "Code From :        ",
                "To        :        ",
                "Date From :  /  /  ",
                "To        :  /  /  ",
                "Page No.  : 1      ",
                "Compact (Y/N): Y   ",
            ], -1),
        ]
    if section == "REPORTS" and item_label == "TRIAL BALANCE":
        return [
            ("Options", ["General", "Customer", "Supplier", "Combined"], 3),
            ("Parameters", [
                "From : 01/04/25",
                "To   : 28/03/26",
                "Zero Balance: N",
            ], -1),
        ]
    if section == "FILES":
        return [
            ("Master", [
                "A/c   Master",
                "Group Master",
                "Agent Master",
                "Item  Master",
                "I.Grp Master",
                "Tax   Master",
            ], 0)
        ]
    return []


WORKFLOW_REFERENCE_SCREENS = [
    {
        "title": "MAIN MENU",
        "menu": ["Cash Book", "Bank Book", "Purchase", "Sales", "Journals", "Stock Receipt", "Stock Issue", "Glass Stock"],
        "selected": 0,
        "boxes": [],
        "footer": APP_FOOTER_TEXT,
    },
    {
        "title": "CASH BOOK",
        "menu": ["Cash Book", "Bank Book", "Purchase", "Sales", "Journals", "Stock Receipt", "Stock Issue", "Glass Stock"],
        "selected": 0,
        "boxes": [("Select Book", [
            "CASH BOOK",
            "CASH (CREDIT SALES)",
            "GEORGIN GLASS WORK",
            "FEDERAL BANK KALADY G",
            "BELORA FEDERAL BANK LOAN A/C",
        ], 0)],
        "footer": APP_FOOTER_TEXT,
    },
    {
        "title": "CASH BOOK",
        "table_headers": ["Date", "Vr.No.", "A/c CD", "A/c Name", "Receipt", "Payment"],
        "table_rows": [
            ["25/03/26", "00207", "5AN001", "AQURIUM  ANIL 9809271003", "500.00", ""],
            ["25/03/26", "01313", "1BSBT1", "S.B.T  67010468481 GENTLY8205", "", "6.00"],
            ["25/03/26", "01314", "44MEER", "MEERA  -9495587107", "", "550.00"],
            ["26/03/26", "01360", "300001", "SALES", "20.00", ""],
            ["27/03/26", "01369", "300001", "SALES", "200.00", ""],
        ],
        "footer": "F10-Add F2-Edit F3-List F4-Del 1-Go Date F5-Receipt F6-Qck_Del",
    },
    {
        "title": "EDITING",
        "table_headers": ["Date", "A/c.Code", "Narration", "Rct. Amt.", "Pyt. Amt."],
        "table_rows": [["25/03/26", "5AN001", "ANIL", "500.00", "0.00"]],
        "footer": APP_FOOTER_TEXT,
    },
    {
        "title": "PURCHASE",
        "table_headers": ["Serial", "Rct.Date", "Bill No", "B.Date", "Party Name", "Amount"],
        "table_rows": [
            ["000123", "30/01/26", "", "30/01/26", "6XATOZ A TO Z 9037778893/4", "60.00"],
            ["000124", "06/02/26", "", "06/02/26", "GLASS HOUSE-KALADY 2462928", "80735.00"],
            ["000125", "07/02/26", "", "07/02/26", "AMBOOKEN AGENCIS 8138051116", "999.00"],
        ],
        "footer": "F10-Add F2-Edit F3-List F4-Del 1-Search Bill F5-Print F6-VAT_Reg.",
    },
    {
        "title": "SALES",
        "table_headers": ["Bill", "Date", "Party", "Sls. Amt", "Add", "Less", "Nett Amt", "Type"],
        "table_rows": [
            ["001362", "26/03/26", "5XMATH", "7424.00", "0.00", "0.00", "7424.00", "Credit"],
            ["001363", "26/03/26", "5XJOHN", "3840.00", "0.00", "0.00", "3840.00", "Credit"],
            ["001369", "27/03/26", "100001", "200.00", "0.00", "0.00", "200.00", "Cash"],
        ],
        "footer": "F10-Add F2-Edit F3-List F4-Del 1-No. 2-Dt F5-Copy F6-Reg. F7-Qck_Del F8-updt",
    },
    {
        "title": "JOURNAL",
        "table_headers": ["Vr. No", "Sr#", "Date", "A/c Head", "Debit", "Credit"],
        "table_rows": [
            ["000001", "1", "10/04/25", "G.G ELE CHITTIKULANGARA", "", "891.00"],
            ["000001", "2", "10/04/25", "BAD DEBTS", "891.00", ""],
            ["000002", "1", "24/04/25", "JOHNSON AGE-PALKULANGARA", "", "28.00"],
        ],
        "footer": "F10-Add F2-Edit F3-List F4-Del 1-Bill 2-Date F5-Print",
    },
    {
        "title": "STOCK RECEIPT",
        "table_headers": ["Vr.No", "Date", "Description", "Amount"],
        "table_rows": [
            ["000002", "28/04/25", "lock return", "650.00"],
            ["000003", "09/05/25", "mkt", "55148.25"],
            ["000004", "29/05/25", "stock mirror", "34011.00"],
        ],
        "footer": "F10-Add F2-Edit F3-List F4-Del 1-Date",
    },
    {
        "title": "ACCOUNT MASTER",
        "table_headers": ["Code", "Account Head", "Grp", "Op. Balance", "Cur. Bal"],
        "table_rows": [
            ["6XLAND", "LANDMARK 8594001359 NEDU-PAPER", "6000", "0.00", "0.00"],
            ["6XMAGL", "MA GLASS HW ASHIEF-9847751932", "6001", "0.00", "2,740.00 CR"],
            ["6XMEPO", "M.E. POLYMERS-7907216811", "6001", "0.00", "0.00"],
        ],
        "footer": "F10-Add F2-Edit F3-List F4-Del 1-Name 2-Code",
    },
    {
        "title": "ITEM MASTER",
        "table_headers": ["Code", "Description", "Unit", "Op.Stock", "C.Price", "D.Price"],
        "table_rows": [
            ["-POLIS", "GLASS POLISH POWDER", "NOS", "1.00", "0.00", "0.00"],
            ["-XFLAP", "FLAP WHEEL", "NOS", "10.00", "0.00", "0.00"],
            ["11BE00", "11BE00 BELL 32MM BR 1-1/4", "NOS", "34.00", "120.00", "0.00"],
        ],
        "footer": "F10-Add F2-Edit F3-List F4-Del 1-Description 2-Code",
    },
    {
        "title": "PERFECT REPORT VIEWER",
        "table_headers": ["DATE", "PARTICULARS", "DEBIT", "CREDIT", "BALANCE"],
        "table_rows": [
            ["01/04/25", "Opening Balance b/f", "6185.00", "", "6185.00 DR"],
            ["01/04/25", "kma", "", "500.00", "5685.00 DR"],
            ["01/04/25", "james", "", "1000.00", "4685.00 DR"],
        ],
        "footer": "1/7718 Report Compiled    Alt_N/Alt_P-Print    Alt_E-Export    Esc-Exit",
    },
]


def _draw_legacy_header(painter, rect, company_text):
    painter.setPen(QPen(QColor("#d0d0d0"), 2))
    painter.drawRect(rect)
    now = datetime.datetime.now()
    painter.drawText(QRectF(rect.left() + 18, rect.top(), rect.width() * 0.33, rect.height()),
                     Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                     now.strftime("%B %d, %Y"))
    painter.drawText(QRectF(rect.left(), rect.top(), rect.width(), rect.height()),
                     Qt.AlignmentFlag.AlignCenter,
                     company_text)
    painter.drawText(QRectF(rect.right() - rect.width() * 0.24, rect.top(), rect.width() * 0.22, rect.height()),
                     Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                     now.strftime("%H:%M:%S"))


def _draw_legacy_title_tab(painter, top_y, width, title):
    painter.setPen(QPen(QColor("#d0d0d0"), 2))
    line_y = top_y + 18
    painter.drawLine(10, line_y, int(width - 10), line_y)
    tab_width = min(320, max(140, len(title) * 14))
    tab_rect = QRectF((width - tab_width) / 2, top_y, tab_width, 34)
    painter.fillRect(tab_rect, QColor("#d0d0d0"))
    painter.setPen(QColor("#000000"))
    painter.drawText(tab_rect, Qt.AlignmentFlag.AlignCenter, title)
    painter.setPen(QPen(QColor("#d0d0d0"), 2))


def _draw_legacy_box(painter, rect, title, lines, selected_index=None):
    painter.setPen(QPen(QColor("#d0d0d0"), 2))
    painter.drawRect(rect)
    if title:
        title_rect = QRectF(rect.left() + 16, rect.top() - 20, min(rect.width() - 32, max(120, len(title) * 13)), 32)
        painter.fillRect(title_rect, QColor("#0f8f96"))
        painter.setPen(QColor("#ffffff"))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, title)
        painter.setPen(QPen(QColor("#d0d0d0"), 2))
    line_height = 28
    y = rect.top() + 16
    for idx, line in enumerate(lines):
        row_rect = QRectF(rect.left() + 12, y, rect.width() - 24, line_height)
        if selected_index == idx:
            painter.fillRect(row_rect, QColor("#0f8f96" if title.lower().startswith("select") else "#800000"))
            painter.setPen(QColor("#ffffff"))
        else:
            painter.setPen(QColor("#f0f0f0"))
        painter.drawText(row_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, line)
        y += line_height + 6
    painter.setPen(QPen(QColor("#d0d0d0"), 2))


def export_workflow_pdf(parent, company_text, output_path=None):
    filename = output_path
    if not filename:
        filename, _ = QFileDialog.getSaveFileName(
            parent,
            "Save Workflow PDF",
            "georgin_legacy_workflow.pdf",
            "PDF (*.pdf)",
        )
    if not filename:
        return None
    writer = QPrinter(QPrinter.PrinterMode.HighResolution)
    writer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    writer.setOutputFileName(filename)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    painter = QPainter(writer)
    try:
        page_rect = writer.pageRect(QPrinter.Unit.DevicePixel)
        width = page_rect.width()
        height = page_rect.height()
        font = QFont("Courier New", 14)
        painter.setFont(font)
        for index, screen in enumerate(WORKFLOW_REFERENCE_SCREENS):
            painter.fillRect(QRectF(0, 0, width, height), QColor("#000000"))
            painter.setPen(QColor("#ffffff"))
            _draw_legacy_header(painter, QRectF(14, 14, width - 28, 80), company_text)
            if screen.get("menu"):
                painter.setPen(QColor("#d0d0d0"))
                menu_y = 130
                painter.drawLine(12, menu_y + 14, int(width - 12), menu_y + 14)
                sections = ["Entries", "Reports", "Utilities", "Files", "Help", "Quit"]
                x = 36
                for label in sections:
                    painter.drawText(QRectF(x, menu_y, 180, 28), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
                    x += 190
            _draw_legacy_title_tab(painter, 156, width, screen["title"])
            if screen.get("menu"):
                _draw_legacy_box(
                    painter,
                    QRectF(54, 222, 250, 330),
                    "",
                    screen["menu"],
                    screen.get("selected", 0),
                )
                x = 380
                for title, lines, selected in screen.get("boxes", []):
                    box_height = 56 + len(lines) * 34
                    _draw_legacy_box(painter, QRectF(x, 266, width - x - 72, box_height), title, lines, selected)
                    x += 40
            else:
                table_rect = QRectF(12, 196, width - 24, height - 330)
                painter.setPen(QPen(QColor("#d0d0d0"), 2))
                painter.drawRect(table_rect)
                headers = screen.get("table_headers", [])
                rows = screen.get("table_rows", [])
                if headers:
                    col_width = table_rect.width() / len(headers)
                    y = table_rect.top() + 14
                    painter.setPen(QColor("#ffffff"))
                    for idx, header in enumerate(headers):
                        head_rect = QRectF(table_rect.left() + idx * col_width, y, col_width, 28)
                        painter.drawText(head_rect.adjusted(8, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, header)
                    painter.setPen(QPen(QColor("#d0d0d0"), 2))
                    painter.drawLine(int(table_rect.left()), int(y + 40), int(table_rect.right()), int(y + 40))
                    row_y = y + 52
                    for row in rows:
                        for idx, value in enumerate(row):
                            cell_rect = QRectF(table_rect.left() + idx * col_width, row_y, col_width, 28)
                            align = Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignRight if idx == len(row) - 1 else Qt.AlignmentFlag.AlignLeft)
                            painter.setPen(QColor("#ffffff"))
                            painter.drawText(cell_rect.adjusted(8, 0, -8, 0), align, value)
                        row_y += 34
            footer_rect = QRectF(12, height - 96, width - 24, 72)
            painter.setPen(QPen(QColor("#d0d0d0"), 2))
            painter.drawRect(footer_rect)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(footer_rect.adjusted(18, 0, -18, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, screen["footer"])
            if index < len(WORKFLOW_REFERENCE_SCREENS) - 1:
                writer.newPage()
    finally:
        painter.end()
    if parent is not None and output_path is None:
        QMessageBox.information(parent, "Saved", f"Workflow PDF saved:\n{filename}")
    return filename


class LegacyFooter(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setFixedHeight(86)
        self.setStyleSheet("background:#000000;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.box = QLabel(text)
        self.box.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.box.setStyleSheet(
            "border:2px solid #d0d0d0; padding:10px 18px; color:#ffffff; font-size:17px; background:#000000;"
        )
        layout.addWidget(self.box)

    def set_text(self, text):
        self.box.setText(text)


class LegacyPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.section = "Entries"
        self.item_label = "Cash Book"
        self.setMinimumWidth(520)

    def set_preview(self, section, item_label):
        self.section = section
        self.item_label = item_label
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#000000"))
        painter.setFont(QFont("Courier New", 13))
        painter.setPen(QPen(QColor("#d0d0d0"), 2))
        title = (self.item_label or self.section or "").upper()
        _draw_legacy_title_tab(painter, 16, self.width(), title)
        model = _menu_preview_model(self.section, self.item_label)
        if not model:
            painter.setPen(QColor("#7f7f7f"))
            painter.drawText(QRectF(24, 86, self.width() - 48, 40), Qt.AlignmentFlag.AlignLeft, "Workflow preview")
            painter.end()
            return
        x = 40
        y = 112
        for box_index, (box_title, lines, selected_index) in enumerate(model):
            box_width = min(360, self.width() - x - 36)
            box_height = max(120, 44 + len(lines) * 34)
            if box_index > 0:
                y += 42
                x += 80
            _draw_legacy_box(painter, QRectF(x, y, box_width, box_height), box_title, lines, selected_index)
        painter.end()


class SortableItem(QTableWidgetItem):
    def __init__(self, text, sort_key=None):
        super().__init__(str(text))
        self.sort_key = str(text) if sort_key is None else sort_key

    def __lt__(self, other):
        if isinstance(other, SortableItem):
            return self.sort_key < other.sort_key
        return super().__lt__(other)

# ─────────────────────────────────────────────────────────────────────────────
# PRINT / EXPORT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _make_html(title, company, headers, rows, totals_row=None):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = ""
    for i, row in enumerate(rows):
        cls = "alt" if i % 2 else ""
        trs += f"<tr class='{cls}'>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
    tot = ""
    if totals_row:
        tot = "<tr class='total'>" + "".join(f"<td><b>{c}</b></td>" for c in totals_row) + "</tr>"
    return f"""<html><head><style>
    body{{font-family:Arial,sans-serif;font-size:11px;margin:20px}}
    h2{{color:#003366;margin:0 0 4px 0}} p.co{{color:#555;font-size:10px;margin:0 0 12px 0}}
    table{{border-collapse:collapse;width:100%}}
    th{{background:#003366;color:#fff;padding:5px 8px;text-align:left;font-size:11px}}
    td{{padding:4px 8px;border-bottom:1px solid #ddd;font-size:11px}}
    tr.alt td{{background:#f5f8ff}} tr.total td{{background:#e0f0e0;border-top:2px solid #006060}}
    </style></head><body>
    <h2>{title}</h2><p class='co'>{company} &nbsp;|&nbsp; Printed: {datetime.date.today().strftime('%d/%m/%Y')}</p>
    <table><thead><tr>{th}</tr></thead><tbody>{trs}{tot}</tbody></table>
    </body></html>"""

def do_print(parent, html):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    dlg = QPrintDialog(printer, parent)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return
    doc = QTextDocument()
    doc.setHtml(html)
    doc.print_(printer)

def do_pdf(parent, hint, html):
    fn, _ = QFileDialog.getSaveFileName(parent, "Save as PDF", f"{hint}.pdf", "PDF (*.pdf)")
    if not fn: return
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(fn)
    doc = QTextDocument(); doc.setHtml(html); doc.print_(printer)
    QMessageBox.information(parent, "Saved", f"PDF saved:\n{fn}")

def do_csv(parent, hint, headers, rows):
    fn, _ = QFileDialog.getSaveFileName(parent, "Save as CSV", f"{hint}.csv", "CSV (*.csv)")
    if not fn: return
    with open(fn, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(headers); w.writerows(rows)
    QMessageBox.information(parent, "Saved", f"CSV saved:\n{fn}")

# ─────────────────────────────────────────────────────────────────────────────
# ACCOUNT LOOKUP DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class AccountLookupDialog(QDialog):
    def __init__(self, year, parent=None):
        super().__init__(parent)
        self.year = year; self.chosen = None
        self.setWindowTitle("Account Search"); self.setMinimumSize(700, 480)
        self.setStyleSheet(APP_STYLE)
        layout = QVBoxLayout(self)
        self.search = QLineEdit(placeholderText="Type account code or name to search…")
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Code","Account Name","City","Balance"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._select)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        btns = QHBoxLayout()
        b_sel = QPushButton("Select"); b_sel.setProperty("class","primary"); b_sel.clicked.connect(self._select)
        b_can = QPushButton("Cancel"); b_can.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(b_sel); btns.addWidget(b_can)
        layout.addLayout(btns)
        self._all = read_table("ACMST", year, order_by="AC_CODE")
        self._fill(self._all)
        self.search.setFocus()

    def _fill(self, recs):
        self.table.setRowCount(0)
        for r in recs[:200]:
            row = self.table.rowCount(); self.table.insertRow(row)
            bal = float(r.get("CURBAL",0) or 0)
            for col, val in enumerate([
                str(r.get("AC_CODE","")).strip(),
                str(r.get("AC_HEAD","")).strip(),
                str(r.get("CITY","")).strip(),
                fmt_amount(abs(bal)) + (" Dr" if bal>=0 else " Cr")
            ]):
                item = QTableWidgetItem(val)
                if col in (2,3): item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)

    def _filter(self, text):
        q = text.upper()
        if q:
            filtered = [r for r in self._all if q in str(r.get("AC_CODE","")).upper()
                        or q in str(r.get("AC_HEAD","")).upper()]
        else:
            filtered = self._all
        self._fill(filtered)

    def _select(self):
        row = self.table.currentRow()
        if row >= 0:
            self.chosen = self.table.item(row, 0).text()
            self.accept()

# ─────────────────────────────────────────────────────────────────────────────
# BOOK SELECT DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class BookSelectDialog(QDialog):
    def __init__(self, books, title="Select Book", parent=None):
        super().__init__(parent)
        self.books = books; self.chosen = None
        self.setWindowTitle(title); self.setMinimumWidth(420)
        self.setStyleSheet(APP_STYLE)
        layout = QVBoxLayout(self)
        lbl = QLabel(title); lbl.setProperty("class","section"); layout.addWidget(lbl)
        self.table = QTableWidget(len(books), 2)
        self.table.setHorizontalHeaderLabels(["Code","Book Name"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._select)
        for i, (docd, desc, shfm, accd) in enumerate(books):
            self.table.setItem(i, 0, QTableWidgetItem(docd))
            self.table.setItem(i, 1, QTableWidgetItem(desc))
        self.table.selectRow(0)
        layout.addWidget(self.table)
        btns = QHBoxLayout()
        b_ok = QPushButton("Open"); b_ok.setProperty("class","primary"); b_ok.clicked.connect(self._select)
        b_can = QPushButton("Cancel"); b_can.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(b_ok); btns.addWidget(b_can)
        layout.addLayout(btns)

    def _select(self):
        row = self.table.currentRow()
        if row >= 0: self.chosen = self.books[row]; self.accept()

# ─────────────────────────────────────────────────────────────────────────────
# CASH / BANK BOOK ENTRY DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class CashEntryDialog(QDialog):
    def __init__(self, year, docd, book_name, rec=None, parent=None):
        super().__init__(parent)
        self.year = year; self.docd = docd; self.book_name = book_name
        self.is_bank = any(str(docd).startswith(x) for x in ["2","3","1b","10"]) or (docd.isdigit() and int(docd)>=10)
        self.rec = rec  # None = new entry
        self.setWindowTitle(f"{'Edit' if rec else 'New'} Entry - {book_name}")
        self.setStyleSheet(APP_STYLE)
        configure_entry_dialog(self)
        self._accounts = get_accounts_dict(year)
        layout = QVBoxLayout(self); layout.setSpacing(10)
        form = QGridLayout(); form.setSpacing(8)

        # Date
        form.addWidget(QLabel("Date:"), 0, 0)
        self.f_date = QDateEdit(); self.f_date.setDisplayFormat("dd/MM/yy")
        self.f_date.setCalendarPopup(True)
        d = rec.get("DATE") if rec else None
        self.f_date.setDate(QDate(d.year,d.month,d.day) if d else QDate.currentDate())
        form.addWidget(self.f_date, 0, 1)

        # Voucher
        form.addWidget(QLabel("Voucher No:"), 0, 2)
        self.f_vrno = QLineEdit()
        self.f_vrno.setText(str(rec.get("VRNO","")).strip() if rec else next_vrno(year, docd))
        form.addWidget(self.f_vrno, 0, 3)

        # A/c Code
        form.addWidget(QLabel("A/c Code:"), 1, 0)
        ac_row = QHBoxLayout()
        self.f_accd = QLineEdit(); self.f_accd.setFixedWidth(100)
        self.f_accd.setText(str(rec.get("ACCD","")).strip() if rec else "")
        self.f_accd.textChanged.connect(self._lookup_name)
        ac_row.addWidget(self.f_accd)
        btn_lookup = QPushButton("Lookup"); btn_lookup.setFixedWidth(70)
        btn_lookup.clicked.connect(self._open_lookup)
        ac_row.addWidget(btn_lookup); ac_row.addStretch()
        form.addLayout(ac_row, 1, 1, 1, 1)

        # A/c Name (auto-fill)
        form.addWidget(QLabel("A/c Name:"), 1, 2)
        self.f_acname = QLineEdit(); self.f_acname.setReadOnly(True)
        accd_val = str(rec.get("ACCD","")).strip() if rec else ""
        self.f_acname.setText(self._accounts.get(accd_val,""))
        form.addWidget(self.f_acname, 1, 3)

        # Narration
        form.addWidget(QLabel("Narration:"), 2, 0)
        self.f_narr = QLineEdit(); self.f_narr.setMaxLength(90)
        self.f_narr.setText(str(rec.get("NARR","")).strip() if rec else "")
        form.addWidget(self.f_narr, 2, 1, 1, 3)

        # Cheque (bank only)
        if self.is_bank:
            form.addWidget(QLabel("Cheque No:"), 3, 0)
            self.f_chqno = QLineEdit()
            self.f_chqno.setText(str(rec.get("CHQNO","")).strip() if rec else "")
            form.addWidget(self.f_chqno, 3, 1)
        else:
            self.f_chqno = QLineEdit()  # hidden but present

        # Amounts
        row_amt = 3 if not self.is_bank else 4
        form.addWidget(QLabel("Receipt Amt (₹):"), row_amt, 0)
        self.f_rct = QDoubleSpinBox(); self.f_rct.setMaximum(9999999999); self.f_rct.setDecimals(2)
        self.f_rct.setGroupSeparatorShown(True)
        form.addWidget(self.f_rct, row_amt, 1)
        form.addWidget(QLabel("Payment Amt (₹):"), row_amt, 2)
        self.f_pyt = QDoubleSpinBox(); self.f_pyt.setMaximum(9999999999); self.f_pyt.setDecimals(2)
        self.f_pyt.setGroupSeparatorShown(True)
        form.addWidget(self.f_pyt, row_amt, 3)

        if rec:
            amt = float(rec.get("AMNT",0) or 0)
            drcr = str(rec.get("DRCR","D")).strip().upper()
            if drcr == "D": self.f_rct.setValue(amt)
            else: self.f_pyt.setValue(amt)

        layout.addLayout(form)

        # Hint
        hint = QLabel("F2=Account Lookup  |  Tab=Next Field  |  Enter=Save")
        hint.setStyleSheet("color:#666; font-size:11px;"); layout.addWidget(hint)

        # Buttons
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save (F9)"); btn_save.setProperty("class","primary")
        btn_save.clicked.connect(self.accept); btn_save.setShortcut("F9")
        btn_can = QPushButton("Cancel (Esc)"); btn_can.clicked.connect(self.reject)
        btn_row.addStretch(); btn_row.addWidget(btn_save); btn_row.addWidget(btn_can)
        layout.addLayout(btn_row)
        self.f_accd.setFocus()

    def _lookup_name(self, code):
        self.f_acname.setText(self._accounts.get(code.strip().upper(), ""))

    def _open_lookup(self):
        dlg = AccountLookupDialog(self.year, self)
        if dlg.exec() and dlg.chosen:
            self.f_accd.setText(dlg.chosen)

    def get_record(self):
        rct = self.f_rct.value(); pyt = self.f_pyt.value()
        amt = rct if rct > 0 else pyt
        drcr = "D" if rct > 0 else "C"
        qd = self.f_date.date()
        return {
            "DATE": datetime.date(qd.year(), qd.month(), qd.day()),
            "VRNO": self.f_vrno.text().strip()[:6],
            "ACCD": self.f_accd.text().strip().upper()[:6],
            "NARR": self.f_narr.text().strip()[:90],
            "CHQNO": self.f_chqno.text().strip()[:10],
            "AMNT": amt, "DRCR": drcr,
            "PYTRCT": "R" if drcr=="D" else "P",
            "DOCD": self.docd[:2], "SRNO": 1,
            "CONDOCD": "", "COUNTCD": "",
        }

    def validate(self):
        if not self.f_accd.text().strip():
            QMessageBox.warning(self, "Validation", "A/c Code is required."); return False
        if self.f_rct.value() == 0 and self.f_pyt.value() == 0:
            QMessageBox.warning(self, "Validation", "Enter Receipt or Payment amount."); return False
        if self.f_rct.value() > 0 and self.f_pyt.value() > 0:
            QMessageBox.warning(self, "Validation", "Enter EITHER Receipt OR Payment, not both."); return False
        return True

    def accept(self):
        if self.validate(): super().accept()


# ─────────────────────────────────────────────────────────────────────────────
# JOURNAL ENTRY DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class JournalEntryDialog(QDialog):
    def __init__(self, year, rec=None, parent=None):
        super().__init__(parent)
        self.year = year; self.rec = rec
        self.setWindowTitle("Journal Entry")
        self.setStyleSheet(APP_STYLE)
        configure_entry_dialog(self)
        self._accounts = get_accounts_dict(year)
        layout = QVBoxLayout(self); layout.setSpacing(10)
        form = QGridLayout(); form.setSpacing(8)

        form.addWidget(QLabel("Date:"), 0, 0)
        self.f_date = QDateEdit(); self.f_date.setDisplayFormat("dd/MM/yy")
        self.f_date.setCalendarPopup(True)
        d = rec.get("DATE") if rec else None
        self.f_date.setDate(QDate(d.year,d.month,d.day) if d else QDate.currentDate())
        form.addWidget(self.f_date, 0, 1)

        form.addWidget(QLabel("Voucher:"), 0, 2)
        self.f_vrno = QLineEdit()
        self.f_vrno.setText(str(rec.get("VRNO","")).strip() if rec else next_vrno(year, "81"))
        form.addWidget(self.f_vrno, 0, 3)

        form.addWidget(QLabel("Dr A/c:"), 1, 0)
        dr_row = QHBoxLayout()
        self.f_dr = QLineEdit(); self.f_dr.setFixedWidth(100)
        self.f_dr.textChanged.connect(lambda t: self.f_drname.setText(self._accounts.get(t.strip().upper(),"")))
        btn_dr = QPushButton("..."); btn_dr.setFixedWidth(40)
        btn_dr.clicked.connect(lambda: self._lookup(self.f_dr))
        dr_row.addWidget(self.f_dr); dr_row.addWidget(btn_dr); dr_row.addStretch()
        form.addLayout(dr_row, 1, 1)
        form.addWidget(QLabel("Name:"), 1, 2)
        self.f_drname = QLineEdit(); self.f_drname.setReadOnly(True)
        form.addWidget(self.f_drname, 1, 3)

        form.addWidget(QLabel("Cr A/c:"), 2, 0)
        cr_row = QHBoxLayout()
        self.f_cr = QLineEdit(); self.f_cr.setFixedWidth(100)
        self.f_cr.textChanged.connect(lambda t: self.f_crname.setText(self._accounts.get(t.strip().upper(),"")))
        btn_cr = QPushButton("..."); btn_cr.setFixedWidth(40)
        btn_cr.clicked.connect(lambda: self._lookup(self.f_cr))
        cr_row.addWidget(self.f_cr); cr_row.addWidget(btn_cr); cr_row.addStretch()
        form.addLayout(cr_row, 2, 1)
        form.addWidget(QLabel("Name:"), 2, 2)
        self.f_crname = QLineEdit(); self.f_crname.setReadOnly(True)
        form.addWidget(self.f_crname, 2, 3)

        form.addWidget(QLabel("Narration:"), 3, 0)
        self.f_narr = QLineEdit(); self.f_narr.setMaxLength(90)
        self.f_narr.setText(str(rec.get("NARR","")).strip() if rec else "")
        form.addWidget(self.f_narr, 3, 1, 1, 3)

        form.addWidget(QLabel("Amount (₹):"), 4, 0)
        self.f_amt = QDoubleSpinBox(); self.f_amt.setMaximum(9999999999); self.f_amt.setDecimals(2)
        self.f_amt.setGroupSeparatorShown(True)
        if rec: self.f_amt.setValue(float(rec.get("AMNT",0) or 0))
        form.addWidget(self.f_amt, 4, 1)

        if rec:
            drcr = str(rec.get("DRCR","D")).upper()
            if drcr == "D": self.f_dr.setText(str(rec.get("ACCD","")).strip())
            else: self.f_cr.setText(str(rec.get("ACCD","")).strip())

        layout.addLayout(form)
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save (F9)"); btn_save.setProperty("class","primary")
        btn_save.setShortcut("F9"); btn_save.clicked.connect(self.accept)
        btn_can = QPushButton("Cancel"); btn_can.clicked.connect(self.reject)
        btn_row.addStretch(); btn_row.addWidget(btn_save); btn_row.addWidget(btn_can)
        layout.addLayout(btn_row)

    def _lookup(self, target):
        dlg = AccountLookupDialog(self.year, self)
        if dlg.exec() and dlg.chosen: target.setText(dlg.chosen)

    def get_records(self):
        """Returns (dr_rec, cr_rec) pair for double-entry."""
        qd = self.f_date.date()
        date = datetime.date(qd.year(), qd.month(), qd.day())
        vrno = self.f_vrno.text().strip()[:6]
        narr = self.f_narr.text().strip()[:90]
        amt = self.f_amt.value()
        base = {"DATE": date, "VRNO": vrno, "NARR": narr, "AMNT": amt, "DOCD": "81", "SRNO": 1}
        dr = {**base, "ACCD": self.f_dr.text().strip().upper()[:6], "DRCR": "D", "PYTRCT": "R"}
        cr = {**base, "ACCD": self.f_cr.text().strip().upper()[:6], "DRCR": "C", "PYTRCT": "P"}
        return dr, cr

    def validate(self):
        if not self.f_dr.text().strip():
            QMessageBox.warning(self,"Validation","Debit A/c required."); return False
        if not self.f_cr.text().strip():
            QMessageBox.warning(self,"Validation","Credit A/c required."); return False
        if self.f_amt.value() <= 0:
            QMessageBox.warning(self,"Validation","Amount must be > 0."); return False
        return True

    def accept(self):
        if self.validate(): super().accept()


# ─────────────────────────────────────────────────────────────────────────────
# SALES ENTRY DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class SalesEntryDialog(QDialog):
    def __init__(self, year, rec=None, parent=None):
        super().__init__(parent)
        self.year = year; self.rec = rec
        self.setWindowTitle("Sales Bill Entry")
        self.setStyleSheet(APP_STYLE)
        configure_entry_dialog(self)
        self._accounts = get_accounts_dict(year)
        layout = QVBoxLayout(self); layout.setSpacing(10)
        form = QGridLayout(); form.setSpacing(8)

        form.addWidget(QLabel("Receipt Date:"), 0, 0)
        self.f_date = QDateEdit(); self.f_date.setDisplayFormat("dd/MM/yy")
        self.f_date.setCalendarPopup(True)
        d = rec_value(rec or {}, "RCTDT", "RCTDTOTK", default=None) if rec else None
        self.f_date.setDate(QDate(d.year,d.month,d.day) if d else QDate.currentDate())
        form.addWidget(self.f_date, 0, 1)

        form.addWidget(QLabel("Bill No:"), 0, 2)
        self.f_billno = QLineEdit()
        self.f_billno.setText(str(rec_value(rec or {}, "SBILLNO", "SBILLNOTK", default="")).strip() if rec else "")
        form.addWidget(self.f_billno, 0, 3)

        form.addWidget(QLabel("Party A/c:"), 1, 0)
        p_row = QHBoxLayout()
        self.f_party = QLineEdit(); self.f_party.setFixedWidth(100)
        self.f_party.setText(str(rec_value(rec or {}, "ACCD", "ACCDOTK", default="")).strip() if rec else "")
        self.f_party.textChanged.connect(lambda t: self.f_pname.setText(self._accounts.get(t.strip().upper(),"")))
        btn_p = QPushButton("..."); btn_p.setFixedWidth(40); btn_p.clicked.connect(self._lookup)
        p_row.addWidget(self.f_party); p_row.addWidget(btn_p); p_row.addStretch()
        form.addLayout(p_row, 1, 1)
        form.addWidget(QLabel("Party Name:"), 1, 2)
        self.f_pname = QLineEdit(); self.f_pname.setReadOnly(True)
        self.f_pname.setText(self._accounts.get(str(rec_value(rec or {}, "ACCD", "ACCDOTK", default="")).strip(),"") if rec else "")
        form.addWidget(self.f_pname, 1, 3)

        form.addWidget(QLabel("Vehicle No:"), 2, 0)
        self.f_veh = QLineEdit()
        self.f_veh.setText(str(rec_value(rec or {}, "VEHICLENO", "VEHICLENOK", "VEHNOTK", default="")).strip() if rec else "")
        form.addWidget(self.f_veh, 2, 1)

        form.addWidget(QLabel("Sales Amt (₹):"), 3, 0)
        self.f_salamt = QDoubleSpinBox(); self.f_salamt.setMaximum(9999999999); self.f_salamt.setDecimals(2)
        self.f_salamt.setGroupSeparatorShown(True)
        if rec: self.f_salamt.setValue(float(rec_value(rec, "SLSAMT", "SLSAMTTK", default=0) or 0))
        form.addWidget(self.f_salamt, 3, 1)

        form.addWidget(QLabel("Total Amt (₹):"), 3, 2)
        self.f_totamt = QDoubleSpinBox(); self.f_totamt.setMaximum(9999999999); self.f_totamt.setDecimals(2)
        self.f_totamt.setGroupSeparatorShown(True)
        if rec: self.f_totamt.setValue(float(rec_value(rec, "TOTAMT", "TOTAMTTK", default=0) or 0))
        form.addWidget(self.f_totamt, 3, 3)

        form.addWidget(QLabel("Credit Sale:"), 4, 0)
        self.f_credit = QCheckBox("Yes (Credit)")
        if rec: self.f_credit.setChecked(bool(rec_value(rec, "ISCREDIT", "ISCREDITTK", default=False)))
        form.addWidget(self.f_credit, 4, 1)

        form.addWidget(QLabel("Narration:"), 5, 0)
        self.f_narr = QLineEdit(); self.f_narr.setMaxLength(90)
        self.f_narr.setText(str(rec_value(rec or {}, "NOTE", "NOTECEK", "NARRTK", default="")).strip() if rec else "")
        form.addWidget(self.f_narr, 5, 1, 1, 3)

        layout.addLayout(form)
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save (F9)"); btn_save.setProperty("class","primary")
        btn_save.setShortcut("F9"); btn_save.clicked.connect(self.accept)
        btn_can = QPushButton("Cancel"); btn_can.clicked.connect(self.reject)
        btn_row.addStretch(); btn_row.addWidget(btn_save); btn_row.addWidget(btn_can)
        layout.addLayout(btn_row)

    def _lookup(self):
        dlg = AccountLookupDialog(self.year, self)
        if dlg.exec() and dlg.chosen: self.f_party.setText(dlg.chosen)

    def get_record(self):
        qd = self.f_date.date()
        return {
            "RCTDTOTK": datetime.date(qd.year(), qd.month(), qd.day()),
            "SBILLNOTK": self.f_billno.text().strip()[:10],
            "ACCDOTK": self.f_party.text().strip().upper()[:6],
            "VEHICLENOK": self.f_veh.text().strip()[:15],
            "SLSAMTTK": self.f_salamt.value(),
            "TOTAMTTK": self.f_totamt.value(),
            "ISCREDITTK": self.f_credit.isChecked(),
            "NOTECEK": self.f_narr.text().strip()[:78],
        }

    def validate(self):
        if not self.f_party.text().strip():
            QMessageBox.warning(self,"Validation","Party A/c Code required."); return False
        if self.f_totamt.value() <= 0:
            QMessageBox.warning(self,"Validation","Total Amount must be > 0."); return False
        return True

    def accept(self):
        if self.validate(): super().accept()


class SalesEntryPage(QWidget):
    def __init__(self, year, company, module, rec=None, recno=None, parent=None):
        super().__init__(parent)
        self.year = year
        self.company = company
        self.module = module
        self.rec = rec
        self.recno = recno
        self._accounts = get_accounts_dict(year)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        title = QLabel("NEW BILL" if self.rec is None else "EDIT BILL")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22px;color:#ffffff;border:1px solid #c0c0c0;padding:4px;")
        layout.addWidget(title)

        form_box = QGroupBox("Sales Entry")
        form_layout = QGridLayout(form_box)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Receipt Date:"), 0, 0)
        self.f_date = QDateEdit()
        self.f_date.setDisplayFormat("dd/MM/yy")
        self.f_date.setCalendarPopup(True)
        d = rec_value(self.rec or {}, "RCTDT", "RCTDTOTK", default=None) if self.rec else None
        self.f_date.setDate(QDate(d.year, d.month, d.day) if d else QDate.currentDate())
        form_layout.addWidget(self.f_date, 0, 1)

        form_layout.addWidget(QLabel("Bill No:"), 0, 2)
        self.f_billno = QLineEdit(str(rec_value(self.rec or {}, "SBILLNO", "SBILLNOTK", default="")).strip() if self.rec else "")
        form_layout.addWidget(self.f_billno, 0, 3)

        form_layout.addWidget(QLabel("Party A/c:"), 1, 0)
        party_row = QHBoxLayout()
        self.f_party = QLineEdit(str(rec_value(self.rec or {}, "ACCD", "ACCDOTK", default="")).strip() if self.rec else "")
        self.f_party.setFixedWidth(120)
        self.f_party.textChanged.connect(lambda t: self.f_pname.setText(self._accounts.get(t.strip().upper(), "")))
        btn_lookup = QPushButton("Lookup")
        btn_lookup.setFixedWidth(90)
        btn_lookup.clicked.connect(self._lookup)
        party_row.addWidget(self.f_party)
        party_row.addWidget(btn_lookup)
        party_row.addStretch()
        form_layout.addLayout(party_row, 1, 1)

        form_layout.addWidget(QLabel("Party Name:"), 1, 2)
        self.f_pname = QLineEdit()
        self.f_pname.setReadOnly(True)
        self.f_pname.setText(self._accounts.get(str(rec_value(self.rec or {}, "ACCD", "ACCDOTK", default="")).strip(), "") if self.rec else "")
        form_layout.addWidget(self.f_pname, 1, 3)

        form_layout.addWidget(QLabel("Vehicle No:"), 2, 0)
        self.f_veh = QLineEdit(str(rec_value(self.rec or {}, "VEHICLENO", "VEHICLENOK", "VEHNOTK", default="")).strip() if self.rec else "")
        form_layout.addWidget(self.f_veh, 2, 1)

        form_layout.addWidget(QLabel("Sales Amt:"), 3, 0)
        self.f_salamt = QDoubleSpinBox()
        self.f_salamt.setMaximum(9999999999)
        self.f_salamt.setDecimals(2)
        self.f_salamt.setGroupSeparatorShown(True)
        if self.rec:
            self.f_salamt.setValue(float(rec_value(self.rec, "SLSAMT", "SLSAMTTK", default=0) or 0))
        form_layout.addWidget(self.f_salamt, 3, 1)

        form_layout.addWidget(QLabel("Total Amt:"), 3, 2)
        self.f_totamt = QDoubleSpinBox()
        self.f_totamt.setMaximum(9999999999)
        self.f_totamt.setDecimals(2)
        self.f_totamt.setGroupSeparatorShown(True)
        if self.rec:
            self.f_totamt.setValue(float(rec_value(self.rec, "TOTAMT", "TOTAMTTK", default=0) or 0))
        form_layout.addWidget(self.f_totamt, 3, 3)

        form_layout.addWidget(QLabel("Credit Sale:"), 4, 0)
        self.f_credit = QCheckBox("Yes")
        if self.rec:
            self.f_credit.setChecked(bool(rec_value(self.rec, "ISCREDIT", "ISCREDITTK", default=False)))
        form_layout.addWidget(self.f_credit, 4, 1)

        form_layout.addWidget(QLabel("Narration:"), 5, 0)
        self.f_narr = QLineEdit(str(rec_value(self.rec or {}, "NOTE", "NOTECEK", "NARRTK", default="")).strip() if self.rec else "")
        form_layout.addWidget(self.f_narr, 5, 1, 1, 3)
        layout.addWidget(form_box)

        btn_row = QHBoxLayout()
        btn_back = QPushButton("Back")
        btn_back.clicked.connect(lambda: self.window()._go_back())
        btn_save = QPushButton("Save")
        btn_save.setProperty("class", "primary")
        btn_save.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(btn_back)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)
        layout.addStretch()

    def _lookup(self):
        dlg = AccountLookupDialog(self.year, self)
        if dlg.exec() and dlg.chosen:
            self.f_party.setText(dlg.chosen)

    def _get_record(self):
        qd = self.f_date.date()
        return {
            "RCTDTOTK": datetime.date(qd.year(), qd.month(), qd.day()),
            "SBILLNOTK": self.f_billno.text().strip()[:10],
            "ACCDOTK": self.f_party.text().strip().upper()[:6],
            "VEHICLENOK": self.f_veh.text().strip()[:15],
            "SLSAMTTK": self.f_salamt.value(),
            "TOTAMTTK": self.f_totamt.value(),
            "ISCREDITTK": self.f_credit.isChecked(),
            "NOTECEK": self.f_narr.text().strip()[:78],
        }

    def _save(self):
        if not self.f_party.text().strip():
            QMessageBox.warning(self, "Validation", "Party A/c Code required.")
            return
        if self.f_totamt.value() <= 0:
            QMessageBox.warning(self, "Validation", "Total Amount must be greater than 0.")
            return
        record = self._get_record()
        if self.recno is None:
            ok = write_record("SREG41", self.year, record)
        else:
            ok = update_record("SREG41", self.year, recno=self.recno, updates=record)
        if not ok:
            QMessageBox.critical(self, "Error", "Save failed.")
            return
        self.module.load_data()
        QMessageBox.information(self, "Saved", "Sales bill saved.")
        self.window()._go_back()


class TableCatalogModule(QWidget):
    def __init__(self, year, company, open_table, parent=None):
        super().__init__(parent)
        self.year = year
        self.company = company
        self.open_table = open_table
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self.load_data()

    def _make_table(self, headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _toolbar_btn(self, label, cls=""):
        button = QPushButton(label)
        if cls:
            button.setProperty("class", cls)
        button.setFixedHeight(28)
        return button

    def _title_bar(self, title):
        label = QLabel(title)
        label.setStyleSheet("font-size:15px;font-weight:bold;color:#ffffff;padding:4px 0;")
        return label

    def _search_box(self, placeholder="Search..."):
        box = QLineEdit()
        box.setPlaceholderText(placeholder)
        box.setFixedWidth(220)
        box.setClearButtonEnabled(True)
        return box

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.addWidget(self._title_bar("DATABASE TABLES"))

        top = QHBoxLayout()
        self.search_box = self._search_box("Search table...")
        top.addWidget(QLabel("Search"))
        top.addWidget(self.search_box)
        top.addStretch()
        self.btn_open = self._toolbar_btn("Open Table", "primary")
        top.addWidget(self.btn_open)
        layout.addLayout(top)

        self.table = self._make_table(["Table", "Rows", "Fields", "Status"])
        self.table.setColumnWidth(0, 220)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 240)
        self.table.doubleClicked.connect(self._open_selected)
        layout.addWidget(self.table)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#888;font-size:12px;padding:2px;")
        layout.addWidget(self.lbl_status)

        self.search_box.textChanged.connect(self._apply_search)
        self.btn_open.clicked.connect(self._open_selected)

    def load_data(self):
        self.table.setRowCount(0)
        rows = []
        for table_name in list_table_bases(self.year):
            count = count_records(table_name, self.year)
            fields = get_table_fields(table_name, self.year)
            status = "Linked screen" if table_name in {
                "ACDOC", "ACMST", "ALLOC", "BRMST", "GL", "GRPMST", "ITMST", "JBK81", "PREG61", "SREG41"
            } else "Generic browser"
            rows.append((table_name, count, len(fields), status))
        rows.sort(key=lambda item: item[0])
        for table_name, count, field_count, status in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate([table_name, str(count), str(field_count), status]):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, table_name)
                if col in (1, 2):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)
        self.lbl_status.setText(f"  Reachable tables: {len(rows)}")

    def _apply_search(self, text):
        q = text.lower()
        for row in range(self.table.rowCount()):
            match = any(q in (self.table.item(row, c).text().lower() if self.table.item(row, c) else "")
                        for c in range(self.table.columnCount()))
            self.table.setRowHidden(row, not match if q else False)

    def _open_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "", "Select a table.")
            return
        item = self.table.item(row, 0)
        if not item:
            return
        table_name = item.data(Qt.ItemDataRole.UserRole) or item.text()
        self.open_table(table_name)


class GenericTableModule(QWidget):
    def __init__(self, year, company, table_name, parent=None):
        super().__init__(parent)
        self.year = year
        self.company = company
        self.table_name = table_name
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self.load_data()

    def _title_bar(self, title):
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        left = QFrame()
        left.setFrameShape(QFrame.Shape.HLine)
        left.setStyleSheet("color:#d0d0d0;")
        right = QFrame()
        right.setFrameShape(QFrame.Shape.HLine)
        right.setStyleSheet("color:#d0d0d0;")
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            "font-size:18px; color:#000000; background:#d0d0d0; padding:2px 14px; border:2px solid #d0d0d0;"
        )
        layout.addWidget(left, 1)
        layout.addWidget(label)
        layout.addWidget(right, 1)
        return wrapper

    def _search_box(self, placeholder="Search…"):
        box = QLineEdit()
        box.setPlaceholderText(placeholder)
        box.setFixedWidth(220)
        box.setClearButtonEnabled(True)
        return box

    def _footer_bar(self, text):
        bar = QLabel(text)
        bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar.setStyleSheet("color:#ffffff; font-size:16px; padding:10px 8px 4px 8px;")
        return bar

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.addWidget(self._title_bar(f"TABLE {self.table_name}"))

        top = QHBoxLayout()
        self.search_box = self._search_box("Search row values...")
        top.addWidget(QLabel("Search"))
        top.addWidget(self.search_box)
        top.addStretch()
        layout.addLayout(top)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        layout.addWidget(self._footer_bar("Alt_N/Alt_P-Print  Alt_E-Export  Esc-Exit"))

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#888;font-size:12px;padding:2px;")
        layout.addWidget(self.lbl_status)
        self.search_box.textChanged.connect(self._apply_search)

    def load_data(self):
        fields = get_table_fields(self.table_name, self.year)
        field_names = [field["name"] for field in fields]
        records = read_table(self.table_name, self.year, limit=500)
        self.table.setColumnCount(len(field_names))
        self.table.setHorizontalHeaderLabels(field_names)
        self.table.setRowCount(0)
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, field_name in enumerate(field_names):
                value = record.get(field_name, "")
                if isinstance(value, datetime.date):
                    value = value.strftime("%d/%m/%Y")
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.lbl_status.setText(f"  Showing {len(records)} rows from {self.table_name}")

    def _apply_search(self, text):
        q = text.lower()
        for row in range(self.table.rowCount()):
            match = any(q in (self.table.item(row, c).text().lower() if self.table.item(row, c) else "")
                        for c in range(self.table.columnCount()))
            self.table.setRowHidden(row, not match if q else False)


# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE ENTRY DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class PurchaseEntryDialog(QDialog):
    def __init__(self, year, rec=None, parent=None):
        super().__init__(parent)
        self.year = year; self.rec = rec
        self.setWindowTitle("Purchase Entry")
        self.setStyleSheet(APP_STYLE)
        configure_entry_dialog(self)
        self._accounts = get_accounts_dict(year)
        layout = QVBoxLayout(self); layout.setSpacing(10)
        form = QGridLayout(); form.setSpacing(8)

        form.addWidget(QLabel("Receipt Date:"), 0, 0)
        self.f_rctdt = QDateEdit(); self.f_rctdt.setDisplayFormat("dd/MM/yy"); self.f_rctdt.setCalendarPopup(True)
        d = rec.get("RCTDT") if rec else None
        self.f_rctdt.setDate(QDate(d.year,d.month,d.day) if d else QDate.currentDate())
        form.addWidget(self.f_rctdt, 0, 1)

        form.addWidget(QLabel("Bill Date:"), 0, 2)
        self.f_billdt = QDateEdit(); self.f_billdt.setDisplayFormat("dd/MM/yy"); self.f_billdt.setCalendarPopup(True)
        bd = rec.get("BILLDT") if rec else None
        self.f_billdt.setDate(QDate(bd.year,bd.month,bd.day) if bd else QDate.currentDate())
        form.addWidget(self.f_billdt, 0, 3)

        form.addWidget(QLabel("Bill No:"), 1, 0)
        self.f_billno = QLineEdit()
        self.f_billno.setText(str(rec.get("PBILLNO","")).strip() if rec else "")
        form.addWidget(self.f_billno, 1, 1)

        form.addWidget(QLabel("Challan No:"), 1, 2)
        self.f_chlno = QLineEdit()
        self.f_chlno.setText(str(rec.get("CHLNO","")).strip() if rec else "")
        form.addWidget(self.f_chlno, 1, 3)

        form.addWidget(QLabel("Supplier A/c:"), 2, 0)
        sup_row = QHBoxLayout()
        self.f_accd = QLineEdit(); self.f_accd.setFixedWidth(100)
        self.f_accd.setText(str(rec.get("ACCD","")).strip() if rec else "")
        self.f_accd.textChanged.connect(lambda t: self.f_supname.setText(self._accounts.get(t.strip().upper(),"")))
        btn_s = QPushButton("..."); btn_s.setFixedWidth(40); btn_s.clicked.connect(self._lookup)
        sup_row.addWidget(self.f_accd); sup_row.addWidget(btn_s); sup_row.addStretch()
        form.addLayout(sup_row, 2, 1)
        form.addWidget(QLabel("Supplier Name:"), 2, 2)
        self.f_supname = QLineEdit(); self.f_supname.setReadOnly(True)
        self.f_supname.setText(self._accounts.get(str(rec.get("ACCD","")).strip(),"") if rec else "")
        form.addWidget(self.f_supname, 2, 3)

        form.addWidget(QLabel("Purchase Amt (₹):"), 3, 0)
        self.f_amt = QDoubleSpinBox(); self.f_amt.setMaximum(9999999999); self.f_amt.setDecimals(2)
        self.f_amt.setGroupSeparatorShown(True)
        if rec: self.f_amt.setValue(float(rec.get("PURAMT",0) or 0))
        form.addWidget(self.f_amt, 3, 1)

        layout.addLayout(form)
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save (F9)"); btn_save.setProperty("class","primary")
        btn_save.setShortcut("F9"); btn_save.clicked.connect(self.accept)
        btn_can = QPushButton("Cancel"); btn_can.clicked.connect(self.reject)
        btn_row.addStretch(); btn_row.addWidget(btn_save); btn_row.addWidget(btn_can)
        layout.addLayout(btn_row)

    def _lookup(self):
        dlg = AccountLookupDialog(self.year, self)
        if dlg.exec() and dlg.chosen: self.f_accd.setText(dlg.chosen)

    def get_record(self):
        qd = self.f_rctdt.date(); qb = self.f_billdt.date()
        return {
            "RCTDT": datetime.date(qd.year(), qd.month(), qd.day()),
            "BILLDT": datetime.date(qb.year(), qb.month(), qb.day()),
            "PBILLNO": self.f_billno.text().strip()[:10],
            "CHLNO": self.f_chlno.text().strip()[:10],
            "ACCD": self.f_accd.text().strip().upper()[:6],
            "PURAMT": self.f_amt.value(),
        }

    def validate(self):
        if not self.f_accd.text().strip():
            QMessageBox.warning(self,"Validation","Supplier A/c required."); return False
        if self.f_amt.value() <= 0:
            QMessageBox.warning(self,"Validation","Amount must be > 0."); return False
        return True

    def accept(self):
        if self.validate(): super().accept()


# ─────────────────────────────────────────────────────────────────────────────
# ACCOUNT MASTER EDIT DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class AccountEditDialog(QDialog):
    def __init__(self, year, rec=None, parent=None):
        super().__init__(parent)
        self.year = year; self.rec = rec
        self.setWindowTitle("Edit Account" if rec else "New Account")
        self.setMinimumWidth(500); self.setStyleSheet(APP_STYLE)
        layout = QVBoxLayout(self); layout.setSpacing(10)
        form = QFormLayout(); form.setSpacing(8)

        self.f_code = QLineEdit(); self.f_code.setMaxLength(6)
        if rec:
            self.f_code.setText(str(rec.get("AC_CODE","")).strip())
            self.f_code.setReadOnly(True)
        form.addRow("Account Code:", self.f_code)

        self.f_name = QLineEdit(); self.f_name.setMaxLength(40)
        self.f_name.setText(str(rec.get("AC_HEAD","")).strip() if rec else "")
        form.addRow("Account Name:", self.f_name)

        groups = read_table("GRPMST", year)
        self.f_grp = QComboBox()
        grp_list = [(str(r.get("GRCD","")).strip(), str(r.get("GRHD","")).strip()) for r in groups]
        for code, name in grp_list:
            self.f_grp.addItem(f"{code} — {name}", code)
        if rec:
            grcd = str(rec.get("AC_GRCD","")).strip()
            idx = next((i for i,(c,n) in enumerate(grp_list) if c==grcd), 0)
            self.f_grp.setCurrentIndex(idx)
        form.addRow("Group:", self.f_grp)

        self.f_city = QLineEdit(); self.f_city.setMaxLength(20)
        self.f_city.setText(str(rec.get("CITY","")).strip() if rec else "")
        form.addRow("City:", self.f_city)

        self.f_phone = QLineEdit(); self.f_phone.setMaxLength(20)
        self.f_phone.setText(str(rec.get("PHONE","")).strip() if rec else "")
        form.addRow("Phone:", self.f_phone)

        self.f_op = QDoubleSpinBox(); self.f_op.setMaximum(9999999999); self.f_op.setDecimals(2)
        self.f_op.setMinimum(-9999999999); self.f_op.setGroupSeparatorShown(True)
        self.f_op.setValue(float(rec.get("YEAROP",0) or 0) if rec else 0)
        form.addRow("Opening Balance (₹):", self.f_op)

        layout.addLayout(form)
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save"); btn_save.setProperty("class","primary"); btn_save.clicked.connect(self.accept)
        btn_can = QPushButton("Cancel"); btn_can.clicked.connect(self.reject)
        btn_row.addStretch(); btn_row.addWidget(btn_save); btn_row.addWidget(btn_can)
        layout.addLayout(btn_row)

    def get_record(self):
        return {
            "AC_CODE": self.f_code.text().strip().upper()[:6],
            "AC_HEAD": self.f_name.text().strip()[:40],
            "AC_GRCD": self.f_grp.currentData() or "",
            "CITY": self.f_city.text().strip()[:20],
            "PHONE": self.f_phone.text().strip()[:20],
            "YEAROP": self.f_op.value(),
            "CURBAL": self.f_op.value(),
        }

    def validate(self):
        if not self.f_code.text().strip():
            QMessageBox.warning(self,"Validation","Account Code required."); return False
        if not self.f_name.text().strip():
            QMessageBox.warning(self,"Validation","Account Name required."); return False
        return True

    def accept(self):
        if self.validate(): super().accept()

# ─────────────────────────────────────────────────────────────────────────────
# BASE MODULE WIDGET
# ─────────────────────────────────────────────────────────────────────────────
class ModuleBase(QWidget):
    def __init__(self, year, company, parent=None):
        super().__init__(parent)
        self.year = year; self.company = company
        self._records = []   # list of dicts (include _recno)
        self.setStyleSheet(APP_STYLE)

    def _make_table(self, headers):
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setStretchLastSection(True)
        t.setSortingEnabled(True)
        t.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        return t

    def _set_item(self, table, row, col, text, align_right=False):
        item = QTableWidgetItem(str(text))
        if align_right:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        table.setItem(row, col, item)

    def _toolbar_btn(self, label, icon="", shortcut=None, cls=""):
        btn = QPushButton(f"{icon} {label}".strip())
        if cls: btn.setProperty("class", cls)
        if shortcut: btn.setShortcut(shortcut)
        btn.setFixedHeight(30)
        return btn

    def _title_bar(self, title):
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        left = QFrame()
        left.setFrameShape(QFrame.Shape.HLine)
        left.setStyleSheet("color:#d0d0d0;")
        right = QFrame()
        right.setFrameShape(QFrame.Shape.HLine)
        right.setStyleSheet("color:#d0d0d0;")
        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            "font-size:18px; color:#000000; background:#d0d0d0; padding:2px 14px; border:2px solid #d0d0d0;"
        )
        layout.addWidget(left, 1)
        layout.addWidget(lbl)
        layout.addWidget(right, 1)
        return wrapper

    def _search_box(self, placeholder="Search…"):
        box = QLineEdit(); box.setPlaceholderText(placeholder)
        box.setFixedWidth(220); box.setClearButtonEnabled(True)
        return box

    def _date_filter(self):
        f = QDateEdit(); f.setDisplayFormat("dd/MM/yy"); f.setCalendarPopup(True)
        f.setDate(QDate(QDate.currentDate().year() - 3, 4, 1))
        return f

    def _get_rows_for_export(self, table):
        rows = []
        for r in range(table.rowCount()):
            rows.append([table.item(r,c).text() if table.item(r,c) else "" for c in range(table.columnCount())])
        return rows

    def _get_headers(self, table):
        return [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]

    def _clipper_group(self, title):
        group = QGroupBox(title)
        group.setStyleSheet(
            "QGroupBox { border:2px solid #d0d0d0; margin-top:14px; padding-top:16px; } "
            "QGroupBox::title { color:#000000; background:#d0d0d0; subcontrol-origin: margin; "
            "subcontrol-position: top center; padding:1px 12px; }"
        )
        return group

    def _footer_bar(self, text):
        bar = QLabel(text)
        bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar.setStyleSheet("color:#ffffff; font-size:16px; padding:10px 8px 4px 8px;")
        return bar


# ─────────────────────────────────────────────────────────────────────────────
# CASH / BANK BOOK MODULE
# ─────────────────────────────────────────────────────────────────────────────
class CashBankBookModule(ModuleBase):
    def __init__(self, year, company, docd, book_name, main_accd, parent=None):
        super().__init__(year, company, parent)
        self.docd = docd; self.book_name = book_name; self.main_accd = main_accd
        self.tbl_name = get_cbk_file(docd)
        self._accounts = get_accounts_dict(year)
        self._edit_recno = None
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,4)
        layout.addWidget(self._title_bar(self.book_name.upper()))

        browse_group = self._clipper_group(self.book_name.upper())
        browse_layout = QVBoxLayout(browse_group)
        self.table = self._make_table(["Date","Voucher","A/c Code","Account Name","Narration","Receipt ₹","Payment ₹","Cheque"])
        self.table.setColumnWidth(0,90); self.table.setColumnWidth(1,90)
        self.table.setColumnWidth(2,80); self.table.setColumnWidth(3,180)
        self.table.setColumnWidth(4,180); self.table.setColumnWidth(5,110)
        self.table.setColumnWidth(6,110); self.table.setColumnWidth(7,100)
        self.table.doubleClicked.connect(self._edit_entry)
        browse_layout.addWidget(self.table)
        layout.addWidget(browse_group, 1)

        entry_group = self._clipper_group("NEW ENTRY")
        form = QGridLayout(entry_group)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        self.f_date = QLineEdit(datetime.date.today().strftime("%d/%m/%y"))
        self.f_accd = QLineEdit()
        self.f_narr = QLineEdit()
        self.f_rct = QLineEdit("0.00")
        self.f_pyt = QLineEdit("0.00")
        for widget, width in [(self.f_date, 120), (self.f_accd, 120), (self.f_rct, 120), (self.f_pyt, 120)]:
            widget.setMaximumWidth(width)
        form.addWidget(QLabel("Date"), 0, 0)
        form.addWidget(QLabel("A/c.Code"), 0, 1)
        form.addWidget(QLabel("Narration"), 0, 2)
        form.addWidget(QLabel("Rct. Amt."), 0, 3)
        form.addWidget(QLabel("Pyt. Amt."), 0, 4)
        form.addWidget(self.f_date, 1, 0)
        form.addWidget(self.f_accd, 1, 1)
        form.addWidget(self.f_narr, 1, 2)
        form.addWidget(self.f_rct, 1, 3)
        form.addWidget(self.f_pyt, 1, 4)
        btn_row = QHBoxLayout()
        self.btn_lookup = self._toolbar_btn("Lookup")
        self.btn_save = self._toolbar_btn("Save", cls="primary")
        self.btn_delete = self._toolbar_btn("Delete", cls="danger")
        self.btn_print = self._toolbar_btn("Print")
        self.btn_pdf = self._toolbar_btn("PDF")
        self.btn_csv = self._toolbar_btn("CSV")
        self.btn_clear = self._toolbar_btn("Clear")
        for button in [self.btn_lookup, self.btn_save, self.btn_delete, self.btn_print, self.btn_pdf, self.btn_csv, self.btn_clear]:
            btn_row.addWidget(button)
        btn_row.addStretch()
        form.addLayout(btn_row, 2, 0, 1, 5)
        layout.addWidget(entry_group)
        layout.addWidget(self._footer_bar("F10-Add  F2-Edit  F3-List  F4-Del  1-Go Date  F5-Receipt  F6-Qck_Del"))

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#ffffff;font-size:18px;padding:6px 0;")
        layout.addWidget(self.lbl_status)

        self.btn_lookup.clicked.connect(self._lookup_account)
        self.btn_save.clicked.connect(self._save_inline_entry)
        self.btn_delete.clicked.connect(self._delete_entry)
        self.btn_print.clicked.connect(self._print)
        self.btn_pdf.clicked.connect(self._pdf)
        self.btn_csv.clicked.connect(self._csv)
        self.btn_clear.clicked.connect(self._reset_entry_form)

    def load_data(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self._records = read_table(self.tbl_name, self.year)
        self._records.sort(key=lambda r: (r.get("DATE") or datetime.date.min, str(r.get("VRNO","") or "")))

        shown = 0; total_rct = 0.0; total_pyt = 0.0
        for r in self._records:
            dt = r.get("DATE")
            row = self.table.rowCount(); self.table.insertRow(row)
            dt_s = dt.strftime("%d/%m/%y") if dt else ""
            accd = str(r.get("ACCD","")).strip()
            amt = float(r.get("AMNT",0) or 0)
            drcr = str(r.get("DRCR","D")).strip().upper()
            is_rct = drcr in ("D","") or str(r.get("PYTRCT","")).strip().upper() == "R"
            rct_s = fmt_amount(amt) if is_rct else ""
            pyt_s = fmt_amount(amt) if not is_rct else ""
            if is_rct: total_rct += amt
            else: total_pyt += amt

            vals = [dt_s, str(r.get("VRNO","")).strip(), accd,
                    self._accounts.get(accd,accd)[:28],
                    str(r.get("NARR","")).strip()[:30],
                    rct_s, pyt_s, str(r.get("CHQNO","")).strip()]
            for col, val in enumerate(vals):
                sort_key = val
                if col == 0:
                    sort_key = dt or datetime.date.min
                elif col in (5, 6):
                    sort_key = amt if val else -1
                item = SortableItem(val, sort_key)
                if col in (5,6): item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                item.setData(Qt.ItemDataRole.UserRole, r.get("_recno"))
                self.table.setItem(row, col, item)
            shown += 1

        self.table.setSortingEnabled(True)
        bal = cash_balance(self.year, self.docd)
        today = datetime.date.today().strftime("%d/%m/%y")
        self.lbl_status.setText(f"  {today} ->  Bal    {fmt_amount(bal)}")

    def _lookup_account(self):
        dlg = AccountLookupDialog(self.year, self)
        if dlg.exec() and dlg.chosen:
            self.f_accd.setText(dlg.chosen)
            self.f_narr.setFocus()

    def _reset_entry_form(self):
        self._edit_recno = None
        self.f_date.setText(datetime.date.today().strftime("%d/%m/%y"))
        self.f_accd.clear()
        self.f_narr.clear()
        self.f_rct.setText("0.00")
        self.f_pyt.setText("0.00")
        self.f_accd.setFocus()

    def _save_inline_entry(self):
        accd = self.f_accd.text().strip().upper()
        if not accd:
            self.lbl_status.setText("  !! A/c Code is required !!")
            return
        try:
            rct = float(self.f_rct.text().strip() or 0)
            pyt = float(self.f_pyt.text().strip() or 0)
        except ValueError:
            self.lbl_status.setText("  !! Invalid amount !!")
            return
        if rct > 0 and pyt > 0:
            self.lbl_status.setText("  !! Enter receipt or payment, not both !!")
            return
        entry_date = parse_date(self.f_date.text().strip()) or datetime.date.today()
        amt = rct if rct > 0 else pyt
        drcr = "D" if rct > 0 else "C"
        record = {
            "ACCD": accd[:6],
            "DOCD": self.docd[:2],
            "DATE": entry_date,
            "VRNO": next_vrno(self.year, self.docd)[:6] if self._edit_recno is None else "",
            "NARR": self.f_narr.text().strip().upper()[:90],
            "PYTRCT": "R" if drcr == "D" else "P",
            "AMNT": amt,
            "SRNO": 1,
            "CHQNO": "",
            "CONDOCD": "",
            "DRCR": drcr,
            "COUNTCD": "",
        }
        if self._edit_recno is None:
            ok = write_record(self.tbl_name, self.year, record)
        else:
            record.pop("VRNO")
            ok = update_record(self.tbl_name, self.year, recno=self._edit_recno, updates=record)
        if not ok:
            self.lbl_status.setText("  !! Save failed !!")
            return
        self._reset_entry_form()
        self.load_data()

    def _get_selected_recno(self):
        row = self.table.currentRow()
        if row < 0: return None, None
        item = self.table.item(row, 0)
        return row, item.data(Qt.ItemDataRole.UserRole) if item else None

    def _get_rec_by_recno(self, recno):
        for r in self._records:
            if r.get("_recno") == recno: return r
        return None

    def _edit_entry(self):
        _, recno = self._get_selected_recno()
        if recno is None: QMessageBox.information(self,"","Select a row to edit."); return
        rec = self._get_rec_by_recno(recno)
        if not rec: return
        self._edit_recno = recno
        entry_date = rec.get("DATE")
        self.f_date.setText(entry_date.strftime("%d/%m/%y") if entry_date else datetime.date.today().strftime("%d/%m/%y"))
        self.f_accd.setText(str(rec.get("ACCD","")).strip())
        self.f_narr.setText(str(rec.get("NARR","")).strip())
        amt = float(rec.get("AMNT",0) or 0)
        is_rct = str(rec.get("DRCR","D")).strip().upper() in ("D","") or str(rec.get("PYTRCT","")).strip().upper()=="R"
        self.f_rct.setText(f"{amt:.2f}" if is_rct else "0.00")
        self.f_pyt.setText(f"{amt:.2f}" if not is_rct else "0.00")

    def _delete_entry(self):
        _, recno = self._get_selected_recno()
        if recno is None: QMessageBox.information(self,"","Select a row to delete."); return
        rec = self._get_rec_by_recno(recno)
        info = f"Date: {rec.get('DATE')}  A/c: {rec.get('ACCD')}  Amt: {rec.get('AMNT')}" if rec else ""
        ans = QMessageBox.question(self,"Confirm Delete",f"Delete this entry?\n{info}",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ans == QMessageBox.StandardButton.Yes:
            ok = delete_record(self.tbl_name, self.year, recno=recno)
            if ok: self.load_data()
            else: QMessageBox.critical(self,"Error","Delete failed.")

    def _get_export_data(self):
        headers = self._get_headers(self.table)
        rows = self._get_rows_for_export(self.table)
        return headers, rows

    def _print(self):
        h, rows = self._get_export_data()
        html = _make_html(self.book_name, self.company, h, rows)
        do_print(self, html)

    def _pdf(self):
        h, rows = self._get_export_data()
        html = _make_html(self.book_name, self.company, h, rows)
        do_pdf(self, self.book_name, html)

    def _csv(self):
        h, rows = self._get_export_data()
        do_csv(self, self.book_name, h, rows)


# ─────────────────────────────────────────────────────────────────────────────
# JOURNAL MODULE
# ─────────────────────────────────────────────────────────────────────────────
class JournalModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._accounts = get_accounts_dict(year)
        self._edit_pair = None
        self._build_ui(); self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,4)
        layout.addWidget(self._title_bar("JOURNAL"))

        browse_group = self._clipper_group("JOURNAL")
        browse_layout = QVBoxLayout(browse_group)
        self.table = self._make_table(["Date","Voucher","Dr A/c","Debit Name","Cr A/c","Credit Name","Narration","Amount ₹"])
        self.table.setColumnWidth(0,90); self.table.setColumnWidth(1,90)
        self.table.setColumnWidth(2,85); self.table.setColumnWidth(3,160)
        self.table.setColumnWidth(4,85); self.table.setColumnWidth(5,160)
        self.table.setColumnWidth(6,220); self.table.setColumnWidth(7,110)
        self.table.doubleClicked.connect(self._edit_entry)
        browse_layout.addWidget(self.table)
        layout.addWidget(browse_group, 1)

        entry_group = self._clipper_group("NEW ENTRY")
        form = QGridLayout(entry_group)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        self.f_date = QLineEdit(datetime.date.today().strftime("%d/%m/%y"))
        self.f_vrno = QLineEdit(next_vrno(self.year, "81"))
        self.f_dr = QLineEdit()
        self.f_cr = QLineEdit()
        self.f_narr = QLineEdit()
        self.f_amt = QLineEdit("0.00")
        for widget, width in [(self.f_date, 120), (self.f_vrno, 120), (self.f_dr, 120), (self.f_cr, 120), (self.f_amt, 120)]:
            widget.setMaximumWidth(width)
        form.addWidget(QLabel("Date"), 0, 0)
        form.addWidget(QLabel("Voucher"), 0, 1)
        form.addWidget(QLabel("Dr A/c"), 0, 2)
        form.addWidget(QLabel("Cr A/c"), 0, 3)
        form.addWidget(QLabel("Narration"), 0, 4)
        form.addWidget(QLabel("Amount"), 0, 5)
        form.addWidget(self.f_date, 1, 0)
        form.addWidget(self.f_vrno, 1, 1)
        form.addWidget(self.f_dr, 1, 2)
        form.addWidget(self.f_cr, 1, 3)
        form.addWidget(self.f_narr, 1, 4)
        form.addWidget(self.f_amt, 1, 5)

        btns = QHBoxLayout()
        self.btn_lookup_dr = self._toolbar_btn("Lookup Dr")
        self.btn_lookup_cr = self._toolbar_btn("Lookup Cr")
        self.btn_save = self._toolbar_btn("Save", cls="primary")
        self.btn_del = self._toolbar_btn("Delete", cls="danger")
        self.btn_print = self._toolbar_btn("Print")
        self.btn_pdf = self._toolbar_btn("PDF")
        self.btn_csv = self._toolbar_btn("CSV")
        self.btn_clear = self._toolbar_btn("Clear")
        for b in [self.btn_lookup_dr, self.btn_lookup_cr, self.btn_save, self.btn_del, self.btn_print, self.btn_pdf, self.btn_csv, self.btn_clear]:
            btns.addWidget(b)
        btns.addStretch()
        form.addLayout(btns, 2, 0, 1, 6)
        layout.addWidget(entry_group)
        layout.addWidget(self._footer_bar("F10-Add  F2-Edit  F3-List  F4-Del  1-Bill  2-Date  F5-Print"))

        self.lbl_status = QLabel(""); self.lbl_status.setStyleSheet("color:#ffffff;font-size:18px;padding:6px 0;")
        layout.addWidget(self.lbl_status)

        self.btn_lookup_dr.clicked.connect(lambda: self._lookup(self.f_dr))
        self.btn_lookup_cr.clicked.connect(lambda: self._lookup(self.f_cr))
        self.btn_save.clicked.connect(self._save_inline_entry)
        self.btn_del.clicked.connect(self._delete_entry)
        self.btn_print.clicked.connect(self._print)
        self.btn_pdf.clicked.connect(self._pdf)
        self.btn_csv.clicked.connect(self._csv)

    def load_data(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        raw_records = read_table("JBK81", self.year)
        grouped = {}
        for record in raw_records:
            key = (
                record.get("DATE") or datetime.date.min,
                str(record.get("VRNO", "") or "").strip(),
            )
            row = grouped.setdefault(key, {
                "DATE": record.get("DATE"),
                "VRNO": str(record.get("VRNO", "") or "").strip(),
                "NARR": str(record.get("NARR", "") or "").strip(),
                "AMNT": float(record.get("AMNT", 0) or 0),
                "DR": None,
                "CR": None,
            })
            if not row["NARR"]:
                row["NARR"] = str(record.get("NARR", "") or "").strip()
            if not row["AMNT"]:
                row["AMNT"] = float(record.get("AMNT", 0) or 0)
            if str(record.get("DRCR", "D")).strip().upper() == "C":
                row["CR"] = record
            else:
                row["DR"] = record
        self._records = [grouped[key] for key in sorted(grouped.keys())]
        total = 0.0
        for record in self._records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            dt = record.get("DATE")
            dr = record.get("DR") or {}
            cr = record.get("CR") or {}
            dr_accd = str(dr.get("ACCD", "")).strip()
            cr_accd = str(cr.get("ACCD", "")).strip()
            amt = float(record.get("AMNT", 0) or 0)
            total += amt
            vals = [
                dt.strftime("%d/%m/%y") if dt else "",
                record.get("VRNO", ""),
                dr_accd,
                self._accounts.get(dr_accd, dr_accd)[:24],
                cr_accd,
                self._accounts.get(cr_accd, cr_accd)[:24],
                record.get("NARR", "")[:34],
                fmt_amount(amt),
            ]
            for col, val in enumerate(vals):
                sort_key = val
                if col == 0:
                    sort_key = dt or datetime.date.min
                elif col == 7:
                    sort_key = amt
                item = SortableItem(val, sort_key)
                if col == 7:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                item.setData(Qt.ItemDataRole.UserRole, (
                    (dr.get("_recno") if dr else None),
                    (cr.get("_recno") if cr else None),
                ))
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.lbl_status.setText(f"  Journal Vouchers: {len(self._records)}   Total: {fmt_amount(total)}")
        if self._edit_pair is None:
            self._reset_entry_form()

    def _get_selected_recno(self):
        row = self.table.currentRow()
        if row < 0: return None, None
        item = self.table.item(row, 0)
        return row, item.data(Qt.ItemDataRole.UserRole) if item else None

    def _lookup(self, target):
        dlg = AccountLookupDialog(self.year, self)
        if dlg.exec() and dlg.chosen:
            target.setText(dlg.chosen)

    def _reset_entry_form(self):
        self._edit_pair = None
        self.f_date.setText(datetime.date.today().strftime("%d/%m/%y"))
        self.f_vrno.setText(next_vrno(self.year, "81"))
        self.f_dr.clear()
        self.f_cr.clear()
        self.f_narr.clear()
        self.f_amt.setText("0.00")
        self.f_dr.setFocus()

    def _save_inline_entry(self):
        dr_accd = self.f_dr.text().strip().upper()
        cr_accd = self.f_cr.text().strip().upper()
        if not dr_accd or not cr_accd:
            self.lbl_status.setText("  !! Debit and Credit accounts are required !!")
            return
        try:
            amount = float(self.f_amt.text().strip() or 0)
        except ValueError:
            self.lbl_status.setText("  !! Invalid amount !!")
            return
        if amount <= 0:
            self.lbl_status.setText("  !! Amount must be greater than 0 !!")
            return
        entry_date = parse_date(self.f_date.text().strip()) or datetime.date.today()
        vrno = self.f_vrno.text().strip() or next_vrno(self.year, "81")
        base = {
            "DATE": entry_date,
            "VRNO": vrno[:6],
            "NARR": self.f_narr.text().strip().upper()[:90],
            "AMNT": amount,
            "DOCD": "81",
            "SRNO": 1,
        }
        dr_record = {**base, "ACCD": dr_accd[:6], "DRCR": "D", "PYTRCT": "R"}
        cr_record = {**base, "ACCD": cr_accd[:6], "DRCR": "C", "PYTRCT": "P"}
        if self._edit_pair is None:
            ok = write_record("JBK81", self.year, dr_record) and write_record("JBK81", self.year, cr_record)
        else:
            dr_recno, cr_recno = self._edit_pair
            ok = True
            if dr_recno:
                ok = ok and update_record("JBK81", self.year, recno=dr_recno, updates=dr_record)
            else:
                ok = ok and write_record("JBK81", self.year, dr_record)
            if cr_recno:
                ok = ok and update_record("JBK81", self.year, recno=cr_recno, updates=cr_record)
            else:
                ok = ok and write_record("JBK81", self.year, cr_record)
        if not ok:
            self.lbl_status.setText("  !! Save failed !!")
            return
        self._reset_entry_form()
        self.load_data()

    def _edit_entry(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "", "Select a row to edit.")
            return
        pair = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole) if self.table.item(row, 0) else None
        if not pair:
            return
        record = self._records[row]
        dr = record.get("DR") or {}
        cr = record.get("CR") or {}
        dt = record.get("DATE")
        self._edit_pair = pair
        self.f_date.setText(dt.strftime("%d/%m/%y") if dt else datetime.date.today().strftime("%d/%m/%y"))
        self.f_vrno.setText(record.get("VRNO", ""))
        self.f_dr.setText(str(dr.get("ACCD", "")).strip())
        self.f_cr.setText(str(cr.get("ACCD", "")).strip())
        self.f_narr.setText(record.get("NARR", ""))
        self.f_amt.setText(f"{float(record.get('AMNT', 0) or 0):.2f}")

    def _delete_entry(self):
        _, pair = self._get_selected_recno()
        if pair is None: QMessageBox.information(self,"","Select a row to delete."); return
        ans = QMessageBox.question(self,"Confirm Delete","Delete this journal entry?",
                                   QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if ans == QMessageBox.StandardButton.Yes:
            ok = True
            dr_recno, cr_recno = pair
            if dr_recno:
                ok = ok and delete_record("JBK81", self.year, recno=dr_recno)
            if cr_recno:
                ok = ok and delete_record("JBK81", self.year, recno=cr_recno)
            if ok:
                self._reset_entry_form()
                self.load_data()
            else:
                QMessageBox.critical(self,"Error","Delete failed.")

    def _print(self):
        html = _make_html("JOURNAL", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_print(self, html)

    def _pdf(self):
        html = _make_html("JOURNAL", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_pdf(self, "Journal", html)

    def _csv(self):
        do_csv(self, "Journal", self._get_headers(self.table), self._get_rows_for_export(self.table))


# ─────────────────────────────────────────────────────────────────────────────
# SALES MODULE
# ─────────────────────────────────────────────────────────────────────────────
class SalesModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._accounts = get_accounts_dict(year)
        self._edit_recno = None
        self._loading_detail = False
        self._build_ui(); self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,4)
        layout.addWidget(self._title_bar("SALES"))

        browse_group = self._clipper_group("SALES")
        browse_layout = QVBoxLayout(browse_group)
        self.table = self._make_table(["Bill", "Date", "Party", "Sls. Amt", "Add", "Less", "Nett Amt", "Type"])
        self.table.setColumnWidth(0,100); self.table.setColumnWidth(1,90); self.table.setColumnWidth(2,110)
        self.table.setColumnWidth(3,120); self.table.setColumnWidth(4,90); self.table.setColumnWidth(5,90)
        self.table.setColumnWidth(6,130); self.table.setColumnWidth(7,90)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._load_selected_entry)
        browse_layout.addWidget(self.table)
        layout.addWidget(browse_group, 1)

        entry_group = self._clipper_group("EDITING")
        form = QGridLayout(entry_group)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        self.f_billno = QLineEdit()
        self.f_date = QLineEdit(datetime.date.today().strftime("%d/%m/%y"))
        self.f_party = QLineEdit()
        self.f_pname = QLineEdit()
        self.f_pname.setReadOnly(True)
        self.f_vehicle = QLineEdit()
        self.f_salamt = QLineEdit("0.00")
        self.f_totamt = QLineEdit("0.00")
        self.f_credit = QCheckBox("Credit Sale")
        self.f_narr = QLineEdit()
        for widget, width in [
            (self.f_billno, 120), (self.f_date, 120), (self.f_party, 120),
            (self.f_pname, 260), (self.f_vehicle, 140), (self.f_salamt, 120),
            (self.f_totamt, 120)
        ]:
            widget.setMaximumWidth(width)
        form.addWidget(QLabel("Bill No."), 0, 0)
        form.addWidget(self.f_billno, 0, 1)
        form.addWidget(QLabel("Date"), 0, 2)
        form.addWidget(self.f_date, 0, 3)
        form.addWidget(self.f_credit, 0, 4, 1, 2)

        form.addWidget(QLabel("Party A/c"), 1, 0)
        form.addWidget(self.f_party, 1, 1)
        form.addWidget(QLabel("Party Name"), 1, 2)
        form.addWidget(self.f_pname, 1, 3, 1, 3)

        form.addWidget(QLabel("Vehicle"), 2, 0)
        form.addWidget(self.f_vehicle, 2, 1)
        form.addWidget(QLabel("Sales Amt"), 2, 2)
        form.addWidget(self.f_salamt, 2, 3)
        form.addWidget(QLabel("Nett Amt"), 2, 4)
        form.addWidget(self.f_totamt, 2, 5)

        form.addWidget(QLabel("Narration"), 3, 0)
        form.addWidget(self.f_narr, 3, 1, 1, 5)

        btns = QHBoxLayout()
        self.btn_new = self._toolbar_btn("New")
        self.btn_edit = self._toolbar_btn("Edit")
        self.btn_lookup = self._toolbar_btn("Lookup")
        self.btn_save = self._toolbar_btn("Save", cls="primary")
        self.btn_delete = self._toolbar_btn("Delete", cls="danger")
        self.btn_print = self._toolbar_btn("Print")
        self.btn_pdf = self._toolbar_btn("PDF")
        self.btn_csv = self._toolbar_btn("CSV")
        self.btn_clear = self._toolbar_btn("Clear")
        for b in [self.btn_new, self.btn_edit, self.btn_lookup, self.btn_save, self.btn_delete, self.btn_print, self.btn_pdf, self.btn_csv, self.btn_clear]:
            btns.addWidget(b)
        btns.addStretch()
        form.addLayout(btns, 4, 0, 1, 6)
        layout.addWidget(entry_group)
        layout.addWidget(self._footer_bar("F10-Add  F2-Edit  F3-List  F4-Del  1-No.  2-Dt  F5-Copy  F6-Reg.  F7-Qck_Del  F8-updt"))

        self.lbl_status = QLabel(""); self.lbl_status.setStyleSheet("color:#ffffff;font-size:18px;padding:2px;")
        layout.addWidget(self.lbl_status)
        self.f_party.textChanged.connect(self._update_party_name)
        self.btn_new.clicked.connect(self._reset_entry_form)
        self.btn_edit.clicked.connect(self._load_selected_entry)
        self.btn_lookup.clicked.connect(self._lookup_party)
        self.btn_save.clicked.connect(self._save_entry)
        self.btn_delete.clicked.connect(self._delete_entry)
        self.btn_print.clicked.connect(self._print); self.btn_pdf.clicked.connect(self._pdf); self.btn_csv.clicked.connect(self._csv)
        self.btn_clear.clicked.connect(self._reset_entry_form)

    def load_data(self):
        selected_bill = self.f_billno.text().strip()
        selected_recno = self._edit_recno
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False); self.table.setRowCount(0)
        self._records = read_table("SREG41", self.year)
        self._records.sort(key=lambda r: (
            rec_value(r, "RCTDT", "RCTDTOTK", default=datetime.date.min) or datetime.date.min,
            str(rec_value(r, "SBILLNO", "SBILLNOTK", default="")).strip(),
        ))
        shown = 0; total = 0.0
        for r in self._records:
            dt = rec_value(r, "RCTDT", "RCTDTOTK", default=None)
            row = self.table.rowCount(); self.table.insertRow(row)
            accd = str(rec_value(r, "ACCD", "ACCDOTK", default="")).strip()
            tot = float(rec_value(r, "TOTAMT", "TOTAMTTK", default=0) or 0); total += tot
            sales_amt = float(rec_value(r, "SLSAMT", "SLSAMTTK", default=0) or 0)
            vals = [str(rec_value(r, "SBILLNO", "SBILLNOTK", default="")).strip(),
                    dt.strftime("%d/%m/%y") if dt else "",
                    accd,
                    fmt_amount(sales_amt),
                    fmt_amount(0),
                    fmt_amount(0),
                    fmt_amount(tot),
                    "Credit" if rec_value(r, "ISCREDIT", "ISCREDITTK", default=False) else "Cash"]
            for col, val in enumerate(vals):
                sort_key = val
                if col == 1:
                    sort_key = dt or datetime.date.min
                elif col == 3:
                    sort_key = sales_amt
                elif col == 6:
                    sort_key = tot
                item = SortableItem(val, sort_key)
                if col in (3,4,5,6): item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                item.setData(Qt.ItemDataRole.UserRole, r.get("_recno"))
                self.table.setItem(row, col, item)
            shown += 1
        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        self.lbl_status.setText(f"  Bills: {shown}   |   Total Sales: ₹ {fmt_amount(total)}")
        if selected_recno is not None and self._select_record(selected_recno):
            self._load_selected_entry()
        elif selected_bill and self._select_bill(selected_bill):
            self._load_selected_entry()
        elif self.table.rowCount():
            self.table.selectRow(0)
            self._load_selected_entry()
        else:
            self._reset_entry_form()

    def _lookup_party(self):
        dlg = AccountLookupDialog(self.year, self)
        if dlg.exec() and dlg.chosen:
            self.f_party.setText(dlg.chosen)

    def _reset_entry_form(self):
        self._loading_detail = True
        self._edit_recno = None
        self.table.clearSelection()
        self.f_billno.setText(next_numeric_code(self._records, "SBILLNO", "SBILLNOTK", width=6))
        self.f_date.setText(datetime.date.today().strftime("%d/%m/%y"))
        self.f_party.clear()
        self.f_pname.clear()
        self.f_vehicle.clear()
        self.f_salamt.setText("0.00")
        self.f_totamt.setText("0.00")
        self.f_credit.setChecked(False)
        self.f_narr.clear()
        self.lbl_status.setText("  New sales bill ready.")
        self._loading_detail = False
        self.f_party.setFocus()

    def _update_party_name(self, text):
        self.f_pname.setText(self._accounts.get(text.strip().upper(), ""))

    def _select_record(self, recno):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == recno:
                self.table.selectRow(row)
                return True
        return False

    def _select_bill(self, bill_no):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text().strip() == bill_no:
                self.table.selectRow(row)
                return True
        return False

    def _get_selected(self):
        row = self.table.currentRow()
        if row < 0 and self.table.selectedItems():
            row = self.table.row(self.table.selectedItems()[0])
        if row < 0:
            return None, None
        item = self.table.item(row, 0)
        recno = item.data(Qt.ItemDataRole.UserRole) if item else None
        rec = next((r for r in self._records if r.get("_recno") == recno), None)
        return recno, rec

    def _load_selected_entry(self):
        if self._loading_detail:
            return
        recno, rec = self._get_selected()
        if not recno or not rec:
            return
        self._loading_detail = True
        dt = rec_value(rec, "RCTDT", "RCTDTOTK", default=None)
        self._edit_recno = recno
        self.f_billno.setText(str(rec_value(rec, "SBILLNO", "SBILLNOTK", default="")).strip())
        self.f_date.setText(dt.strftime("%d/%m/%y") if dt else datetime.date.today().strftime("%d/%m/%y"))
        self.f_party.setText(str(rec_value(rec, "ACCD", "ACCDOTK", default="")).strip())
        self.f_vehicle.setText(str(rec_value(rec, "VEHICLENO", "VEHICLENOK", default="")).strip())
        self.f_salamt.setText(f"{float(rec_value(rec, 'SLSAMT', 'SLSAMTTK', default=0) or 0):.2f}")
        self.f_totamt.setText(f"{float(rec_value(rec, 'TOTAMT', 'TOTAMTTK', default=0) or 0):.2f}")
        self.f_credit.setChecked(bool(rec_value(rec, "ISCREDIT", "ISCREDITTK", default=False)))
        self.f_narr.setText(str(rec_value(rec, "NOTE", "NOTECEK", "NARRTK", default="")).strip())
        self.lbl_status.setText(
            f"  Editing Bill {self.f_billno.text().strip()}   Party: {self.f_pname.text().strip() or self.f_party.text().strip()}"
        )
        self._loading_detail = False

    def _save_entry(self):
        accd = self.f_party.text().strip().upper()
        if not accd:
            self.lbl_status.setText("  !! Party A/c Code required !!")
            return
        try:
            sales_amt = float(self.f_salamt.text().strip() or 0)
            total_amt = float(self.f_totamt.text().strip() or 0)
        except ValueError:
            self.lbl_status.setText("  !! Invalid sales amount !!")
            return
        if total_amt <= 0:
            self.lbl_status.setText("  !! Nett amount must be greater than 0 !!")
            return
        qd = parse_date(self.f_date.text().strip()) or datetime.date.today()
        rec = {
            "RCTDTOTK": qd,
            "SBILLNOTK": self.f_billno.text().strip()[:10] or next_numeric_code(self._records, "SBILLNO", "SBILLNOTK", width=6),
            "ACCDOTK": accd[:6],
            "VEHICLENOK": self.f_vehicle.text().strip()[:15],
            "SLSAMTTK": sales_amt if sales_amt > 0 else total_amt,
            "TOTAMTTK": total_amt,
            "ISCREDITTK": self.f_credit.isChecked(),
            "NOTECEK": self.f_narr.text().strip()[:78],
        }
        bill_no = rec["SBILLNOTK"]
        ok = update_record("SREG41", self.year, recno=self._edit_recno, updates=rec) if self._edit_recno else write_record("SREG41", self.year, rec)
        if not ok:
            self.lbl_status.setText("  !! Save failed !!")
            return
        saved_recno = self._edit_recno
        self.load_data()
        if saved_recno is not None:
            self._select_record(saved_recno)
            self._load_selected_entry()
        else:
            self._select_bill(bill_no)
            self._load_selected_entry()
        self.lbl_status.setText(f"  Saved Bill {bill_no}")

    def _delete_entry(self):
        recno, rec = self._get_selected()
        if not recno: QMessageBox.information(self,"","Select a row."); return
        if QMessageBox.question(self,"Delete","Delete this sales bill?",
           QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if delete_record("SREG41", self.year, recno=recno):
                self.load_data()
                if self.table.rowCount() == 0:
                    self._reset_entry_form()
            else: QMessageBox.critical(self,"Error","Delete failed.")

    def _print(self):
        html = _make_html("SALES REGISTER", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_print(self, html)
    def _pdf(self):
        html = _make_html("SALES REGISTER", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_pdf(self, "Sales_Register", html)
    def _csv(self):
        do_csv(self, "Sales_Register", self._get_headers(self.table), self._get_rows_for_export(self.table))


# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE MODULE
# ─────────────────────────────────────────────────────────────────────────────
class PurchaseModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._accounts = get_accounts_dict(year)
        self._edit_recno = None
        self._build_ui(); self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,4)
        layout.addWidget(self._title_bar("PURCHASE"))

        browse_group = self._clipper_group("PURCHASE")
        browse_layout = QVBoxLayout(browse_group)
        self.table = self._make_table(["Receipt Date","Bill Date","Bill No","Challan","Supplier Code","Supplier Name","Amount ₹"])
        for w,c in [(90,0),(90,1),(100,2),(100,3),(90,4),(200,5),(120,6)]:
            self.table.setColumnWidth(c,w)
        self.table.doubleClicked.connect(self._edit_entry)
        browse_layout.addWidget(self.table)
        layout.addWidget(browse_group, 1)

        entry_group = self._clipper_group("NEW PURCHASE")
        form = QGridLayout(entry_group)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        self.f_rctdt = QLineEdit(datetime.date.today().strftime("%d/%m/%y"))
        self.f_billdt = QLineEdit(datetime.date.today().strftime("%d/%m/%y"))
        self.f_billno = QLineEdit()
        self.f_chlno = QLineEdit()
        self.f_accd = QLineEdit()
        self.f_amt = QLineEdit("0.00")
        for widget, width in [(self.f_rctdt, 120), (self.f_billdt, 120), (self.f_billno, 120), (self.f_chlno, 120), (self.f_accd, 120), (self.f_amt, 120)]:
            widget.setMaximumWidth(width)
        form.addWidget(QLabel("Rcpt Date"), 0, 0)
        form.addWidget(QLabel("Bill Date"), 0, 1)
        form.addWidget(QLabel("Bill No"), 0, 2)
        form.addWidget(QLabel("Challan"), 0, 3)
        form.addWidget(QLabel("Supplier"), 0, 4)
        form.addWidget(QLabel("Amount"), 0, 5)
        form.addWidget(self.f_rctdt, 1, 0)
        form.addWidget(self.f_billdt, 1, 1)
        form.addWidget(self.f_billno, 1, 2)
        form.addWidget(self.f_chlno, 1, 3)
        form.addWidget(self.f_accd, 1, 4)
        form.addWidget(self.f_amt, 1, 5)

        btns = QHBoxLayout()
        self.btn_lookup = self._toolbar_btn("Lookup")
        self.btn_save = self._toolbar_btn("Save", cls="primary")
        self.btn_del = self._toolbar_btn("Delete", cls="danger")
        self.btn_print = self._toolbar_btn("Print")
        self.btn_pdf = self._toolbar_btn("PDF")
        self.btn_csv = self._toolbar_btn("CSV")
        self.btn_clear = self._toolbar_btn("Clear")
        for b in [self.btn_lookup, self.btn_save, self.btn_del, self.btn_print, self.btn_pdf, self.btn_csv, self.btn_clear]:
            btns.addWidget(b)
        btns.addStretch()
        form.addLayout(btns, 2, 0, 1, 6)
        layout.addWidget(entry_group)
        layout.addWidget(self._footer_bar("F10-Add  F2-Edit  F3-List  F4-Del  1-Search Bill  F5-Print  F6-VAT_Reg."))

        self.lbl_status = QLabel(""); self.lbl_status.setStyleSheet("color:#ffffff;font-size:18px;padding:6px 0;")
        layout.addWidget(self.lbl_status)

        self.btn_lookup.clicked.connect(self._lookup_account)
        self.btn_save.clicked.connect(self._save_inline_entry)
        self.btn_del.clicked.connect(self._delete_entry)
        self.btn_print.clicked.connect(self._print); self.btn_pdf.clicked.connect(self._pdf); self.btn_csv.clicked.connect(self._csv)

    def load_data(self):
        self.table.setSortingEnabled(False); self.table.setRowCount(0)
        self._records = read_table("PREG61", self.year)
        self._records.sort(key=lambda r: (r.get("RCTDT") or datetime.date.min, str(r.get("PBILLNO", "") or "")))
        total = 0.0
        for r in self._records:
            row = self.table.rowCount(); self.table.insertRow(row)
            rdt = r.get("RCTDT"); bdt = r.get("BILLDT")
            accd = str(r.get("ACCD","")).strip()
            amt = float(r.get("PURAMT",0) or 0); total += amt
            vals = [rdt.strftime("%d/%m/%y") if rdt else "",
                    bdt.strftime("%d/%m/%y") if bdt else "",
                    str(r.get("PBILLNO","")).strip(), str(r.get("CHLNO","")).strip(),
                    accd, self._accounts.get(accd,accd)[:28], fmt_amount(amt)]
            for col, val in enumerate(vals):
                sort_key = val
                if col == 0:
                    sort_key = rdt or datetime.date.min
                elif col == 1:
                    sort_key = bdt or datetime.date.min
                elif col == 6:
                    sort_key = amt
                item = SortableItem(val, sort_key)
                if col == 6: item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                item.setData(Qt.ItemDataRole.UserRole, r.get("_recno"))
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.lbl_status.setText(f"  Purchases: {len(self._records)}   Total: {fmt_amount(total)}")
        if self._edit_recno is None:
            self._reset_entry_form()

    def _lookup_account(self):
        dlg = AccountLookupDialog(self.year, self)
        if dlg.exec() and dlg.chosen:
            self.f_accd.setText(dlg.chosen)

    def _reset_entry_form(self):
        self._edit_recno = None
        today = datetime.date.today().strftime("%d/%m/%y")
        self.f_rctdt.setText(today)
        self.f_billdt.setText(today)
        self.f_billno.setText(next_numeric_code(self._records, "PBILLNO", width=6))
        self.f_chlno.clear()
        self.f_accd.clear()
        self.f_amt.setText("0.00")
        self.f_accd.setFocus()

    def _save_inline_entry(self):
        accd = self.f_accd.text().strip().upper()
        if not accd:
            self.lbl_status.setText("  !! Supplier A/c required !!")
            return
        try:
            amount = float(self.f_amt.text().strip() or 0)
        except ValueError:
            self.lbl_status.setText("  !! Invalid amount !!")
            return
        if amount <= 0:
            self.lbl_status.setText("  !! Amount must be greater than 0 !!")
            return
        record = {
            "RCTDT": parse_date(self.f_rctdt.text().strip()) or datetime.date.today(),
            "BILLDT": parse_date(self.f_billdt.text().strip()) or datetime.date.today(),
            "PBILLNO": self.f_billno.text().strip()[:10] or next_numeric_code(self._records, "PBILLNO", width=6),
            "CHLNO": self.f_chlno.text().strip()[:10],
            "ACCD": accd[:6],
            "PURAMT": amount,
            "DOCD": "61",
            "VAT": 0.0,
        }
        ok = update_record("PREG61", self.year, recno=self._edit_recno, updates=record) if self._edit_recno else write_record("PREG61", self.year, record)
        if not ok:
            self.lbl_status.setText("  !! Save failed !!")
            return
        self._reset_entry_form()
        self.load_data()

    def _get_selected(self):
        row = self.table.currentRow()
        if row < 0: return None, None
        item = self.table.item(row,0)
        recno = item.data(Qt.ItemDataRole.UserRole) if item else None
        return recno, next((r for r in self._records if r.get("_recno")==recno), None)

    def _edit_entry(self):
        recno, rec = self._get_selected()
        if not recno: QMessageBox.information(self,"","Select a row."); return
        self._edit_recno = recno
        rctdt = rec.get("RCTDT")
        billdt = rec.get("BILLDT")
        self.f_rctdt.setText(rctdt.strftime("%d/%m/%y") if rctdt else datetime.date.today().strftime("%d/%m/%y"))
        self.f_billdt.setText(billdt.strftime("%d/%m/%y") if billdt else datetime.date.today().strftime("%d/%m/%y"))
        self.f_billno.setText(str(rec.get("PBILLNO", "")).strip())
        self.f_chlno.setText(str(rec.get("CHLNO", "")).strip())
        self.f_accd.setText(str(rec.get("ACCD", "")).strip())
        self.f_amt.setText(f"{float(rec.get('PURAMT', 0) or 0):.2f}")

    def _delete_entry(self):
        recno, _ = self._get_selected()
        if not recno: return
        if QMessageBox.question(self,"Delete","Delete this purchase record?",
           QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if delete_record("PREG61", self.year, recno=recno):
                self._reset_entry_form()
                self.load_data()
            else: QMessageBox.critical(self,"Error","Delete failed.")

    def _print(self):
        html = _make_html("PURCHASE REGISTER", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_print(self, html)
    def _pdf(self):
        html = _make_html("PURCHASE REGISTER", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_pdf(self, "Purchase_Register", html)
    def _csv(self):
        do_csv(self, "Purchase_Register", self._get_headers(self.table), self._get_rows_for_export(self.table))

# ─────────────────────────────────────────────────────────────────────────────
# TRIAL BALANCE MODULE
# ─────────────────────────────────────────────────────────────────────────────
class TrialBalanceModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._build_ui(); self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,4)
        title_row = QHBoxLayout()
        title_row.addWidget(self._title_bar("TRIAL BALANCE")); title_row.addStretch()
        btn_refresh = QPushButton("Refresh"); btn_refresh.clicked.connect(self.load_data)
        title_row.addWidget(btn_refresh)
        layout.addLayout(title_row)

        tb = QHBoxLayout(); tb.setSpacing(6)
        self.btn_print = self._toolbar_btn("Print","","Ctrl+P")
        self.btn_pdf = self._toolbar_btn("PDF","")
        self.btn_csv = self._toolbar_btn("CSV","")
        for b in [self.btn_print,self.btn_pdf,self.btn_csv]: tb.addWidget(b)
        tb.addStretch()
        self.search_box = self._search_box("Filter accounts…")
        tb.addWidget(QLabel("Search")); tb.addWidget(self.search_box)
        layout.addLayout(tb)

        self.table = self._make_table(["Code","Account Name","Group","Opening ₹","Movement ₹","Balance ₹","Dr/Cr"])
        self.table.setColumnWidth(0,80); self.table.setColumnWidth(1,220)
        self.table.setColumnWidth(2,120); self.table.setColumnWidth(3,120)
        self.table.setColumnWidth(4,120); self.table.setColumnWidth(5,120); self.table.setColumnWidth(6,60)
        layout.addWidget(self.table)
        layout.addWidget(self._footer_bar("Alt_N/Alt_P-Print  Alt_E-Export  Esc-Exit"))
        self.lbl_status = QLabel(""); self.lbl_status.setStyleSheet("color:#888;font-size:12px;padding:2px;")
        layout.addWidget(self.lbl_status)

        self.btn_print.clicked.connect(self._print)
        self.btn_pdf.clicked.connect(self._pdf)
        self.btn_csv.clicked.connect(self._csv)
        self.search_box.textChanged.connect(self._apply_search)

    def load_data(self):
        self.table.setSortingEnabled(False); self.table.setRowCount(0)
        # Compute GL totals per account
        gl_totals = {}
        for r in read_table("GL", self.year):
            accd = str(r.get("ACCD","")).strip()
            amt = float(r.get("AMNT",0) or 0)
            drcr = str(r.get("DRCR","D")).strip().upper()
            gl_totals[accd] = gl_totals.get(accd,0.0) + (amt if drcr=="D" else -amt)

        groups = {str(r.get("GRCD","")).strip(): str(r.get("GRHD","")).strip()
                  for r in read_table("GRPMST", self.year)}

        total_dr = 0.0; total_cr = 0.0
        for acc in read_table("ACMST", self.year, order_by="AC_CODE"):
            code = str(acc.get("AC_CODE","")).strip()
            if not code: continue
            yearop = float(acc.get("YEAROP",0) or 0)
            mv = gl_totals.get(code,0.0)
            bal = yearop + mv
            grcd = str(acc.get("AC_GRCD","")).strip()
            drcr_s = "Dr" if bal >= 0 else "Cr"
            if bal >= 0: total_dr += bal
            else: total_cr += abs(bal)

            row = self.table.rowCount(); self.table.insertRow(row)
            vals = [code, str(acc.get("AC_HEAD","")).strip()[:30],
                    groups.get(grcd,grcd)[:15],
                    fmt_amount(yearop), fmt_amount(mv), fmt_amount(abs(bal)), drcr_s]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col in (3,4,5): item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                if col==6:
                    item.setForeground(QColor("#00ff88") if drcr_s=="Dr" else QColor("#ff6644"))
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.lbl_status.setText(f"  Accounts: {self.table.rowCount()}   |   Total Debit: ₹ {fmt_amount(total_dr)}   |   Total Credit: ₹ {fmt_amount(total_cr)}")

    def _apply_search(self, text):
        q = text.lower()
        for row in range(self.table.rowCount()):
            match = any(q in (self.table.item(row,c).text().lower() if self.table.item(row,c) else "")
                        for c in range(self.table.columnCount()))
            self.table.setRowHidden(row, not match if q else False)

    def _print(self):
        html = _make_html("TRIAL BALANCE", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_print(self, html)
    def _pdf(self):
        html = _make_html("TRIAL BALANCE", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_pdf(self, "Trial_Balance", html)
    def _csv(self):
        do_csv(self, "Trial_Balance", self._get_headers(self.table), self._get_rows_for_export(self.table))


# ─────────────────────────────────────────────────────────────────────────────
# ACCOUNT LEDGER MODULE
# ─────────────────────────────────────────────────────────────────────────────
class LedgerModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._accounts = get_accounts_dict(year)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,4)
        layout.addWidget(self._title_bar("ACCOUNT LEDGER"))

        # Account selector
        sel_row = QHBoxLayout(); sel_row.setSpacing(8)
        sel_row.addWidget(QLabel("Account:"))
        self.f_accd = QLineEdit(); self.f_accd.setFixedWidth(100)
        self.f_accd.setPlaceholderText("A/c Code")
        sel_row.addWidget(self.f_accd)
        btn_lookup = QPushButton("Lookup"); btn_lookup.clicked.connect(self._lookup)
        sel_row.addWidget(btn_lookup)
        self.lbl_acname = QLabel(""); self.lbl_acname.setStyleSheet("color:#00c8c8;font-weight:bold;")
        sel_row.addWidget(self.lbl_acname)
        sel_row.addStretch()
        layout.addLayout(sel_row)

        # Date filter
        df = QHBoxLayout(); df.setSpacing(6)
        df.addWidget(QLabel("From:")); self.f_from = self._date_filter(); df.addWidget(self.f_from)
        df.addWidget(QLabel("To:")); self.f_to = QDateEdit(); self.f_to.setDisplayFormat("dd/MM/yy")
        self.f_to.setCalendarPopup(True); self.f_to.setDate(QDate.currentDate()); df.addWidget(self.f_to)
        btn_show = QPushButton("Show Ledger"); btn_show.setProperty("class","primary"); btn_show.clicked.connect(self.load_data)
        df.addWidget(btn_show); df.addStretch()
        self.btn_print = self._toolbar_btn("Print",""); self.btn_pdf = self._toolbar_btn("PDF",""); self.btn_csv = self._toolbar_btn("CSV","")
        df.addWidget(self.btn_print); df.addWidget(self.btn_pdf); df.addWidget(self.btn_csv)
        layout.addLayout(df)

        self.table = self._make_table(["Date","Doc","Voucher","Narration","Debit ₹","Credit ₹","Balance ₹"])
        self.table.setColumnWidth(0,90); self.table.setColumnWidth(1,60); self.table.setColumnWidth(2,90)
        self.table.setColumnWidth(3,230); self.table.setColumnWidth(4,110); self.table.setColumnWidth(5,110); self.table.setColumnWidth(6,120)
        layout.addWidget(self.table)
        layout.addWidget(self._footer_bar("Alt_N/Alt_P-Print  Alt_E-Export  Esc-Exit"))
        self.lbl_status = QLabel(""); self.lbl_status.setStyleSheet("color:#888;font-size:12px;padding:2px;")
        layout.addWidget(self.lbl_status)

        self.btn_print.clicked.connect(self._print); self.btn_pdf.clicked.connect(self._pdf); self.btn_csv.clicked.connect(self._csv)
        self.f_accd.returnPressed.connect(self.load_data)

    def _lookup(self):
        dlg = AccountLookupDialog(self.year, self)
        if dlg.exec() and dlg.chosen:
            self.f_accd.setText(dlg.chosen)
            self.load_data()

    def load_data(self):
        code = self.f_accd.text().strip().upper()
        if not code: QMessageBox.information(self,"","Enter or select an Account Code first."); return
        self.lbl_acname.setText(self._accounts.get(code,"Unknown Account"))
        self.table.setSortingEnabled(False); self.table.setRowCount(0)

        fd = self.f_from.date(); td = self.f_to.date()
        from_dt = datetime.date(fd.year(),fd.month(),fd.day()); to_dt = datetime.date(td.year(),td.month(),td.day())

        # Get opening balance
        opening = 0.0
        for a in read_table("ACMST", self.year):
            if str(a.get("AC_CODE","")).strip() == code:
                opening = float(a.get("YEAROP",0) or 0); break

        records = [r for r in read_table("GL", self.year) if str(r.get("ACCD","")).strip() == code]
        records.sort(key=lambda r: (r.get("DATE") or datetime.date.min, str(r.get("VRNO","") or "")))

        balance = opening
        total_dr = 0.0; total_cr = 0.0
        for r in records:
            dt = r.get("DATE")
            if dt and dt > to_dt: continue
            amt = float(r.get("AMNT",0) or 0)
            drcr = str(r.get("DRCR","D")).strip().upper()
            if drcr == "D": balance += amt; total_dr += amt
            else: balance -= amt; total_cr += amt
            if dt and dt < from_dt: continue  # include in balance but don't show

            row = self.table.rowCount(); self.table.insertRow(row)
            bal_s = fmt_amount(abs(balance)) + (" Dr" if balance>=0 else " Cr")
            vals = [dt.strftime("%d/%m/%y") if dt else "",
                    str(r.get("DOCD","")).strip(), str(r.get("VRNO","")).strip(),
                    str(r.get("NARR","")).strip()[:35],
                    fmt_amount(amt) if drcr=="D" else "",
                    fmt_amount(amt) if drcr=="C" else "", bal_s]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col in (4,5,6): item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)

        self.table.setSortingEnabled(True)
        self.lbl_status.setText(f"  A/c: {code}  |  Opening: ₹{fmt_amount(opening)}  |  Dr: ₹{fmt_amount(total_dr)}  |  Cr: ₹{fmt_amount(total_cr)}  |  Closing: ₹{fmt_amount(abs(balance))} {'Dr' if balance>=0 else 'Cr'}")

    def _print(self):
        html = _make_html(f"LEDGER — {self.f_accd.text().upper()}  {self.lbl_acname.text()}", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_print(self, html)
    def _pdf(self):
        html = _make_html(f"LEDGER — {self.f_accd.text().upper()}", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_pdf(self, f"Ledger_{self.f_accd.text()}", html)
    def _csv(self):
        do_csv(self, f"Ledger_{self.f_accd.text()}", self._get_headers(self.table), self._get_rows_for_export(self.table))


# ─────────────────────────────────────────────────────────────────────────────
# DAY BOOK MODULE
# ─────────────────────────────────────────────────────────────────────────────
class DayBookModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._accounts = get_accounts_dict(year)
        self._build_ui(); self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,4)
        layout.addWidget(self._title_bar("DAY BOOK"))
        df = QHBoxLayout(); df.setSpacing(6)
        df.addWidget(QLabel("From:")); self.f_from = self._date_filter(); df.addWidget(self.f_from)
        df.addWidget(QLabel("To:")); self.f_to = QDateEdit(); self.f_to.setDisplayFormat("dd/MM/yy")
        self.f_to.setCalendarPopup(True); self.f_to.setDate(QDate.currentDate()); df.addWidget(self.f_to)
        btn_f = QPushButton("Show"); btn_f.setProperty("class","primary"); btn_f.clicked.connect(self.load_data)
        df.addWidget(btn_f); df.addStretch()
        self.btn_print = self._toolbar_btn("Print",""); self.btn_pdf = self._toolbar_btn("PDF",""); self.btn_csv = self._toolbar_btn("CSV","")
        for b in [self.btn_print,self.btn_pdf,self.btn_csv]: df.addWidget(b)
        layout.addLayout(df)
        self.table = self._make_table(["Date","Source","Doc","Voucher","A/c Code","Account Name","Narration","Amount ₹","Dr/Cr"])
        self.table.setColumnWidth(0,90); self.table.setColumnWidth(1,60); self.table.setColumnWidth(2,50)
        self.table.setColumnWidth(3,90); self.table.setColumnWidth(4,80); self.table.setColumnWidth(5,160)
        self.table.setColumnWidth(6,180); self.table.setColumnWidth(7,110); self.table.setColumnWidth(8,55)
        layout.addWidget(self.table)
        self.lbl_status = QLabel(""); self.lbl_status.setStyleSheet("color:#888;font-size:12px;padding:2px;")
        layout.addWidget(self.lbl_status)
        self.btn_print.clicked.connect(self._print); self.btn_pdf.clicked.connect(self._pdf); self.btn_csv.clicked.connect(self._csv)

    def load_data(self):
        self.table.setSortingEnabled(False); self.table.setRowCount(0)
        fd = self.f_from.date(); td = self.f_to.date()
        from_dt = datetime.date(fd.year(),fd.month(),fd.day()); to_dt = datetime.date(td.year(),td.month(),td.day())
        all_recs = []
        for src in ["GL","CBK01","CBK02","JBK81"]:
            for r in read_table(src, self.year):
                dt = r.get("DATE")
                if dt and from_dt <= dt <= to_dt:
                    all_recs.append((src, r))
        all_recs.sort(key=lambda x: (x[1].get("DATE") or datetime.date.min, x[1].get("VRNO") or ""))
        total = 0.0
        for src, r in all_recs:
            row = self.table.rowCount(); self.table.insertRow(row)
            dt = r.get("DATE"); accd = str(r.get("ACCD","")).strip()
            amt = float(r.get("AMNT",0) or 0); total += amt
            drcr = str(r.get("DRCR","D")).strip().upper()
            vals = [dt.strftime("%d/%m/%y") if dt else "", src,
                    str(r.get("DOCD","")).strip(), str(r.get("VRNO","")).strip(),
                    accd, self._accounts.get(accd,accd)[:22],
                    str(r.get("NARR","")).strip()[:28],
                    fmt_amount(amt), drcr]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col == 7: item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.lbl_status.setText(f"  Transactions: {len(all_recs)}   |   Period: {from_dt.strftime('%d/%m/%Y')} to {to_dt.strftime('%d/%m/%Y')}   |   Total: ₹ {fmt_amount(total)}")

    def _print(self):
        html = _make_html("DAY BOOK", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_print(self, html)
    def _pdf(self):
        html = _make_html("DAY BOOK", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_pdf(self, "Day_Book", html)
    def _csv(self):
        do_csv(self, "Day_Book", self._get_headers(self.table), self._get_rows_for_export(self.table))


# ─────────────────────────────────────────────────────────────────────────────
# OUTSTANDING BILLS MODULE
# ─────────────────────────────────────────────────────────────────────────────
class OutstandingModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._accounts = get_accounts_dict(year)
        self._build_ui(); self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,4)
        title_row = QHBoxLayout()
        title_row.addWidget(self._title_bar("OUTSTANDING BILLS")); title_row.addStretch()
        layout.addLayout(title_row)
        tb = QHBoxLayout(); tb.setSpacing(6)
        self.btn_print = self._toolbar_btn("Print",""); self.btn_pdf = self._toolbar_btn("PDF",""); self.btn_csv = self._toolbar_btn("CSV","")
        for b in [self.btn_print,self.btn_pdf,self.btn_csv]: tb.addWidget(b)
        tb.addStretch()
        self.search_box = self._search_box("Search party / bill…")
        tb.addWidget(QLabel("Search")); tb.addWidget(self.search_box)
        layout.addLayout(tb)
        self.table = self._make_table(["Doc","Bill No","Bill Date","Party Code","Party Name","Bill Amt ₹","Received ₹","Balance ₹"])
        for w,c in [(55,0),(100,1),(90,2),(80,3),(200,4),(110,5),(110,6),(110,7)]:
            self.table.setColumnWidth(c,w)
        layout.addWidget(self.table)
        layout.addWidget(self._footer_bar("Alt_N/Alt_P-Print  Alt_E-Export  Esc-Exit"))
        self.lbl_status = QLabel(""); self.lbl_status.setStyleSheet("color:#888;font-size:12px;padding:2px;")
        layout.addWidget(self.lbl_status)
        self.btn_print.clicked.connect(self._print); self.btn_pdf.clicked.connect(self._pdf); self.btn_csv.clicked.connect(self._csv)
        self.search_box.textChanged.connect(self._apply_search)

    def load_data(self):
        self.table.setSortingEnabled(False); self.table.setRowCount(0)
        total_bill = 0.0; total_bal = 0.0
        for r in read_table("ALLOC", self.year):
            bill_amt = float(r.get("BILLAMT",0) or 0)
            rcd_amt = float(r.get("RCDAMT",0) or 0)
            bal = bill_amt - rcd_amt
            if abs(bal) < 0.01: continue
            accd = str(r.get("PARTYCD","")).strip()
            dt = r.get("BILLDT")
            total_bill += bill_amt; total_bal += bal
            row = self.table.rowCount(); self.table.insertRow(row)
            vals = [str(r.get("DOCD","")).strip(), str(r.get("BILLNO","")).strip(),
                    dt.strftime("%d/%m/%y") if dt else "", accd,
                    self._accounts.get(accd,accd)[:28],
                    fmt_amount(bill_amt), fmt_amount(rcd_amt), fmt_amount(bal)]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col in (5,6,7):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                    if col==7: item.setForeground(QColor("#ff8844"))
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.lbl_status.setText(f"  Outstanding Bills: {self.table.rowCount()}   |   Total Bill Amt: ₹{fmt_amount(total_bill)}   |   Total Outstanding: ₹{fmt_amount(total_bal)}")

    def _apply_search(self, text):
        q = text.lower()
        for row in range(self.table.rowCount()):
            match = any(q in (self.table.item(row,c).text().lower() if self.table.item(row,c) else "")
                        for c in range(self.table.columnCount()))
            self.table.setRowHidden(row, not match if q else False)

    def _print(self):
        html = _make_html("OUTSTANDING BILLS", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_print(self, html)
    def _pdf(self):
        html = _make_html("OUTSTANDING BILLS", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_pdf(self, "Outstanding_Bills", html)
    def _csv(self):
        do_csv(self, "Outstanding_Bills", self._get_headers(self.table), self._get_rows_for_export(self.table))


# ─────────────────────────────────────────────────────────────────────────────
# ACCOUNT MASTER MODULE
# ─────────────────────────────────────────────────────────────────────────────
class AccountMasterModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._build_ui(); self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,4)
        layout.addWidget(self._title_bar("ACCOUNT MASTER"))
        tb = QHBoxLayout(); tb.setSpacing(6)
        self.btn_add = self._toolbar_btn("New Account","","Ctrl+N","primary")
        self.btn_edit = self._toolbar_btn("Edit","","Ctrl+E")
        self.btn_print = self._toolbar_btn("Print","","Ctrl+P")
        self.btn_pdf = self._toolbar_btn("PDF","")
        self.btn_csv = self._toolbar_btn("CSV","")
        for b in [self.btn_add,self.btn_edit,self.btn_print,self.btn_pdf,self.btn_csv]: tb.addWidget(b)
        tb.addStretch()
        self.search_box = self._search_box("Search code / name…")
        tb.addWidget(QLabel("Search")); tb.addWidget(self.search_box)
        layout.addLayout(tb)

        self.table = self._make_table(["Code","Account Name","Group","City","Opening Bal ₹","Current Bal ₹"])
        self.table.setColumnWidth(0,80); self.table.setColumnWidth(1,250)
        self.table.setColumnWidth(2,130); self.table.setColumnWidth(3,120)
        self.table.setColumnWidth(4,130); self.table.setColumnWidth(5,130)
        self.table.doubleClicked.connect(self._edit)
        layout.addWidget(self.table)
        layout.addWidget(self._footer_bar("F10-Add  F2-Edit  F3-List  F4-Del  1-Name  2-Code"))
        self.lbl_status = QLabel(""); self.lbl_status.setStyleSheet("color:#888;font-size:12px;padding:2px;")
        layout.addWidget(self.lbl_status)

        self.btn_add.clicked.connect(self._add); self.btn_edit.clicked.connect(self._edit)
        self.btn_print.clicked.connect(self._print); self.btn_pdf.clicked.connect(self._pdf); self.btn_csv.clicked.connect(self._csv)
        self.search_box.textChanged.connect(self._apply_search)

    def load_data(self):
        self.table.setSortingEnabled(False); self.table.setRowCount(0)
        groups = {str(r.get("GRCD","")).strip(): str(r.get("GRHD","")).strip()
                  for r in read_table("GRPMST", self.year)}
        self._records = read_table("ACMST", self.year, order_by="AC_CODE")
        for r in self._records:
            code = str(r.get("AC_CODE","")).strip()
            if not code: continue
            grcd = str(r.get("AC_GRCD","")).strip()
            row = self.table.rowCount(); self.table.insertRow(row)
            vals = [code, str(r.get("AC_HEAD","")).strip()[:35],
                    groups.get(grcd,grcd)[:18], str(r.get("CITY","")).strip()[:15],
                    fmt_amount(r.get("YEAROP",0)), fmt_amount(r.get("CURBAL",0))]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col in (4,5): item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                item.setData(Qt.ItemDataRole.UserRole, r.get("_recno"))
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.lbl_status.setText(f"  Accounts: {self.table.rowCount()}")

    def _apply_search(self, text):
        q = text.lower()
        for row in range(self.table.rowCount()):
            match = any(q in (self.table.item(row,c).text().lower() if self.table.item(row,c) else "")
                        for c in range(self.table.columnCount()))
            self.table.setRowHidden(row, not match if q else False)

    def _add(self):
        dlg = AccountEditDialog(self.year, parent=self)
        if dlg.exec():
            ok = write_record("ACMST", self.year, dlg.get_record())
            if ok: self.load_data(); QMessageBox.information(self,"Saved","Account created.")
            else: QMessageBox.critical(self,"Error","Save failed.")

    def _edit(self):
        row = self.table.currentRow()
        if row < 0: QMessageBox.information(self,"","Select an account."); return
        item = self.table.item(row,0); recno = item.data(Qt.ItemDataRole.UserRole) if item else None
        rec = next((r for r in self._records if r.get("_recno")==recno), None)
        if not rec: return
        dlg = AccountEditDialog(self.year, rec=rec, parent=self)
        if dlg.exec():
            ok = update_record("ACMST", self.year, recno=recno, updates=dlg.get_record())
            if ok: self.load_data()
            else: QMessageBox.critical(self,"Error","Update failed.")

    def _print(self):
        html = _make_html("ACCOUNT MASTER", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_print(self, html)
    def _pdf(self):
        html = _make_html("ACCOUNT MASTER", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_pdf(self, "Account_Master", html)
    def _csv(self):
        do_csv(self, "Account_Master", self._get_headers(self.table), self._get_rows_for_export(self.table))


# ─────────────────────────────────────────────────────────────────────────────
# ITEM MASTER MODULE
# ─────────────────────────────────────────────────────────────────────────────
class ItemMasterModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._build_ui(); self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,4)
        layout.addWidget(self._title_bar("ITEM MASTER"))
        tb = QHBoxLayout(); tb.setSpacing(6)
        self.btn_print = self._toolbar_btn("Print",""); self.btn_pdf = self._toolbar_btn("PDF",""); self.btn_csv = self._toolbar_btn("CSV","")
        for b in [self.btn_print,self.btn_pdf,self.btn_csv]: tb.addWidget(b)
        tb.addStretch()
        self.search_box = self._search_box("Search item…"); tb.addWidget(QLabel("Search")); tb.addWidget(self.search_box)
        layout.addLayout(tb)
        self.table = self._make_table(["Code","Item Description","Unit","Op.Stock","Cur.Stock","Sale Rate ₹","Pur.Rate ₹"])
        self.table.setColumnWidth(0,80); self.table.setColumnWidth(1,280); self.table.setColumnWidth(2,60)
        for c in (3,4,5,6): self.table.setColumnWidth(c,110)
        layout.addWidget(self.table)
        layout.addWidget(self._footer_bar("F10-Add  F2-Edit  F3-List  F4-Del  1-Description  2-Code"))
        self.lbl_status = QLabel(""); self.lbl_status.setStyleSheet("color:#888;font-size:12px;padding:2px;")
        layout.addWidget(self.lbl_status)
        self.btn_print.clicked.connect(self._print); self.btn_pdf.clicked.connect(self._pdf); self.btn_csv.clicked.connect(self._csv)
        self.search_box.textChanged.connect(self._apply_search)

    def load_data(self):
        self.table.setSortingEnabled(False); self.table.setRowCount(0)
        self._records = read_table("ITMST", self.year, order_by="ITCD")
        for r in self._records:
            row = self.table.rowCount(); self.table.insertRow(row)
            vals = [str(r.get("ITCD","")).strip(), str(r.get("ITDESC","")).strip()[:35],
                    str(r.get("UNIT","")).strip(),
                    f"{float(r.get('OPSTK',0) or 0):.3f}",
                    f"{float(r.get('CURQTY',0) or 0):.3f}",
                    fmt_amount(r.get("SALRATE",0)), fmt_amount(r.get("PURRATE",0))]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col in (3,4,5,6): item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.lbl_status.setText(f"  Items: {len(self._records)}")

    def _apply_search(self, text):
        q = text.lower()
        for row in range(self.table.rowCount()):
            match = any(q in (self.table.item(row,c).text().lower() if self.table.item(row,c) else "")
                        for c in range(self.table.columnCount()))
            self.table.setRowHidden(row, not match if q else False)

    def _print(self):
        html = _make_html("ITEM MASTER", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_print(self, html)
    def _pdf(self):
        html = _make_html("ITEM MASTER", self.company, self._get_headers(self.table), self._get_rows_for_export(self.table))
        do_pdf(self, "Item_Master", html)
    def _csv(self):
        do_csv(self, "Item_Master", self._get_headers(self.table), self._get_rows_for_export(self.table))


class AgentMasterModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.addWidget(self._title_bar("AGENT MASTER"))
        self.table = self._make_table(["Code", "Name", "Account", "Phone"])
        self.table.setColumnWidth(0, 90)
        self.table.setColumnWidth(1, 260)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 160)
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        for rec in read_table("AGMST", self.year, order_by="AGCD"):
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                str(rec.get("AGCD", "")).strip(),
                str(rec.get("AGNM", "")).strip()[:30],
                str(rec.get("ACCD", "")).strip(),
                str(rec.get("PHONE", "")).strip(),
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, SortableItem(value))


class AddressBookModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.addWidget(self._title_bar("ADDRESS BOOK"))
        self.table = self._make_table(["#", "Name", "Place", "Mobile", "Phone(O)", "Category"])
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 120)
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        for rec in read_table("ADDRES", self.year, order_by="NAME"):
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                str(rec.get("SLNO", "")).strip(),
                str(rec.get("NAME", "")).strip()[:28],
                str(rec.get("PLACE", "")).strip()[:20],
                str(rec.get("MOBILE", "")).strip(),
                str(rec.get("PHONEO", "")).strip(),
                str(rec.get("CATEGORY", "")).strip(),
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, SortableItem(value))


class StockRegisterModule(ModuleBase):
    def __init__(self, year, company, parent=None):
        super().__init__(year, company, parent)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.addWidget(self._title_bar("STOCK REGISTER"))
        self.table = self._make_table(["Code", "Item Name", "Unit", "Op.Stock", "Cur.Stock", "Sale Rate"])
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        for rec in read_table("ITMST", self.year, order_by="ITCD"):
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                (str(rec.get("ITCD", "")).strip(), str(rec.get("ITCD", "")).strip()),
                (str(rec.get("ITDESC", "")).strip()[:30], str(rec.get("ITDESC", "")).strip()),
                (str(rec.get("UNIT", "")).strip(), str(rec.get("UNIT", "")).strip()),
                (f"{float(rec.get('OPSTK', 0) or 0):.3f}", float(rec.get('OPSTK', 0) or 0)),
                (f"{float(rec.get('CURQTY', 0) or 0):.3f}", float(rec.get('CURQTY', 0) or 0)),
                (fmt_amount(rec.get("SALRATE", 0)), float(rec.get("SALRATE", 0) or 0)),
            ]
            for col, (text, sort_key) in enumerate(values):
                item = SortableItem(text, sort_key)
                if col >= 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)


class DebtorCreditorModule(ModuleBase):
    def __init__(self, year, company, mode="debtors", parent=None):
        super().__init__(year, company, parent)
        self.mode = mode
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        title = "DEBTORS" if self.mode == "debtors" else "CREDITORS"
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.addWidget(self._title_bar(title))
        self.table = self._make_table(["Code", "Account Name", "City", "Balance"])
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        grp_prefix = "1" if self.mode == "debtors" else "2"
        for rec in read_table("ACMST", self.year, order_by="AC_CODE"):
            grcd = str(rec.get("AC_GRCD", "")).strip()
            if not grcd.startswith(grp_prefix):
                continue
            bal = float(rec.get("CURBAL", 0) or 0)
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                (str(rec.get("AC_CODE", "")).strip(), str(rec.get("AC_CODE", "")).strip()),
                (str(rec.get("AC_HEAD", "")).strip()[:30], str(rec.get("AC_HEAD", "")).strip()),
                (str(rec.get("CITY", "")).strip()[:15], str(rec.get("CITY", "")).strip()),
                (fmt_amount(abs(bal)), abs(bal)),
            ]
            for col, (text, sort_key) in enumerate(values):
                item = SortableItem(text, sort_key)
                if col == 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)

# ─────────────────────────────────────────────────────────────────────────────
# YEAR SELECT DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class YearSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chosen_year = None; self.chosen_company = ""
        self.setWindowTitle("GEORGIN - Select Company / Year")
        self.setStyleSheet(APP_STYLE)
        self.setMinimumSize(1200, 820)
        self.resize(1360, 900)
        self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        layout = QVBoxLayout(self); layout.setSpacing(12)

        # Logo / header
        logo = QLabel("GEORGIN ACCOUNTING SYSTEM")
        logo.setStyleSheet("font-size:20px;font-weight:bold;color:#00c8ff;padding:12px 0 4px 0;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        sub = QLabel("Select the Company / Financial Year to open")
        sub.setStyleSheet("color:#888;"); sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Data folder:"))
        self.lbl_folder = QLabel("")
        self.lbl_folder.setStyleSheet("color:#00c8c8;")
        self.lbl_folder.setWordWrap(True)
        folder_row.addWidget(self.lbl_folder, 1)
        btn_folder = QPushButton("Change Folder")
        btn_folder.clicked.connect(self._pick_folder)
        folder_row.addWidget(btn_folder)
        layout.addLayout(folder_row)

        # Years table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Code","Company / Year","Period"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 320)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._select)

        layout.addWidget(self.table)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Open Selected Year"); btn_ok.setProperty("class","primary")
        btn_ok.setMinimumHeight(36); btn_ok.clicked.connect(self._select)
        btn_quit = QPushButton("Quit"); btn_quit.clicked.connect(self.reject)
        btns.addWidget(btn_ok); btns.addWidget(btn_quit)
        layout.addLayout(btns)
        self._reload_years()

    def _reload_years(self):
        self.lbl_folder.setText(dbf_layer.DATA_DIR)
        self.table.setRowCount(0)
        brmst = read_table("BRMST")
        brmst.sort(key=lambda r: (r.get("YERCLDT") or datetime.date.min, r.get("YEROPDT") or datetime.date.min))
        for r in brmst:
            code = str(r.get("BRCOD","")).strip()
            if not code: continue
            name = str(r.get("BRNAME","")).strip()
            opdt = r.get("YEROPDT"); cldt = r.get("YERCLDT")
            period = f"{opdt.strftime('%d/%m/%Y')} — {cldt.strftime('%d/%m/%Y')}" if opdt and cldt else ""
            row = self.table.rowCount(); self.table.insertRow(row)
            for col, val in enumerate([code, name, period]):
                self.table.setItem(row, col, QTableWidgetItem(val))
        if self.table.rowCount():
            self.table.selectRow(0)

    def _pick_folder(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select GEORGIN Data Folder", dbf_layer.DATA_DIR)
        if not chosen:
            return
        detected = find_data_dir(chosen)
        if not detected:
            QMessageBox.warning(
                self,
                "Folder Not Detected",
                "No GEORGIN DBF folder was found inside the selected folder."
            )
            return
        set_data_dir(detected)
        settings = _load_settings()
        settings["data_dir"] = detected
        _save_settings(settings)
        self._reload_years()

    def _select(self):
        row = self.table.currentRow()
        if row < 0: return
        self.chosen_year = self.table.item(row,0).text()
        name = self.table.item(row,1).text()
        period = self.table.item(row,2).text()
        yr = period.split("—")[0].strip()[-4:] + "-" + period.split("—")[-1].strip()[-4:] if "—" in period else ""
        self.chosen_company = f"{name}  {yr}"
        self.accept()


class DosMenuPage(QWidget):
    def __init__(self, year, company, handlers, parent=None):
        super().__init__(parent)
        self.year = year
        self.company = company
        self.handlers = handlers
        self.section_order = ["Entries", "Reports", "Utilities", "Files", "Help", "Quit"]
        self.section_items = {
            "Entries": [
                ("Cash Book", handlers["cash"]),
                ("Bank Book", handlers["bank"]),
                ("Purchase", handlers["purchase"]),
                ("Sales", handlers["sales"]),
                ("Journals", handlers["journal"]),
                ("Stock Receipt", handlers["stock_receipt"]),
                ("Stock Issue", handlers["stock_issue"]),
                ("Glass Stock", handlers["glass_stock"]),
            ],
            "Reports": [
                ("Ledger", handlers["ledger"]),
                ("Group Ledger", handlers["group_ledger"]),
                ("Outstanding(Ledger)", handlers["outstanding"]),
                ("Trial Balance", handlers["trial_balance"]),
                ("Stock Register", handlers["stock_register"]),
                ("Stock Summary", handlers["stock_summary"]),
                ("Itemwise Purchase", handlers["itemwise_purchase"]),
                ("Itemwise Sales", handlers["itemwise_sales"]),
                ("Cash & Bank Balance", handlers["cash_bank_balance"]),
                ("Daily Summary", handlers["daybook"]),
            ],
            "Utilities": [
                ("Change Year", handlers["change_year"]),
                ("Change Data Folder", handlers["change_data_folder"]),
                ("Backup", handlers["backup"]),
                ("Restore", handlers["restore"]),
            ],
            "Files": [
                ("A/c   Master", handlers["acmst"]),
                ("Group Master", handlers["group_mst"]),
                ("Agent Master", handlers["agent_mst"]),
                ("Item  Master", handlers["itmst"]),
                ("I.Grp Master", handlers["item_group_mst"]),
                ("Tax   Master", handlers["tax_mst"]),
            ],
            "Help": [
                ("About", handlers["about"]),
            ],
            "Quit": [
                ("Exit", handlers["quit"]),
            ],
        }
        self.nav_buttons = {}
        self.current_section = "Entries"
        self.current_item_label = "Cash Book"
        self._build_ui()
        self.set_company_year(company, year)
        self._show_section(self.current_section)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = QWidget()
        nav.setStyleSheet("border-top:2px solid #d0d0d0; border-bottom:2px solid #d0d0d0;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(12, 10, 12, 10)
        nav_layout.setSpacing(0)
        for section in self.section_order:
            button = QPushButton(section)
            button.setFlat(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _, s=section: self._show_section(s))
            button.setStyleSheet("border:none; padding:0 22px; font-size:20px; color:#e6e6e6;")
            self.nav_buttons[section] = button
            nav_layout.addWidget(button)
            if section != self.section_order[-1]:
                line = QLabel("────")
                line.setStyleSheet("color:#d0d0d0; font-size:18px;")
                nav_layout.addWidget(line)
        nav_layout.addStretch()
        layout.addWidget(nav)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(24, 22, 24, 8)
        body_layout.setSpacing(30)

        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(320)
        self.menu_list.itemActivated.connect(self._activate_item)
        self.menu_list.currentItemChanged.connect(self._update_preview)
        body_layout.addWidget(self.menu_list, alignment=Qt.AlignmentFlag.AlignTop)

        self.preview = LegacyPreviewWidget()
        body_layout.addWidget(self.preview, 1)
        layout.addWidget(body, 1)

    def _show_section(self, section):
        self.current_section = section
        for name, button in self.nav_buttons.items():
            if name == section:
                button.setStyleSheet("border:none; padding:0 22px; font-size:20px; color:#ffffff; background:#800000;")
            else:
                button.setStyleSheet("border:none; padding:0 22px; font-size:20px; color:#e6e6e6; background:transparent;")

        self.menu_list.clear()
        for label, handler in self.section_items[section]:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, handler)
            self.menu_list.addItem(item)
        if self.menu_list.count():
            self.menu_list.setCurrentRow(0)
            self.current_item_label = self.menu_list.item(0).text()
        self.preview.set_preview(self.current_section, self.current_item_label)

    def _activate_item(self, item):
        handler = item.data(Qt.ItemDataRole.UserRole)
        if callable(handler):
            try:
                handler()
            except Exception as exc:
                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Open Failed",
                    f"Unable to open '{item.text()}'.\n\n{exc}",
                )

    def _update_preview(self, current, previous):
        if current:
            self.current_item_label = current.text()
            self.preview.set_preview(self.current_section, self.current_item_label)

    def set_company_year(self, company, year):
        self.company = company
        self.year = year


# ─────────────────────────────────────────────────────────────────────────────
# HEADER BAR WIDGET
# ─────────────────────────────────────────────────────────────────────────────
class HeaderBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(112)
        self.setStyleSheet("background:#000000;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 8)
        self.frame = QFrame()
        self.frame.setStyleSheet("border:2px solid #d0d0d0; background:#000000;")
        frame_layout = QHBoxLayout(self.frame)
        frame_layout.setContentsMargins(26, 16, 26, 16)
        self.lbl_date = QLabel(); self.lbl_date.setStyleSheet("color:#f0f0f0;font-size:22px;")
        self.lbl_company = QLabel(); self.lbl_company.setStyleSheet("color:#ffffff;font-size:24px;font-weight:bold;")
        self.lbl_company.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time = QLabel(); self.lbl_time.setStyleSheet("color:#f0f0f0;font-size:22px;")
        frame_layout.addWidget(self.lbl_date)
        frame_layout.addStretch()
        frame_layout.addWidget(self.lbl_company)
        frame_layout.addStretch()
        frame_layout.addWidget(self.lbl_time)
        layout.addWidget(self.frame)
        timer = QTimer(self); timer.timeout.connect(self._update); timer.start(1000)
        self._update()

    def _update(self):
        now = datetime.datetime.now()
        self.lbl_date.setText(now.strftime("%B %d, %Y"))
        self.lbl_time.setText(now.strftime("%H:%M:%S"))

    def set_company(self, text):
        self.lbl_company.setText(text)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self, year, company):
        super().__init__()
        self.year = year; self.company = company
        self._history = []
        self._dynamic_pages = set()
        self.setWindowTitle(f"GEORGIN Accounting - {company}")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 860)
        self.setStyleSheet(APP_STYLE)
        self.menuBar().hide()
        self._build_ui()
        self._set_current_page(self.menu_page, add_history=False, title="Menu")

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        main_layout = QVBoxLayout(central); main_layout.setSpacing(0); main_layout.setContentsMargins(0,0,0,0)

        self.header = HeaderBar()
        self.header.set_company(self.company)
        main_layout.addWidget(self.header)

        nav_bar = QWidget()
        nav_bar.setStyleSheet("background:#000000;border-bottom:2px solid #d0d0d0;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(12, 6, 12, 6)
        self.btn_back = QPushButton("Esc-Back")
        self.btn_back.clicked.connect(self._go_back)
        self.btn_back.setVisible(False)
        nav_layout.addWidget(self.btn_back)
        self.lbl_page = QLabel("Home")
        self.lbl_page.setStyleSheet("font-size:14px;font-weight:bold;color:#c8c8c8;")
        nav_layout.addWidget(self.lbl_page)
        nav_layout.addStretch()
        main_layout.addWidget(nav_bar)

        # Content stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        self.menu_page = DosMenuPage(
            self.year,
            self.company,
            {
                "cash": self._open_cash_book,
                "bank": self._open_bank_book,
                "sales": self._open_sales,
                "purchase": self._open_purchase,
                "journal": self._open_journal,
                "stock_receipt": self._open_stock_receipt,
                "stock_issue": self._open_stock_issue,
                "glass_stock": self._open_glass_stock,
                "daybook": self._open_daybook,
                "ledger": self._open_ledger,
                "group_ledger": self._open_group_ledger,
                "trial_balance": self._open_trial_balance,
                "outstanding": self._open_outstanding,
                "stock_register": self._open_stock_register,
                "stock_summary": self._open_stock_summary,
                "itemwise_purchase": self._open_itemwise_purchase,
                "itemwise_sales": self._open_itemwise_sales,
                "cash_bank_balance": self._open_cash_bank_balance,
                "debtors": self._open_debtors,
                "creditors": self._open_creditors,
                "db_tables": self._open_db_tables,
                "acmst": self._open_acmst,
                "group_mst": self._open_group_master,
                "itmst": self._open_itmst,
                "item_group_mst": self._open_item_group_master,
                "tax_mst": self._open_tax_master,
                "agent_mst": self._open_agent_master,
                "address_book": self._open_address_book,
                "change_year": self._change_year,
                "change_data_folder": self._change_data_folder,
                "workflow_pdf": self._export_workflow_pdf,
                "backup": self._backup_data,
                "restore": self._restore_data,
                "about": self._about,
                "quit": self.close,
            },
        )
        self.menu_page.page_title = "Menu"
        self.stack.addWidget(self.menu_page)

        # Status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().setStyleSheet("background:#000000;color:#ffffff;font-size:12px;border-top:2px solid #d0d0d0;")
        self._set_status("Ready")
        self.footer = LegacyFooter(APP_FOOTER_TEXT)
        main_layout.addWidget(self.footer)

    def _set_status(self, message):
        self.statusBar().showMessage(f"  Year: {self.year}   |   Data: {dbf_layer.DATA_DIR}   |   {message}")

    def _set_current_page(self, widget, add_history=True, title=None):
        current = self.stack.currentWidget()
        if add_history and current and current is not widget:
            self._history.append(current)
        self.stack.setCurrentWidget(widget)
        if title is None:
            title = getattr(widget, "page_title", "Home")
        self.lbl_page.setText(title)
        self.btn_back.setVisible(bool(self._history))

    def _push_module(self, widget, title, status_message):
        self.stack.addWidget(widget)
        self._dynamic_pages.add(widget)
        widget.page_title = title
        self._set_current_page(widget)
        self._set_status(status_message)

    def _clear_dynamic_pages(self):
        for widget in list(self._dynamic_pages):
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self._dynamic_pages.clear()

    def _go_back(self):
        if not self._history:
            return
        current = self.stack.currentWidget()
        target = self._history.pop()
        self.stack.setCurrentWidget(target)
        self.lbl_page.setText(getattr(target, "page_title", "Home"))
        self.btn_back.setVisible(bool(self._history))
        if current in self._dynamic_pages:
            self._dynamic_pages.remove(current)
            self.stack.removeWidget(current)
            current.deleteLater()
        self._set_status(self.lbl_page.text())

    # ── Module openers ──
    def _open_cash_book(self):
        books = get_cash_book_choices(self.year)
        if not books: QMessageBox.information(self,"","No cash books configured."); return
        preferred = next((book for book in books if book[1].strip().upper() == "CASH BOOK"), None)
        d,n,s,a = preferred or books[0]
        self._push_module(CashBankBookModule(self.year, self.company, d, n, a), n, n)

    def _open_bank_book(self):
        books = get_bank_book_choices(self.year)
        if not books: QMessageBox.information(self,"","No bank books configured."); return
        if len(books) == 1:
            d,n,s,a = books[0]
        else:
            dlg = BookSelectDialog(books, "Select Bank Book", self)
            if not dlg.exec(): return
            d,n,s,a = dlg.chosen
        self._push_module(CashBankBookModule(self.year, self.company, d, n, a), n, n)

    def _open_sales(self):
        self._push_module(SalesModule(self.year, self.company), "Sales Register", "Sales Register")

    def _open_purchase(self):
        self._push_module(PurchaseModule(self.year, self.company), "Purchase Register", "Purchase Register")

    def _open_journal(self):
        self._push_module(JournalModule(self.year, self.company), "Journal", "Journal")

    def _open_stock_receipt(self):
        self._push_module(GenericTableModule(self.year, self.company, "SRCT"), "Stock Receipt", "Stock Receipt")

    def _open_stock_issue(self):
        self._push_module(GenericTableModule(self.year, self.company, "SISU"), "Stock Issue", "Stock Issue")

    def _open_glass_stock(self):
        self._push_module(GenericTableModule(self.year, self.company, "GLASS"), "Glass Stock", "Glass Stock")

    def _open_daybook(self):
        self._push_module(DayBookModule(self.year, self.company), "Day Book", "Day Book")

    def _open_ledger(self):
        self._push_module(LedgerModule(self.year, self.company), "Account Ledger", "Account Ledger")

    def _open_group_ledger(self):
        self._open_first_available_generic(["GL", "ACMST"], "Group Ledger", "Group Ledger")

    def _open_trial_balance(self):
        self._push_module(TrialBalanceModule(self.year, self.company), "Trial Balance", "Trial Balance")

    def _open_outstanding(self):
        self._push_module(OutstandingModule(self.year, self.company), "Outstanding Bills", "Outstanding Bills")

    def _open_stock_register(self):
        self._push_module(StockRegisterModule(self.year, self.company), "Stock Register", "Stock Register")

    def _open_stock_summary(self):
        self._push_module(StockRegisterModule(self.year, self.company), "Stock Summary", "Stock Summary")

    def _open_itemwise_purchase(self):
        self._open_first_available_generic(["PREG61", "ITMST"], "Itemwise Purchase", "Itemwise Purchase")

    def _open_itemwise_sales(self):
        self._open_first_available_generic(["SREG41", "ITMST"], "Itemwise Sales", "Itemwise Sales")

    def _open_cash_bank_balance(self):
        self._open_first_available_generic(["ACMST", "GL"], "Cash & Bank Balance", "Cash & Bank Balance")

    def _open_debtors(self):
        self._push_module(DebtorCreditorModule(self.year, self.company, mode="debtors"), "Debtors", "Debtors")

    def _open_creditors(self):
        self._push_module(DebtorCreditorModule(self.year, self.company, mode="creditors"), "Creditors", "Creditors")

    def _open_db_tables(self):
        self._push_module(
            TableCatalogModule(self.year, self.company, self._open_generic_table),
            "Database Tables",
            "Database Tables"
        )

    def _open_generic_table(self, table_name):
        self._push_module(
            GenericTableModule(self.year, self.company, table_name),
            f"Table {table_name}",
            f"Table {table_name}"
        )

    def _open_acmst(self):
        self._push_module(AccountMasterModule(self.year, self.company), "Account Master", "Account Master")

    def _open_group_master(self):
        self._open_first_available_generic(["GRPMST"], "Group Master", "Group Master")

    def _open_itmst(self):
        self._push_module(ItemMasterModule(self.year, self.company), "Item Master", "Item Master")

    def _open_item_group_master(self):
        self._open_first_available_generic(["ITGRP", "ITMST"], "Item Group Master", "Item Group Master")

    def _open_tax_master(self):
        self._open_first_available_generic(["TAXMST", "TAX", "ACMST"], "Tax Master", "Tax Master")

    def _open_agent_master(self):
        self._push_module(AgentMasterModule(self.year, self.company), "Agent Master", "Agent Master")

    def _open_address_book(self):
        self._push_module(AddressBookModule(self.year, self.company), "Address Book", "Address Book")

    def _open_first_available_generic(self, candidates, title, status_message):
        available = set(list_table_bases(self.year))
        for table_name in candidates:
            if table_name in available:
                self._push_module(
                    GenericTableModule(self.year, self.company, table_name),
                    title,
                    status_message,
                )
                return
        QMessageBox.information(self, "", f"No linked database table found for {title}.")

    def _change_year(self):
        dlg = YearSelectDialog(self)
        if dlg.exec():
            self.year = dlg.chosen_year
            self.company = dlg.chosen_company
            self.header.set_company(self.company)
            self.menu_page.set_company_year(self.company, self.year)
            self.setWindowTitle(f"GEORGIN Accounting - {self.company}")
            self._clear_dynamic_pages()
            self._history.clear()
            self._set_current_page(self.menu_page, add_history=False, title="Menu")
            self._set_status(f"Year changed to {self.year}")

    def _change_data_folder(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select GEORGIN Data Folder", dbf_layer.DATA_DIR)
        if not chosen:
            return
        detected = find_data_dir(chosen)
        if not detected:
            QMessageBox.warning(self, "Folder Not Detected", "No GEORGIN DBF folder was found inside the selected folder.")
            return
        set_data_dir(detected)
        settings = _load_settings()
        settings["data_dir"] = detected
        _save_settings(settings)
        dlg = YearSelectDialog(self)
        if dlg.exec():
            self.year = dlg.chosen_year
            self.company = dlg.chosen_company
            self.header.set_company(self.company)
            self.menu_page.set_company_year(self.company, self.year)
            self.setWindowTitle(f"GEORGIN Accounting - {self.company}")
            self._clear_dynamic_pages()
            self._history.clear()
            self._set_current_page(self.menu_page, add_history=False, title="Menu")
            self._set_status("Data folder changed")

    def _backup_data(self):
        target, _ = QFileDialog.getSaveFileName(self, "Backup GEORGIN Data", f"georgin_backup_{self.year}.zip", "ZIP (*.zip)")
        if not target:
            return
        root, ext = os.path.splitext(target)
        archive_base = root if ext.lower() == ".zip" else target
        archive = shutil.make_archive(archive_base, "zip", dbf_layer.DATA_DIR)
        QMessageBox.information(self, "Backup Complete", f"Backup created:\n{archive}")

    def _restore_data(self):
        archive, _ = QFileDialog.getOpenFileName(self, "Restore GEORGIN Data", "", "ZIP (*.zip)")
        if not archive:
            return
        target_dir = QFileDialog.getExistingDirectory(self, "Select Restore Destination", dbf_layer.DATA_DIR)
        if not target_dir:
            return
        shutil.unpack_archive(archive, target_dir)
        QMessageBox.information(self, "Restore Complete", f"Data restored to:\n{target_dir}")

    def _about(self):
        QMessageBox.about(self, "About GEORGIN",
            "<b>GEORGIN Accounting System</b><br>Mac Desktop Edition<br><br>"
            f"Version: {APP_VERSION}<br><br>"
            "Built with Python + PyQt6<br>"
            "Data: CA-Clipper DBF format<br><br>"
            f"Data directory:<br>{dbf_layer.DATA_DIR}")

    def _export_workflow_pdf(self):
        export_workflow_pdf(self, self.company)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# DATA PATH SETUP DIALOG (for standalone .app usage)
# ─────────────────────────────────────────────────────────────────────────────
import json as _json

_SETTINGS_FILE = os.path.expanduser("~/.georgin_settings.json")

def _load_settings():
    try:
        if os.path.exists(_SETTINGS_FILE):
            with open(_SETTINGS_FILE) as f:
                return _json.load(f)
    except: pass
    return {}

def _save_settings(s):
    try:
        with open(_SETTINGS_FILE, "w") as f:
            _json.dump(s, f, indent=2)
    except: pass

def _ensure_data_path(app):
    """If GEORGIN_DATA not set and saved path not found, ask user to choose."""
    if find_data_dir(dbf_layer.DATA_DIR):
        detected = find_data_dir(dbf_layer.DATA_DIR)
        if detected:
            set_data_dir(detected)
        return True
    # Try saved path
    s = _load_settings()
    saved = s.get("data_dir", "")
    detected = find_data_dir(saved) if saved else None
    if detected:
        set_data_dir(detected)
        return True
    # Ask user
    while True:
        QMessageBox.information(None, "GEORGIN - Data Folder",
            "Please select the GEORGIN data folder (the folder containing your .DBF files).")
        chosen = QFileDialog.getExistingDirectory(None, "Select GEORGIN Data Folder",
                                                   os.path.expanduser("~"))
        if not chosen:
            return False
        detected = find_data_dir(chosen)
        if detected:
            set_data_dir(detected)
            s["data_dir"] = detected
            _save_settings(s)
            return True
        else:
            QMessageBox.warning(None, "Wrong Folder",
                "This folder does not contain GEORGIN DBF files.\n"
                "Select the data folder or a parent folder that contains it.")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GEORGIN Accounting")
    app.setOrganizationName("GEORGIN")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    # Ensure data path is configured
    if not _ensure_data_path(app):
        sys.exit(0)

    # Show year select
    dlg = YearSelectDialog()
    if not dlg.exec():
        sys.exit(0)

    year = dlg.chosen_year
    company = dlg.chosen_company

    win = MainWindow(year, company)
    win.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
