"""
History View Module for IP Address Tracker & Geolocation Tool.

Provides:
- Styled Treeview table of persistent SQLite lookup history (newest first)
- Actions for manual refresh, deleting selected records, and clearing history
- Explicit confirmation dialog for destructive actions
- Detailed record inspection pane
"""
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from database.db import clear_history, delete_lookup, get_lookup_history
from database.models import LookupRecord

# Color Palette Definitions
BG_DARK = "#0F172A"       # Deep slate 900
CARD_BG = "#1E293B"       # Slate 800
CARD_BORDER = "#334155"   # Slate 700
ACCENT_BLUE = "#0EA5E9"   # Sky 500
ACCENT_RED = "#EF4444"    # Red 500
TEXT_LIGHT = "#F8FAFC"    # Slate 50
TEXT_MUTED = "#94A3B8"    # Slate 400


class HistoryView(tk.Frame):
    """View displaying historical lookup records stored in SQLite database."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, bg=BG_DARK)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._configure_treeview_styles()
        self._create_header_actions()
        self._create_history_table()
        self._create_detail_pane()

        # Load initial history data
        self.refresh_history()

    def _configure_treeview_styles(self) -> None:
        """Configure custom dark theme styles for ttk.Treeview."""
        style = ttk.Style()
        style.theme_use("clamp")

        style.configure(
            "History.Treeview",
            background=CARD_BG,
            foreground=TEXT_LIGHT,
            fieldbackground=CARD_BG,
            rowheight=28,
            bordercolor=CARD_BORDER,
            borderwidth=1,
            font=("Segoe UI", 9),
        )
        style.configure(
            "History.Treeview.Heading",
            background="#0F172A",
            foreground=ACCENT_BLUE,
            font=("Segoe UI", 9, "bold"),
            bordercolor=CARD_BORDER,
            borderwidth=1,
        )
        style.map(
            "History.Treeview",
            background=[("selected", ACCENT_BLUE)],
            foreground=[("selected", "#FFFFFF")],
        )

    def _create_header_actions(self) -> None:
        """Create header title and action controls bar."""
        header_frame = tk.Frame(self, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.columnconfigure(1, weight=1)

        title = tk.Label(
            header_frame,
            text="LOOKUP HISTORY & LOGS",
            font=("Segoe UI", 11, "bold"),
            fg=ACCENT_BLUE,
            bg=CARD_BG,
        )
        title.grid(row=0, column=0, padx=15, pady=12)

        btn_box = tk.Frame(header_frame, bg=CARD_BG)
        btn_box.grid(row=0, column=2, padx=15, pady=8)

        refresh_btn = tk.Button(
            btn_box,
            text="REFRESH",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg=TEXT_LIGHT,
            activebackground="#475569",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=4,
            command=self.refresh_history,
        )
        refresh_btn.pack(side="left", padx=5)

        delete_btn = tk.Button(
            btn_box,
            text="DELETE SELECTED",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg=TEXT_LIGHT,
            activebackground="#475569",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._delete_selected,
        )
        delete_btn.pack(side="left", padx=5)

        clear_btn = tk.Button(
            btn_box,
            text="CLEAR HISTORY",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_RED,
            fg="#FFFFFF",
            activebackground="#DC2626",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._clear_all_history,
        )
        clear_btn.pack(side="left", padx=5)

    def _create_history_table(self) -> None:
        """Create Treeview table for history records."""
        table_container = tk.Frame(self, bg=BG_DARK)
        table_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=5)
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        columns = (
            "id",
            "timestamp",
            "input",
            "type",
            "ip",
            "location",
            "org",
            "status",
        )

        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            style="History.Treeview",
            selectmode="browse",
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("timestamp", text="TIMESTAMP")
        self.tree.heading("input", text="INPUT VALUE")
        self.tree.heading("type", text="TYPE")
        self.tree.heading("ip", text="TARGET IP")
        self.tree.heading("location", text="LOCATION")
        self.tree.heading("org", text="ORGANIZATION")
        self.tree.heading("status", text="STATUS")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("timestamp", width=140, anchor="w")
        self.tree.column("input", width=140, anchor="w")
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("ip", width=130, anchor="w")
        self.tree.column("location", width=140, anchor="w")
        self.tree.column("org", width=150, anchor="w")
        self.tree.column("status", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_container, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

    def _create_detail_pane(self) -> None:
        """Create bottom details panel for selected record inspection."""
        self.detail_frame = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        self.detail_frame.grid(
            row=2, column=0, sticky="ew", padx=20, pady=(5, 20)
        )

        self.detail_lbl = tk.Label(
            self.detail_frame,
            text="Select a record above to view full historical details.",
            font=("Segoe UI", 9, "italic"),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        self.detail_lbl.pack(padx=15, pady=10, anchor="w")

    def refresh_history(self) -> None:
        """Reload records from SQLite database into Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        records = get_lookup_history()
        self.records_map = {}

        for rec in records:
            location_str = f"{rec.city}, {rec.country}" if rec.city != "N/A" else rec.country
            time_str = rec.timestamp[:19].replace("T", " ")
            item_id = self.tree.insert(
                "",
                "end",
                values=(
                    rec.id,
                    time_str,
                    rec.input_value,
                    rec.input_type,
                    rec.ip_address or "N/A",
                    location_str,
                    rec.organization,
                    rec.status,
                ),
            )
            self.records_map[item_id] = rec

    def _on_row_selected(self, event: tk.Event) -> None:
        """Render detailed panel when a row is selected."""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item_id = selected_items[0]
        rec: Optional[LookupRecord] = self.records_map.get(item_id)
        if not rec:
            return

        for w in self.detail_frame.winfo_children():
            w.destroy()

        header = tk.Label(
            self.detail_frame,
            text=f"RECORD DETAILS [ID #{rec.id}] - Input: '{rec.input_value}'",
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_BLUE,
            bg=CARD_BG,
        )
        header.pack(anchor="w", padx=15, pady=(8, 4))

        details_str = (
            f"Target IP: {rec.ip_address} ({rec.ip_version})  |  "
            f"Location: {rec.city}, {rec.region}, {rec.country} ({rec.country_code})  |  "
            f"Coordinates: Lat {rec.latitude}, Lon {rec.longitude}\n"
            f"Network: {rec.organization} | ISP: {rec.isp} | ASN: {rec.asn}  |  Timezone: {rec.timezone}\n"
            f"Timing: DNS {rec.dns_response_time_ms}ms, API {rec.api_response_time_ms}ms  |  Status: {rec.status}"
        )
        if rec.error_message:
            details_str += f"\nError: {rec.error_message}"

        info_lbl = tk.Label(
            self.detail_frame,
            text=details_str,
            font=("Segoe UI", 9),
            fg=TEXT_LIGHT,
            bg=CARD_BG,
            justify="left",
        )
        info_lbl.pack(anchor="w", padx=15, pady=(0, 8))

    def _delete_selected(self) -> None:
        """Delete currently selected history item with confirmation."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "Selection Required", "Please select a history record to delete."
            )
            return

        item_id = selected_items[0]
        rec: Optional[LookupRecord] = self.records_map.get(item_id)
        if not rec or rec.id is None:
            return

        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete lookup record #{rec.id} ('{rec.input_value}')?",
        ):
            delete_lookup(rec.id)
            self.refresh_history()

    def _clear_all_history(self) -> None:
        """Clear all history records with confirmation dialog."""
        if messagebox.askyesno(
            "Confirm Clear History",
            "Are you sure you want to clear ALL lookup history?\nThis action cannot be undone.",
        ):
            clear_history()
            self.refresh_history()
