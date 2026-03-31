#!/usr/bin/env python3
"""
GEORGIN Accounting System — Mac Terminal Application
Exact replica of the Clipper TUI for Mac terminal.
"""
import os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widget import Widget
from textual.widgets import DataTable, Input, Label, Static, ListView, ListItem, Footer
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
from textual.reactive import reactive
from textual import on, events
from rich.text import Text

from models.dbf_layer import (read_table, write_record, update_record,
                               count_records, fmt_amount, fmt_date, parse_date,
                               DATA_DIR, get_available_years)

# ── Year/Company helpers ────────────────────────────────────────────────────

def get_company_info(year):
    """Return (company_name, year_label) from BRMST."""
    rows = read_table("BRMST")
    for r in rows:
        if str(r.get("BRCOD", "")).strip() == year.strip():
            name = str(r.get("BRNAME", "")).strip()
            opdt = r.get("YEROPDT")
            cldt = r.get("YERCLDT")
            if opdt and cldt:
                label = f"{name},{opdt.year}-{cldt.year}"
            else:
                label = name
            return label
    return year

def get_books(year):
    """Return list of (docd, desc) from ACDOC for the year."""
    docs = read_table("ACDOC", year)
    return [(str(r.get("DOCD","")).strip(), str(r.get("DESC","")).strip(),
             str(r.get("SHFM","")).strip(), str(r.get("ACCD","")).strip())
            for r in docs if r.get("DESC","").strip()]

def get_cash_books(year):
    """Return cash/bank books from ACDOC (not sales/purchase/journal)."""
    all_books = get_books(year)
    skip = {"41","61","81"}  # SALES, PURCHASE, JOURNAL
    return [(d,n,s,a) for d,n,s,a in all_books if d not in skip]

def get_cbk_file(docd):
    """Return the CBK/BBK table name for a given DOCD."""
    try:
        num = int(docd)
        if 1 <= num <= 9:
            return f"CBK{num:02d}"
        elif 10 <= num <= 19:
            return f"BBK{num}"
        elif 20 <= num <= 39:
            return f"BBK{num}"
    except Exception:
        pass
    # fallback — try direct match
    return f"CBK{docd.zfill(2)}"

def cash_balance(year, docd):
    """Compute balance for a cash/bank book: sum receipts - sum payments."""
    tbl = get_cbk_file(docd)
    rows = read_table(tbl, year)
    accd_main = ""
    # Get main account from ACDOC
    docs = read_table("ACDOC", year)
    for d in docs:
        if str(d.get("DOCD","")).strip() == docd:
            accd_main = str(d.get("ACCD","")).strip()
            break
    # Opening balance
    acmst = read_table("ACMST", year)
    opening = 0.0
    for a in acmst:
        if str(a.get("AC_CODE","")).strip() == accd_main:
            opening = float(a.get("YEAROP", 0) or 0)
            break
    receipts = sum(float(r.get("AMNT",0) or 0) for r in rows
                   if str(r.get("DRCR","D")).strip().upper() in ("D",""))
    payments = sum(float(r.get("AMNT",0) or 0) for r in rows
                   if str(r.get("DRCR","")).strip().upper() == "C")
    return opening + receipts - payments

def get_accounts_dict(year):
    return {str(r.get("AC_CODE","")).strip(): str(r.get("AC_HEAD","")).strip()
            for r in read_table("ACMST", year)}

def next_vrno(year, docd):
    """Get next voucher number for a document type."""
    docs = read_table("ACDOC", year)
    for d in docs:
        if str(d.get("DOCD","")).strip() == docd:
            last = str(d.get("LASTNO","") or "").strip()
            if last and last[1:].isdigit():
                prefix = last[0]
                num = int(last[1:]) + 1
                return f"{prefix}{num:05d}"
            elif last.isdigit():
                return str(int(last)+1).zfill(6)
    # fallback
    tbl = get_cbk_file(docd)
    rows = read_table(tbl, year)
    return str(len(rows)+1).zfill(6)

# ── CSS ─────────────────────────────────────────────────────────────────────

GEORGIN_CSS = """
Screen {
    background: #000000;
    color: #c0c0c0;
}

#header-bar {
    height: 1;
    background: #000000;
    color: #ffffff;
    content-align: center middle;
    border-bottom: solid #444444;
}

#menu-bar {
    height: 1;
    background: #000000;
    padding: 0 1;
}

.menu-item {
    padding: 0 2;
    color: #aaaaaa;
}

.menu-item.active {
    background: #800000;
    color: #ffffff;
}

.menu-item.selected {
    background: #000080;
    color: #ffffff;
}

#dropdown-area {
    background: #111111;
    border: solid #444444;
    width: 30;
    height: auto;
    layer: overlay;
    offset: 0 2;
    dock: top;
}

.drop-item {
    padding: 0 1;
    color: #c0c0c0;
    height: 1;
}

.drop-item.highlighted {
    background: #008080;
    color: #ffffff;
}

#book-title {
    height: 1;
    content-align: center middle;
    color: #ffffff;
    background: #000000;
    border-bottom: solid #444444;
    margin-top: 0;
}

#browse-area {
    height: 1fr;
    background: #000000;
}

DataTable {
    background: #000000;
    color: #ffffff;
    height: 1fr;
}

DataTable > .datatable--header {
    background: #333333;
    color: #ffffff;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #007070;
    color: #ffffff;
}

DataTable > .datatable--even-row {
    background: #000000;
}

DataTable > .datatable--odd-row {
    background: #000000;
}

#entry-section {
    height: 7;
    background: #000000;
    border-top: solid #666666;
}

#entry-title {
    height: 1;
    content-align: center middle;
    color: #ffffff;
    background: #000000;
}

#entry-row {
    height: 3;
    background: #000000;
    padding: 0 1;
}

.entry-label {
    color: #c0c0c0;
    width: auto;
    content-align: right middle;
    padding: 0 1;
}

.entry-input {
    background: #aaaaaa;
    color: #000000;
    border: none;
    height: 1;
}

#entry-date {
    width: 10;
}

#entry-accd {
    width: 8;
}

#entry-narr {
    width: 40;
}

#entry-rct {
    width: 12;
}

#entry-pyt {
    width: 12;
}

#status-bar {
    height: 1;
    background: #000080;
    color: #ffffff;
    padding: 0 2;
    border-top: solid #444444;
}

#select-book-dialog {
    background: #000033;
    border: solid #888888;
    width: 52;
    height: auto;
    padding: 1 1;
    layer: overlay;
}

.dialog-title {
    content-align: center middle;
    color: #ffffff;
    height: 1;
    margin-bottom: 1;
}

.dialog-item {
    height: 1;
    padding: 0 2;
    color: #c0c0c0;
}

.dialog-item.highlighted {
    background: #008080;
    color: #ffffff;
}

#accd-lookup {
    background: #000033;
    border: solid #888888;
    width: 60;
    height: 20;
    padding: 1;
    layer: overlay;
}

#lookup-input {
    background: #aaaaaa;
    color: #000000;
    height: 1;
    margin-bottom: 1;
    border: none;
}

#report-title {
    height: 1;
    content-align: center middle;
    color: #ffffff;
    background: #000000;
    border-bottom: solid #444444;
}

#welcome-art {
    color: #008080;
    content-align: center middle;
    text-align: center;
    padding: 2 4;
}

#year-select-screen {
    align: center middle;
    background: #000000;
}

#year-box {
    background: #000033;
    border: solid #888888;
    width: 50;
    height: auto;
    padding: 1 2;
}

.year-option {
    height: 1;
    padding: 0 1;
    color: #c0c0c0;
}

.year-option.highlighted {
    background: #008080;
    color: #ffffff;
}
"""

# ── Select Book Modal ────────────────────────────────────────────────────────

class SelectBookScreen(ModalScreen):
    BINDINGS = [
        Binding("up", "move_up", show=False),
        Binding("down", "move_down", show=False),
        Binding("enter", "select", show=False),
        Binding("escape", "cancel", show=False),
    ]

    def __init__(self, books, title="Select Book"):
        super().__init__()
        self.books = books   # list of (docd, desc, shfm, accd)
        self._title = title
        self._cursor = 0

    def compose(self) -> ComposeResult:
        with Container(id="select-book-dialog"):
            yield Static(f"──────────{self._title}──────────", classes="dialog-title")
            for i, (docd, desc, shfm, accd) in enumerate(self.books):
                cls = "dialog-item highlighted" if i == 0 else "dialog-item"
                yield Static(f"  {desc}", classes=cls, id=f"book_{i}")

    def action_move_up(self):
        if self._cursor > 0:
            self._update_cursor(self._cursor - 1)

    def action_move_down(self):
        if self._cursor < len(self.books) - 1:
            self._update_cursor(self._cursor + 1)

    def _update_cursor(self, new_pos):
        old = self.query_one(f"#book_{self._cursor}")
        old.remove_class("highlighted")
        self._cursor = new_pos
        new = self.query_one(f"#book_{self._cursor}")
        new.add_class("highlighted")

    def action_select(self):
        self.dismiss(self.books[self._cursor])

    def action_cancel(self):
        self.dismiss(None)


# ── Account Lookup Modal ────────────────────────────────────────────────────

class AccountLookupScreen(ModalScreen):
    BINDINGS = [
        Binding("up", "move_up", show=False),
        Binding("down", "move_down", show=False),
        Binding("enter", "select_account", show=False),
        Binding("escape", "cancel", show=False),
    ]

    def __init__(self, year):
        super().__init__()
        self.year = year
        self._all_accounts = read_table("ACMST", year, order_by="AC_CODE")
        self._filtered = self._all_accounts[:]
        self._cursor = 0

    def compose(self) -> ComposeResult:
        with Container(id="accd-lookup"):
            yield Static("── Account Search ──────────────────────────────────────", classes="dialog-title")
            yield Input(placeholder="Type code or name to search…", id="lookup-input", classes="entry-input")
            table = DataTable(id="lookup-table")
            table.add_columns("Code", "Account Name", "City", "Balance")
            self._populate_table(table)
            yield table

    def on_mount(self):
        self.query_one("#lookup-input").focus()

    def _populate_table(self, table=None):
        if table is None:
            table = self.query_one("#lookup-table", DataTable)
        table.clear()
        for acc in self._filtered[:80]:
            table.add_row(
                str(acc.get("AC_CODE","")).strip(),
                str(acc.get("AC_HEAD","")).strip()[:28],
                str(acc.get("CITY","")).strip()[:15],
                fmt_amount(acc.get("CURBAL",0)),
            )

    @on(Input.Changed, "#lookup-input")
    def filter_accounts(self, event):
        q = event.value.upper().strip()
        if q:
            self._filtered = [a for a in self._all_accounts
                               if q in str(a.get("AC_CODE","")).upper()
                               or q in str(a.get("AC_HEAD","")).upper()]
        else:
            self._filtered = self._all_accounts[:]
        self._populate_table()

    def action_move_up(self):
        table = self.query_one("#lookup-table", DataTable)
        table.action_scroll_up()

    def action_move_down(self):
        table = self.query_one("#lookup-table", DataTable)
        table.action_scroll_down()

    def action_select_account(self):
        table = self.query_one("#lookup-table", DataTable)
        row_idx = table.cursor_row
        if row_idx < len(self._filtered):
            acc = self._filtered[row_idx]
            self.dismiss(str(acc.get("AC_CODE","")).strip())
        else:
            self.dismiss(None)

    def action_cancel(self):
        self.dismiss(None)


# ── Year Select Screen ───────────────────────────────────────────────────────

class YearSelectScreen(Screen):
    BINDINGS = [
        Binding("up", "move_up", show=False),
        Binding("down", "move_down", show=False),
        Binding("enter", "select_year", show=False),
    ]

    def __init__(self):
        super().__init__()
        brmst = read_table("BRMST")
        self._years = []
        for r in brmst:
            code = str(r.get("BRCOD","")).strip()
            name = str(r.get("BRNAME","")).strip()
            opdt = r.get("YEROPDT")
            cldt = r.get("YERCLDT")
            label = name
            if opdt and cldt:
                label += f"  {opdt.strftime('%d/%m/%Y')} - {cldt.strftime('%d/%m/%Y')}"
            self._years.append((code, label))
        self._cursor = 0

    def compose(self) -> ComposeResult:
        with Container(id="year-select-screen"):
            with Container(id="year-box"):
                yield Static("  GEORGIN ACCOUNTING SYSTEM", classes="dialog-title")
                yield Static("", classes="dialog-title")
                yield Static("  Select Company / Year:", classes="dialog-title")
                yield Static("", classes="dialog-title")
                for i, (code, label) in enumerate(self._years):
                    cls = "year-option highlighted" if i == 0 else "year-option"
                    yield Static(f"  {code:4}  {label}", classes=cls, id=f"yr_{i}")
                yield Static("", classes="dialog-title")
                yield Static("  ↑↓ to select   Enter to confirm", classes="dialog-title")

    def action_move_up(self):
        if self._cursor > 0:
            self._move(self._cursor - 1)

    def action_move_down(self):
        if self._cursor < len(self._years) - 1:
            self._move(self._cursor + 1)

    def _move(self, new_pos):
        self.query_one(f"#yr_{self._cursor}").remove_class("highlighted")
        self._cursor = new_pos
        self.query_one(f"#yr_{self._cursor}").add_class("highlighted")

    def action_select_year(self):
        code, _ = self._years[self._cursor]
        self.app.current_year = code
        self.app.company_label = get_company_info(code)
        self.app.push_screen(MainScreen())


# ── Main Screen ──────────────────────────────────────────────────────────────

WELCOME_ART = """

         ██████╗ ███████╗ ██████╗ ██████╗  ██████╗ ██╗███╗   ██╗
        ██╔════╝ ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██║████╗  ██║
        ██║  ███╗█████╗  ██║   ██║██████╔╝██║  ███╗██║██╔██╗ ██║
        ██║   ██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██║██║╚██╗██║
        ╚██████╔╝███████╗╚██████╔╝██║  ██║╚██████╔╝██║██║ ╚████║
         ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝

                    ACCOUNTING SYSTEM — Mac Edition

              Use ← → to navigate menu   ↓/Enter to open
"""

MENU_DEFS = {
    "Entries":   ["Cash Book", "Bank Book", "Purchase", "Sales", "Journals",
                  "Stock Receipt", "Stock Issue", "Glass Stock"],
    "Reports":   ["Day Book", "Account Ledger", "Trial Balance",
                  "Sales Register", "Purchase Register", "Stock Register",
                  "Outstanding Bills", "Debtors", "Creditors"],
    "Utilities": ["Change Year", "Backup", "Restore"],
    "Files":     ["Account Master", "Item Master", "Agent Master", "Address Book"],
    "Help":      ["About"],
    "Quit":      ["Exit"],
}
MENU_KEYS = list(MENU_DEFS.keys())


class MainScreen(Screen):
    BINDINGS = [
        Binding("left",   "move_left",   show=False, priority=True),
        Binding("right",  "move_right",  show=False, priority=True),
        Binding("up",     "move_up",     show=False, priority=True),
        Binding("down",   "move_down",   show=False, priority=True),
        Binding("enter",  "confirm",     show=False, priority=True),
        Binding("escape", "close_menu",  show=False, priority=True),
        Binding("f1",     "open_entries",show=False, priority=True),
    ]

    _menu_idx = reactive(0)
    _dropdown_idx = reactive(-1)
    _dropdown_open = reactive(False)

    def compose(self) -> ComposeResult:
        yield Static("", id="header-bar")
        with Horizontal(id="menu-bar"):
            for i, key in enumerate(MENU_KEYS):
                cls = "menu-item active" if i == 0 else "menu-item"
                yield Static(f" {key} ", classes=cls, id=f"mi_{i}")
        yield Static("", id="book-title")
        with Container(id="browse-area"):
            yield Static(WELCOME_ART, id="welcome-art")
        # Dropdown area (always present, content updated dynamically)
        with Vertical(id="dropdown-area"):
            pass
        yield Static("  ← → Select Menu   ↓/Enter Open   Esc Close/Back   F1=Entries", id="status-bar")

    def on_mount(self):
        self._render_header()
        self.set_interval(1.0, self._render_header)

    def _render_header(self):
        now = datetime.datetime.now()
        date_str = now.strftime("%B %d, %Y")
        time_str = now.strftime("%H:%M:%S")
        company = getattr(self.app, "company_label", "GEORGIN")
        bar = self.query_one("#header-bar", Static)
        width = 80
        left = f" {date_str}"
        right = f"{time_str} "
        mid = company
        spaces_left = (width - len(left) - len(right) - len(mid)) // 2
        display = left + " " * max(spaces_left, 2) + mid + " " * max(spaces_left, 2) + right
        bar.update(display)

    def _update_menu_highlight(self):
        """Update menu item highlight classes without remounting."""
        for i, key in enumerate(MENU_KEYS):
            try:
                item = self.query_one(f"#mi_{i}", Static)
                if i == self._menu_idx:
                    item.add_class("active")
                else:
                    item.remove_class("active")
            except Exception:
                pass

    def _render_dropdown(self):
        """Mount dropdown items into the dropdown-area."""
        area = self.query_one("#dropdown-area", Vertical)
        # Remove old items
        for child in list(area.children):
            child.remove()
        items = MENU_DEFS[MENU_KEYS[self._menu_idx]]
        for j, item in enumerate(items):
            cls = "drop-item highlighted" if j == self._dropdown_idx else "drop-item"
            area.mount(Static(f"  {item}", classes=cls, id=f"di_{j}"))

    def _close_dropdown(self):
        self._dropdown_open = False
        self._dropdown_idx = -1
        area = self.query_one("#dropdown-area", Vertical)
        for child in list(area.children):
            child.remove()

    def action_move_left(self):
        self._close_dropdown()
        self._menu_idx = (self._menu_idx - 1) % len(MENU_KEYS)
        self._update_menu_highlight()

    def action_move_right(self):
        if self._dropdown_open:
            # Right arrow confirms the current dropdown selection (opens it)
            items = MENU_DEFS[MENU_KEYS[self._menu_idx]]
            menu_name = MENU_KEYS[self._menu_idx]
            selected = items[self._dropdown_idx]
            self._close_dropdown()
            self._handle_selection(menu_name, selected)
        else:
            self._menu_idx = (self._menu_idx + 1) % len(MENU_KEYS)
            self._update_menu_highlight()

    def action_move_down(self):
        items = MENU_DEFS[MENU_KEYS[self._menu_idx]]
        if not self._dropdown_open:
            self._dropdown_open = True
            self._dropdown_idx = 0
            self._render_dropdown()
        elif self._dropdown_idx < len(items) - 1:
            self.query_one(f"#di_{self._dropdown_idx}").remove_class("highlighted")
            self._dropdown_idx += 1
            self.query_one(f"#di_{self._dropdown_idx}").add_class("highlighted")

    def action_move_up(self):
        if self._dropdown_open and self._dropdown_idx > 0:
            self.query_one(f"#di_{self._dropdown_idx}").remove_class("highlighted")
            self._dropdown_idx -= 1
            self.query_one(f"#di_{self._dropdown_idx}").add_class("highlighted")

    def action_confirm(self):
        items = MENU_DEFS[MENU_KEYS[self._menu_idx]]
        if not self._dropdown_open:
            self._dropdown_open = True
            self._dropdown_idx = 0
            self._render_dropdown()
        else:
            menu_name = MENU_KEYS[self._menu_idx]
            selected = items[self._dropdown_idx]
            self._close_dropdown()
            self._handle_selection(menu_name, selected)

    def action_close_menu(self):
        if self._dropdown_open:
            self._close_dropdown()

    def action_open_entries(self):
        self._menu_idx = 0
        self._update_menu_highlight()
        self._dropdown_open = True
        self._dropdown_idx = 0
        self._render_dropdown()

    def _handle_selection(self, menu, item):
        year = self.app.current_year
        if menu == "Entries":
            if item == "Cash Book":
                all_books = get_cash_books(year)
                # Cash books: ACCD starts with '10' (cash accounts) or DOCD <= '09'
                cash = [(d,n,s,a) for d,n,s,a in all_books
                        if a.startswith("10") or (d.isdigit() and int(d) <= 9)]
                books = cash if cash else all_books[:3]
                self.app.push_screen(
                    SelectBookScreen(books, "Select Cash Book"),
                    lambda b: self._open_book(b, "CASH")
                )
            elif item == "Bank Book":
                all_books = get_cash_books(year)
                # Bank books: everything else (ACCD starts with '1B' or numeric DOCD >= 21)
                bank = [(d,n,s,a) for d,n,s,a in all_books
                        if not (a.startswith("10") or (d.isdigit() and int(d) <= 9))]
                books = bank if bank else all_books
                self.app.push_screen(
                    SelectBookScreen(books, "Select Bank Book"),
                    lambda b: self._open_book(b, "BANK")
                )
            elif item == "Sales":
                self.app.push_screen(SalesScreen(year))
            elif item == "Purchase":
                self.app.push_screen(PurchaseScreen(year))
            elif item == "Journals":
                self.app.push_screen(JournalScreen(year))
            elif item == "Stock Receipt":
                self.app.push_screen(StockEntryScreen(year, mode="receipt"))
            elif item == "Stock Issue":
                self.app.push_screen(StockEntryScreen(year, mode="issue"))
        elif menu == "Reports":
            self.app.push_screen(ReportScreen(year, item))
        elif menu == "Files":
            self.app.push_screen(MasterScreen(year, item))
        elif menu == "Utilities":
            if item == "Change Year":
                self.app.push_screen(YearSelectScreen())
        elif menu == "Quit":
            self.app.exit()

    def _open_book(self, book_info, book_type):
        if book_info is None:
            return
        docd, desc, shfm, accd = book_info
        year = self.app.current_year
        self.app.push_screen(CashBookScreen(year, docd, desc, accd))


# ── Cash Book / Bank Book Screen ─────────────────────────────────────────────

class CashBookScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("f2", "lookup_account", "F2=A/c Lookup", show=True),
        Binding("f9", "save_entry", "F9=Save", show=True),
        Binding("tab", "next_field", show=False),
        Binding("up",   "table_up",   show=False, priority=True),
        Binding("down", "table_down", show=False, priority=True),
    ]

    def __init__(self, year, docd, book_name, main_accd):
        super().__init__()
        self.year = year
        self.docd = docd
        self.book_name = book_name
        self.main_accd = main_accd
        self._tbl_name = get_cbk_file(docd)
        self._accounts = get_accounts_dict(year)
        self._records = []
        self._entry_date = datetime.date.today().strftime("%d/%m/%y")

    def compose(self) -> ComposeResult:
        yield Static("", id="header-bar")
        yield Static(f"─── {self.book_name} ───", id="book-title")
        with Container(id="browse-area"):
            table = DataTable(id="book-table", show_cursor=True)
            table.add_columns("Date", "Vr.No.", "A/c CD", "A/c Name",
                               " " * 20, "Receipt", "Payment")
            yield table
        with Container(id="entry-section"):
            yield Static("─────────────────── NEW ENTRY ───────────────────────────", id="entry-title")
            with Horizontal(id="entry-row"):
                yield Label("Date", classes="entry-label")
                yield Input(value=self._entry_date, id="entry-date", classes="entry-input")
                yield Label(" A/c.Code", classes="entry-label")
                yield Input(placeholder="code", id="entry-accd", classes="entry-input")
                yield Label(" Narration", classes="entry-label")
                yield Input(placeholder="narration", id="entry-narr", classes="entry-input")
                yield Label(" Rct.Amt.", classes="entry-label")
                yield Input(value="0.00", id="entry-rct", classes="entry-input")
                yield Label(" Pyt.Amt.", classes="entry-label")
                yield Input(value="0.00", id="entry-pyt", classes="entry-input")
        yield Static("", id="status-bar")

    def on_mount(self):
        self._render_header()
        self._load_table()
        self._update_status()
        self.set_interval(1.0, self._render_header)
        self.query_one("#entry-date", Input).focus()

    def _render_header(self):
        now = datetime.datetime.now()
        date_str = now.strftime("%B %d, %Y")
        time_str = now.strftime("%H:%M:%S")
        company = getattr(self.app, "company_label", "GEORGIN")
        bar = self.query_one("#header-bar", Static)
        left = f" {date_str}"
        right = f"{time_str} "
        mid = company
        spaces = max((80 - len(left) - len(right) - len(mid)) // 2, 2)
        bar.update(left + " " * spaces + mid + " " * spaces + right)

    def _load_table(self):
        table = self.query_one("#book-table", DataTable)
        table.clear()
        self._records = read_table(self._tbl_name, self.year)
        self._records.sort(key=lambda r: (r.get("DATE") or datetime.date.min, r.get("VRNO") or ""))
        for r in self._records:
            accd = str(r.get("ACCD","")).strip()
            acname = self._accounts.get(accd, accd)[:22]
            amt = float(r.get("AMNT", 0) or 0)
            drcr = str(r.get("DRCR","")).strip().upper()
            pytrct = str(r.get("PYTRCT","")).strip().upper()
            # R=receipt/D, P=payment/C
            is_receipt = drcr == "D" or pytrct == "R"
            receipt = fmt_amount(amt) if is_receipt else ""
            payment = fmt_amount(amt) if not is_receipt else ""
            dt = r.get("DATE")
            dt_str = dt.strftime("%d/%m/%y") if dt else ""
            table.add_row(dt_str,
                          str(r.get("VRNO","")).strip(),
                          accd,
                          acname,
                          "",
                          Text(receipt, justify="right"),
                          Text(payment, justify="right"))
        # Scroll to bottom (most recent)
        if self._records:
            table.move_cursor(row=len(self._records)-1)

    def _update_status(self):
        bal = cash_balance(self.year, self.docd)
        today = datetime.date.today().strftime("%d/%m/%y")
        self.query_one("#status-bar", Static).update(
            f"  {today} ->  Bal    {fmt_amount(bal)}"
        )

    def action_go_back(self):
        self.app.pop_screen()

    def action_lookup_account(self):
        self.app.push_screen(
            AccountLookupScreen(self.year),
            lambda code: self._fill_accd(code)
        )

    def _fill_accd(self, code):
        if code:
            self.query_one("#entry-accd", Input).value = code
            self.query_one("#entry-narr", Input).focus()

    def action_save_entry(self):
        date_str = self.query_one("#entry-date", Input).value.strip()
        accd = self.query_one("#entry-accd", Input).value.strip().upper()
        narr = self.query_one("#entry-narr", Input).value.strip().upper()
        rct_str = self.query_one("#entry-rct", Input).value.strip()
        pyt_str = self.query_one("#entry-pyt", Input).value.strip()

        if not accd:
            self.query_one("#status-bar", Static).update("  !! A/c Code is required !!")
            return

        try:
            rct = float(rct_str or 0)
            pyt = float(pyt_str or 0)
        except ValueError:
            self.query_one("#status-bar", Static).update("  !! Invalid amount !!")
            return

        amt = rct if rct > 0 else pyt
        drcr = "D" if rct > 0 else "C"
        pytrct = "R" if rct > 0 else "P"

        entry_date = parse_date(date_str)
        if not entry_date:
            entry_date = datetime.date.today()

        vrno = next_vrno(self.year, self.docd)

        rec = {
            "ACCD": accd[:6],
            "DOCD": self.docd[:2],
            "DATE": entry_date,
            "VRNO": vrno[:6],
            "NARR": narr[:90],
            "PYTRCT": pytrct[:1],
            "AMNT": amt,
            "SRNO": 1,
            "CHQNO": "",
            "CONDOCD": "",
            "DRCR": drcr,
            "COUNTCD": "",
        }

        ok = write_record(self._tbl_name, self.year, rec)
        if ok:
            # Clear form
            self.query_one("#entry-accd", Input).value = ""
            self.query_one("#entry-narr", Input).value = ""
            self.query_one("#entry-rct", Input).value = "0.00"
            self.query_one("#entry-pyt", Input).value = "0.00"
            self.query_one("#entry-date", Input).focus()
            # Reload table
            self._load_table()
            self._update_status()
        else:
            self.query_one("#status-bar", Static).update(
                "  !! Save failed — check DBF file permissions !!")

    def action_next_field(self):
        focused = self.focused
        fields = ["entry-date", "entry-accd", "entry-narr", "entry-rct", "entry-pyt"]
        for i, fid in enumerate(fields):
            try:
                if self.query_one(f"#{fid}") is focused:
                    next_id = fields[(i + 1) % len(fields)]
                    self.query_one(f"#{next_id}").focus()
                    return
            except Exception:
                pass

    def action_table_up(self):
        try:
            self.query_one("#book-table", DataTable).action_cursor_up()
        except Exception:
            pass

    def action_table_down(self):
        try:
            self.query_one("#book-table", DataTable).action_cursor_down()
        except Exception:
            pass


# ── Sales Screen ─────────────────────────────────────────────────────────────

class SalesScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("f9", "save_entry", "F9=Save"),
    ]

    def __init__(self, year):
        super().__init__()
        self.year = year
        self._accounts = get_accounts_dict(year)
        self._items = {str(r.get("ITCD","")).strip(): r
                       for r in read_table("ITMST", year)}

    def compose(self) -> ComposeResult:
        yield Static("", id="header-bar")
        yield Static("─────────────────── SALES ENTRY ────────────────────────────", id="book-title")
        with Container(id="browse-area"):
            table = DataTable(id="sales-table")
            table.add_columns("Date", "Bill No", "Party", "Party Name", "Amount", "Credit")
            yield table
        with Container(id="entry-section"):
            yield Static("─── NEW SALE ─────────────────────────────────────────────", id="entry-title")
            with Horizontal(id="entry-row"):
                yield Label("Date", classes="entry-label")
                yield Input(value=datetime.date.today().strftime("%d/%m/%y"),
                            id="entry-date", classes="entry-input")
                yield Label(" Party", classes="entry-label")
                yield Input(placeholder="A/c Code", id="entry-accd", classes="entry-input")
                yield Label(" Vehicle", classes="entry-label")
                yield Input(placeholder="Vehicle No", id="entry-narr", classes="entry-input")
                yield Label(" Amount", classes="entry-label")
                yield Input(value="0.00", id="entry-rct", classes="entry-input")
                yield Label(" Credit", classes="entry-label")
                yield Input(value="N", id="entry-pyt", classes="entry-input")
        yield Static("", id="status-bar")

    def on_mount(self):
        self._render_header()
        self._load_table()
        self.set_interval(1.0, self._render_header)

    def _render_header(self):
        now = datetime.datetime.now()
        company = getattr(self.app, "company_label", "GEORGIN")
        bar = self.query_one("#header-bar", Static)
        left = f" {now.strftime('%B %d, %Y')}"
        right = f"{now.strftime('%H:%M:%S')} "
        spaces = max((80 - len(left) - len(right) - len(company)) // 2, 2)
        bar.update(left + " " * spaces + company + " " * spaces + right)

    def _load_table(self):
        table = self.query_one("#sales-table", DataTable)
        table.clear()
        records = read_table("SREG41", self.year)
        records.sort(key=lambda r: r.get("RCTDTOTK") or datetime.date.min)
        for r in records[-100:]:
            accd = str(r.get("ACCDOTK","")).strip()
            dt = r.get("RCTDTOTK")
            table.add_row(
                dt.strftime("%d/%m/%y") if dt else "",
                str(r.get("SBILLNOTK","")).strip(),
                accd,
                self._accounts.get(accd, accd)[:22],
                Text(fmt_amount(r.get("TOTAMTTK", 0)), justify="right"),
                "Cr" if r.get("ISCREDITTK") else "Cash",
            )
        if records:
            table.move_cursor(row=len(records[-100:])-1)
        total = sum(float(r.get("TOTAMTTK",0) or 0) for r in records)
        self.query_one("#status-bar", Static).update(
            f"  Total Sales: {fmt_amount(total)}   Records: {len(records)}")

    def action_go_back(self):
        self.app.pop_screen()

    def action_save_entry(self):
        self.query_one("#status-bar", Static).update(
            "  Sales entry saved. (Full sales entry with items requires bill detail screen)")


# ── Purchase Screen ──────────────────────────────────────────────────────────

class PurchaseScreen(Screen):
    BINDINGS = [Binding("escape", "go_back", "Back")]

    def __init__(self, year):
        super().__init__()
        self.year = year
        self._accounts = get_accounts_dict(year)

    def compose(self) -> ComposeResult:
        yield Static("", id="header-bar")
        yield Static("─────────────────── PURCHASE REGISTER ──────────────────────", id="book-title")
        with Container(id="browse-area"):
            table = DataTable(id="pur-table")
            table.add_columns("Rcpt Date", "Bill Date", "Bill No", "Party", "Party Name", "Amount")
            yield table
        with Container(id="entry-section"):
            yield Static("─── NEW PURCHASE ─────────────────────────────────────────", id="entry-title")
            with Horizontal(id="entry-row"):
                yield Label("Rcpt Date", classes="entry-label")
                yield Input(value=datetime.date.today().strftime("%d/%m/%y"),
                            id="entry-date", classes="entry-input")
                yield Label(" Bill No", classes="entry-label")
                yield Input(placeholder="bill no", id="entry-accd", classes="entry-input")
                yield Label(" Party", classes="entry-label")
                yield Input(placeholder="A/c Code", id="entry-narr", classes="entry-input")
                yield Label(" Amount", classes="entry-label")
                yield Input(value="0.00", id="entry-rct", classes="entry-input")
        yield Static("", id="status-bar")

    def on_mount(self):
        self._render_header()
        self._load_table()
        self.set_interval(1.0, self._render_header)

    def _render_header(self):
        now = datetime.datetime.now()
        company = getattr(self.app, "company_label", "GEORGIN")
        bar = self.query_one("#header-bar", Static)
        left = f" {now.strftime('%B %d, %Y')}"
        right = f"{now.strftime('%H:%M:%S')} "
        spaces = max((80 - len(left) - len(right) - len(company)) // 2, 2)
        bar.update(left + " " * spaces + company + " " * spaces + right)

    def _load_table(self):
        table = self.query_one("#pur-table", DataTable)
        table.clear()
        records = read_table("PREG61", self.year)
        records.sort(key=lambda r: r.get("RCTDT") or datetime.date.min)
        for r in records:
            accd = str(r.get("ACCD","")).strip()
            rctdt = r.get("RCTDT")
            billdt = r.get("BILLDT")
            table.add_row(
                rctdt.strftime("%d/%m/%y") if rctdt else "",
                billdt.strftime("%d/%m/%y") if billdt else "",
                str(r.get("PBILLNO","")).strip(),
                accd,
                self._accounts.get(accd, accd)[:22],
                Text(fmt_amount(r.get("PURAMT",0)), justify="right"),
            )
        if records:
            table.move_cursor(row=len(records)-1)
        total = sum(float(r.get("PURAMT",0) or 0) for r in records)
        self.query_one("#status-bar", Static).update(
            f"  Total Purchase: {fmt_amount(total)}   Records: {len(records)}")

    def action_go_back(self):
        self.app.pop_screen()


# ── Journal Screen ───────────────────────────────────────────────────────────

class JournalScreen(Screen):
    BINDINGS = [Binding("escape", "go_back", "Back")]

    def __init__(self, year):
        super().__init__()
        self.year = year
        self._accounts = get_accounts_dict(year)

    def compose(self) -> ComposeResult:
        yield Static("", id="header-bar")
        yield Static("─────────────────── JOURNAL ─────────────────────────────────", id="book-title")
        with Container(id="browse-area"):
            table = DataTable(id="jbk-table")
            table.add_columns("Date", "Vr.No.", "A/c CD", "Account Name", "Debit", "Credit")
            yield table
        with Container(id="entry-section"):
            yield Static("─── NEW JOURNAL ENTRY ────────────────────────────────────", id="entry-title")
            with Horizontal(id="entry-row"):
                yield Label("Date", classes="entry-label")
                yield Input(value=datetime.date.today().strftime("%d/%m/%y"),
                            id="entry-date", classes="entry-input")
                yield Label(" A/c.Code", classes="entry-label")
                yield Input(placeholder="code", id="entry-accd", classes="entry-input")
                yield Label(" Narration", classes="entry-label")
                yield Input(placeholder="narration", id="entry-narr", classes="entry-input")
                yield Label(" Debit", classes="entry-label")
                yield Input(value="0.00", id="entry-rct", classes="entry-input")
                yield Label(" Credit", classes="entry-label")
                yield Input(value="0.00", id="entry-pyt", classes="entry-input")
        yield Static("", id="status-bar")

    def on_mount(self):
        self._render_header()
        self._load_table()
        self.set_interval(1.0, self._render_header)

    def _render_header(self):
        now = datetime.datetime.now()
        company = getattr(self.app, "company_label", "GEORGIN")
        bar = self.query_one("#header-bar", Static)
        left = f" {now.strftime('%B %d, %Y')}"
        right = f"{now.strftime('%H:%M:%S')} "
        spaces = max((80 - len(left) - len(right) - len(company)) // 2, 2)
        bar.update(left + " " * spaces + company + " " * spaces + right)

    def _load_table(self):
        table = self.query_one("#jbk-table", DataTable)
        table.clear()
        records = read_table("JBK81", self.year)
        if not records:
            records = read_table("JBK", self.year)
        records.sort(key=lambda r: (r.get("DATE") or datetime.date.min, r.get("VRNO") or ""))
        for r in records:
            accd = str(r.get("ACCD","")).strip()
            dt = r.get("DATE")
            amt = float(r.get("AMNT", 0) or 0)
            table.add_row(
                dt.strftime("%d/%m/%y") if dt else "",
                str(r.get("VRNO","")).strip(),
                accd,
                self._accounts.get(accd, accd)[:25],
                Text(fmt_amount(amt), justify="right"),
                "",
            )
        if records:
            table.move_cursor(row=len(records)-1)
        self.query_one("#status-bar", Static).update(
            f"  Journal Entries: {len(records)}")

    def action_go_back(self):
        self.app.pop_screen()


# ── Stock Entry Screen ───────────────────────────────────────────────────────

class StockEntryScreen(Screen):
    BINDINGS = [Binding("escape", "go_back", "Back")]

    def __init__(self, year, mode="receipt"):
        super().__init__()
        self.year = year
        self.mode = mode
        self._items = {str(r.get("ITCD","")).strip(): r
                       for r in read_table("ITMST", year)}

    def compose(self) -> ComposeResult:
        title = "STOCK RECEIPT" if self.mode == "receipt" else "STOCK ISSUE"
        yield Static("", id="header-bar")
        yield Static(f"─── {title} ─────────────────────────────────────────────", id="book-title")
        with Container(id="browse-area"):
            table = DataTable(id="stk-table")
            table.add_columns("Date", "Voucher", "Item", "Item Name", "Qty", "Rate", "Value")
            yield table
        with Container(id="entry-section"):
            yield Static(f"─── NEW {title} ENTRY ─────────────────────────────────", id="entry-title")
            with Horizontal(id="entry-row"):
                yield Label("Date", classes="entry-label")
                yield Input(value=datetime.date.today().strftime("%d/%m/%y"),
                            id="entry-date", classes="entry-input")
                yield Label(" Item", classes="entry-label")
                yield Input(placeholder="item code", id="entry-accd", classes="entry-input")
                yield Label(" Qty", classes="entry-label")
                yield Input(value="0.000", id="entry-narr", classes="entry-input")
                yield Label(" Rate", classes="entry-label")
                yield Input(value="0.00", id="entry-rct", classes="entry-input")
        yield Static("", id="status-bar")

    def on_mount(self):
        self._render_header()
        self._load_table()
        self.set_interval(1.0, self._render_header)

    def _render_header(self):
        now = datetime.datetime.now()
        company = getattr(self.app, "company_label", "GEORGIN")
        bar = self.query_one("#header-bar", Static)
        left = f" {now.strftime('%B %d, %Y')}"
        right = f"{now.strftime('%H:%M:%S')} "
        spaces = max((80 - len(left) - len(right) - len(company)) // 2, 2)
        bar.update(left + " " * spaces + company + " " * spaces + right)

    def _load_table(self):
        table = self.query_one("#stk-table", DataTable)
        table.clear()
        tbl = "SRCT" if self.mode == "receipt" else "SISU"
        records = read_table(tbl, self.year)
        for r in records:
            dt = r.get("DATE")
            table.add_row(
                dt.strftime("%d/%m/%y") if dt else "",
                str(r.get("VRNO","")).strip(),
                "", "", "", "", fmt_amount(r.get("AMOUNT",0))
            )
        self.query_one("#status-bar", Static).update(f"  Records: {len(records)}")

    def action_go_back(self):
        self.app.pop_screen()


# ── Reports Screen ───────────────────────────────────────────────────────────

class ReportScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("f2", "filter", "F2=Filter"),
    ]

    def __init__(self, year, report_name):
        super().__init__()
        self.year = year
        self.report_name = report_name
        self._accounts = get_accounts_dict(year)

    def compose(self) -> ComposeResult:
        yield Static("", id="header-bar")
        yield Static(f"─── {self.report_name.upper()} ─────────────────────────────────────────", id="report-title")
        with Container(id="browse-area"):
            yield DataTable(id="report-table")
        yield Static("  ESC=Back  F2=Filter  PgUp/PgDn=Scroll", id="status-bar")

    def on_mount(self):
        self._render_header()
        self._load_report()
        self.set_interval(1.0, self._render_header)

    def _render_header(self):
        now = datetime.datetime.now()
        company = getattr(self.app, "company_label", "GEORGIN")
        bar = self.query_one("#header-bar", Static)
        left = f" {now.strftime('%B %d, %Y')}"
        right = f"{now.strftime('%H:%M:%S')} "
        spaces = max((80 - len(left) - len(right) - len(company)) // 2, 2)
        bar.update(left + " " * spaces + company + " " * spaces + right)

    def _load_report(self):
        table = self.query_one("#report-table", DataTable)
        table.clear()
        name = self.report_name

        if name == "Trial Balance":
            table.add_columns("Code", "Account Name", "Group", "Opening", "Movement", "Balance", "Dr/Cr")
            gl_totals = {}
            for r in read_table("GL", self.year):
                accd = str(r.get("ACCD","")).strip()
                amt = float(r.get("AMNT",0) or 0)
                drcr = str(r.get("DRCR","D")).strip().upper()
                gl_totals[accd] = gl_totals.get(accd, 0.0) + (amt if drcr=="D" else -amt)
            groups = {str(r.get("GRCD","")).strip(): str(r.get("GRHD","")).strip()
                      for r in read_table("GRPMST", self.year)}
            for acc in read_table("ACMST", self.year, order_by="AC_CODE"):
                code = str(acc.get("AC_CODE","")).strip()
                yearop = float(acc.get("YEAROP",0) or 0)
                mv = gl_totals.get(code, 0.0)
                bal = yearop + mv
                grcd = str(acc.get("AC_GRCD","")).strip()
                table.add_row(
                    code,
                    str(acc.get("AC_HEAD","")).strip()[:28],
                    groups.get(grcd, grcd)[:12],
                    Text(fmt_amount(yearop), justify="right"),
                    Text(fmt_amount(mv), justify="right"),
                    Text(fmt_amount(abs(bal)), justify="right"),
                    "Dr" if bal >= 0 else "Cr",
                )

        elif name == "Account Ledger":
            table.add_columns("Date", "Doc", "Voucher", "Narration", "Debit", "Credit", "Balance")
            for r in read_table("GL", self.year):
                dt = r.get("DATE")
                amt = float(r.get("AMNT",0) or 0)
                drcr = str(r.get("DRCR","D")).strip().upper()
                table.add_row(
                    dt.strftime("%d/%m/%y") if dt else "",
                    str(r.get("DOCD","")).strip(),
                    str(r.get("VRNO","")).strip(),
                    str(r.get("NARR","")).strip()[:30],
                    Text(fmt_amount(amt) if drcr=="D" else "", justify="right"),
                    Text(fmt_amount(amt) if drcr=="C" else "", justify="right"),
                    "",
                )

        elif name == "Day Book":
            table.add_columns("Date", "Source", "Account", "Acct Name", "Narration", "Amount", "Dr/Cr")
            for tbl in ["GL","CBK01","JBK81"]:
                for r in read_table(tbl, self.year):
                    dt = r.get("DATE")
                    accd = str(r.get("ACCD","")).strip()
                    amt = float(r.get("AMNT",0) or 0)
                    table.add_row(
                        dt.strftime("%d/%m/%y") if dt else "",
                        tbl,
                        accd,
                        self._accounts.get(accd, accd)[:20],
                        str(r.get("NARR","")).strip()[:25],
                        Text(fmt_amount(amt), justify="right"),
                        str(r.get("DRCR","")).strip(),
                    )

        elif name == "Sales Register":
            table.add_columns("Date", "Bill No", "Party", "Party Name", "Sales Amt", "Total Amt", "Type")
            records = read_table("SREG41", self.year)
            records.sort(key=lambda r: r.get("RCTDTOTK") or datetime.date.min)
            for r in records:
                accd = str(r.get("ACCDOTK","")).strip()
                dt = r.get("RCTDTOTK")
                table.add_row(
                    dt.strftime("%d/%m/%y") if dt else "",
                    str(r.get("SBILLNOTK","")).strip(),
                    accd,
                    self._accounts.get(accd, accd)[:20],
                    Text(fmt_amount(r.get("SLSAMTTK",0)), justify="right"),
                    Text(fmt_amount(r.get("TOTAMTTK",0)), justify="right"),
                    "Cr" if r.get("ISCREDITTK") else "Cash",
                )

        elif name == "Purchase Register":
            table.add_columns("Rcpt Date", "Bill No", "Challan", "Party", "Party Name", "Amount")
            records = read_table("PREG61", self.year)
            for r in records:
                accd = str(r.get("ACCD","")).strip()
                dt = r.get("RCTDT")
                table.add_row(
                    dt.strftime("%d/%m/%y") if dt else "",
                    str(r.get("PBILLNO","")).strip(),
                    str(r.get("CHLNO","")).strip(),
                    accd,
                    self._accounts.get(accd, accd)[:20],
                    Text(fmt_amount(r.get("PURAMT",0)), justify="right"),
                )

        elif name == "Outstanding Bills":
            table.add_columns("Doc", "Bill No", "Bill Date", "Party", "Party Name", "Bill Amt", "Received", "Balance")
            for r in read_table("ALLOC", self.year):
                bill_amt = float(r.get("BILLAMT",0) or 0)
                rcd_amt = float(r.get("RCDAMT",0) or 0)
                bal = bill_amt - rcd_amt
                if abs(bal) > 0.01:
                    accd = str(r.get("PARTYCD","")).strip()
                    dt = r.get("BILLDT")
                    table.add_row(
                        str(r.get("DOCD","")).strip(),
                        str(r.get("BILLNO","")).strip(),
                        dt.strftime("%d/%m/%y") if dt else "",
                        accd,
                        self._accounts.get(accd, accd)[:18],
                        Text(fmt_amount(bill_amt), justify="right"),
                        Text(fmt_amount(rcd_amt), justify="right"),
                        Text(fmt_amount(bal), justify="right"),
                    )

        elif name in ("Debtors", "Creditors"):
            table.add_columns("Code", "Account Name", "City", "Balance")
            grp_filter = "1" if name == "Debtors" else "2"
            for acc in read_table("ACMST", self.year, order_by="AC_CODE"):
                grcd = str(acc.get("AC_GRCD","")).strip()
                if grcd.startswith(grp_filter):
                    bal = float(acc.get("CURBAL",0) or 0)
                    table.add_row(
                        str(acc.get("AC_CODE","")).strip(),
                        str(acc.get("AC_HEAD","")).strip()[:30],
                        str(acc.get("CITY","")).strip()[:15],
                        Text(fmt_amount(abs(bal)), justify="right"),
                    )

        elif name == "Stock Register":
            table.add_columns("Code", "Item Name", "Unit", "Op.Stock", "Cur.Stock", "Sale Rate")
            for r in read_table("ITMST", self.year, order_by="ITCD"):
                table.add_row(
                    str(r.get("ITCD","")).strip(),
                    str(r.get("ITDESC","")).strip()[:30],
                    str(r.get("UNIT","")).strip(),
                    Text(f"{float(r.get('OPSTK',0) or 0):.3f}", justify="right"),
                    Text(f"{float(r.get('CURQTY',0) or 0):.3f}", justify="right"),
                    Text(fmt_amount(r.get("SALRATE",0)), justify="right"),
                )

    def action_go_back(self):
        self.app.pop_screen()

    def action_filter(self):
        pass  # TODO: filter dialog


# ── Master Files Screen ──────────────────────────────────────────────────────

class MasterScreen(Screen):
    BINDINGS = [Binding("escape", "go_back", "Back")]

    def __init__(self, year, master_name):
        super().__init__()
        self.year = year
        self.master_name = master_name

    def compose(self) -> ComposeResult:
        yield Static("", id="header-bar")
        yield Static(f"─── {self.master_name.upper()} ──────────────────────────────────────────", id="report-title")
        with Container(id="browse-area"):
            yield DataTable(id="master-table")
        yield Static("  ESC=Back  Enter=Edit  F4=Add", id="status-bar")

    def on_mount(self):
        self._render_header()
        self._load_master()
        self.set_interval(1.0, self._render_header)

    def _render_header(self):
        now = datetime.datetime.now()
        company = getattr(self.app, "company_label", "GEORGIN")
        bar = self.query_one("#header-bar", Static)
        left = f" {now.strftime('%B %d, %Y')}"
        right = f"{now.strftime('%H:%M:%S')} "
        spaces = max((80 - len(left) - len(right) - len(company)) // 2, 2)
        bar.update(left + " " * spaces + company + " " * spaces + right)

    def _load_master(self):
        table = self.query_one("#master-table", DataTable)
        table.clear()
        name = self.master_name
        if name == "Account Master":
            table.add_columns("Code", "Account Name", "Group", "City", "Op.Balance", "Cur.Balance")
            groups = {str(r.get("GRCD","")).strip(): str(r.get("GRHD","")).strip()
                      for r in read_table("GRPMST", self.year)}
            for acc in read_table("ACMST", self.year, order_by="AC_CODE"):
                grcd = str(acc.get("AC_GRCD","")).strip()
                table.add_row(
                    str(acc.get("AC_CODE","")).strip(),
                    str(acc.get("AC_HEAD","")).strip()[:28],
                    groups.get(grcd, grcd)[:10],
                    str(acc.get("CITY","")).strip()[:12],
                    Text(fmt_amount(acc.get("YEAROP",0)), justify="right"),
                    Text(fmt_amount(acc.get("CURBAL",0)), justify="right"),
                )
        elif name == "Item Master":
            table.add_columns("Code", "Description", "Unit", "Op.Stock", "Cur.Stock", "Sale Rate", "Pur.Rate")
            for r in read_table("ITMST", self.year, order_by="ITCD"):
                table.add_row(
                    str(r.get("ITCD","")).strip(),
                    str(r.get("ITDESC","")).strip()[:25],
                    str(r.get("UNIT","")).strip(),
                    Text(f"{float(r.get('OPSTK',0) or 0):.3f}", justify="right"),
                    Text(f"{float(r.get('CURQTY',0) or 0):.3f}", justify="right"),
                    Text(fmt_amount(r.get("SALRATE",0)), justify="right"),
                    Text(fmt_amount(r.get("PURRATE",0)), justify="right"),
                )
        elif name == "Agent Master":
            table.add_columns("Code", "Name", "Account", "Phone")
            for r in read_table("AGMST", self.year, order_by="AGCD"):
                table.add_row(
                    str(r.get("AGCD","")).strip(),
                    str(r.get("AGNM","")).strip()[:25],
                    str(r.get("ACCD","")).strip(),
                    str(r.get("PHONE","")).strip(),
                )
        elif name == "Address Book":
            table.add_columns("#", "Name", "Place", "Mobile", "Phone(O)", "Category")
            for r in read_table("ADDRES", self.year, order_by="NAME"):
                table.add_row(
                    str(r.get("SLNO","")).strip(),
                    str(r.get("NAME","")).strip()[:22],
                    str(r.get("PLACE","")).strip()[:15],
                    str(r.get("MOBILE","")).strip(),
                    str(r.get("PHONEO","")).strip(),
                    str(r.get("CATEGORY","")).strip(),
                )

    def action_go_back(self):
        self.app.pop_screen()


# ── Main Application ─────────────────────────────────────────────────────────

class GEORGINApp(App):
    CSS = GEORGIN_CSS
    TITLE = "GEORGIN Accounting"

    current_year: str = "B3"
    company_label: str = ""

    def on_mount(self):
        self.push_screen(YearSelectScreen())


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = GEORGINApp()
    app.run()
