"""
Field Project GUI View Module for IP Address Tracker & Geolocation Tool.

Implements the Manual-First Field Project Interface:
- Displays available observations loaded from SQLite Lookup History (N / 50).
- Shows Manual Observations, Remaining count, and Target Status.
- Provides REFRESH FROM HISTORY control.
- Provides optional COMPLETE REMAINING N AUTOMATICALLY button (only active when N < 50).
- Displays live progress bar and table during controlled automatic completion.
"""
import csv
from pathlib import Path
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

from services.field_test_service import (
    export_field_dataset_from_history,
    get_default_output_path,
    get_field_project_status,
    run_automatic_completion,
)
from services.lookup_service import LookupResult

# Color constants
BG_DARK = "#0F172A"       # Deep slate 900
CARD_BG = "#1E293B"       # Slate 800
CARD_BORDER = "#334155"   # Slate 700
ACCENT_BLUE = "#0EA5E9"   # Sky 500
ACCENT_GREEN = "#10B981"  # Emerald 500
ACCENT_YELLOW = "#F59E0B" # Amber 500
TEXT_LIGHT = "#F8FAFC"    # Slate 50
TEXT_MUTED = "#94A3B8"    # Slate 400


class FieldTestView(tk.Frame):
    """View module for manual-first 50-website field project workflow."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, bg=BG_DARK)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.is_running = False
        self.stop_event = threading.Event()
        self.status_data: Dict = {}

        self._configure_styles()
        self._create_header()
        self._create_stats_bar()
        self._create_main_content()

        # Load initial status from History
        self.refresh_status()

    def _configure_styles(self) -> None:
        """Configure custom Treeview styles for Field Test table."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "FieldTest.Treeview",
            background=CARD_BG,
            foreground=TEXT_LIGHT,
            fieldbackground=CARD_BG,
            rowheight=26,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.configure(
            "FieldTest.Treeview.Heading",
            background="#0284C7",
            foreground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
        )

    def _create_header(self) -> None:
        """Create header bar with title and informational banner."""
        header_frame = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.columnconfigure(0, weight=1)

        title = tk.Label(
            header_frame,
            text="FIELD PROJECT — 50-WEBSITE DATA COLLECTION",
            font=("Segoe UI", 11, "bold"),
            fg=ACCENT_BLUE,
            bg=CARD_BG,
        )
        title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 2))

        banner = tk.Label(
            header_frame,
            text="* MANUAL-FIRST METHODOLOGY: Normal lookups executed on Dashboard are automatically collected in History for this field project.",
            font=("Segoe UI", 8, "bold"),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        banner.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))

    def _create_stats_bar(self) -> None:
        """Create stat cards and control buttons bar."""
        bar_frame = tk.Frame(self, bg=BG_DARK)
        bar_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        for i in range(4):
            bar_frame.columnconfigure(i, weight=1)

        # 4 Stat Cards
        self.card_available = self._create_stat_card(bar_frame, 0, "AVAILABLE OBSERVATIONS", "0 / 50", "History Records")
        self.card_manual = self._create_stat_card(bar_frame, 1, "MANUAL OBSERVATIONS", "0", "Dashboard Lookups")
        self.card_remaining = self._create_stat_card(bar_frame, 2, "REMAINING", "50", "Needed for Target")
        self.card_status = self._create_stat_card(bar_frame, 3, "STATUS", "INCOMPLETE", "Target: 50 Sites")

        # Action Buttons Frame
        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        self.btn_refresh = tk.Button(
            btn_frame,
            text="REFRESH FROM HISTORY",
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG,
            fg=TEXT_LIGHT,
            activebackground=CARD_BORDER,
            activeforeground=TEXT_LIGHT,
            bd=1,
            cursor="hand2",
            padx=15,
            pady=6,
            command=self.refresh_status,
        )
        self.btn_refresh.pack(side="left", padx=(0, 10))

        self.btn_auto = tk.Button(
            btn_frame,
            text="COMPLETE REMAINING AUTOMATICALLY",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_BLUE,
            fg="#FFFFFF",
            activebackground="#0284C7",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=15,
            pady=6,
            command=self._start_automatic_completion,
        )
        self.btn_auto.pack(side="left", padx=10)

        self.btn_view_data = tk.Button(
            btn_frame,
            text="VIEW FIELD DATA",
            font=("Segoe UI", 9, "bold"),
            bg=CARD_BG,
            fg=TEXT_LIGHT,
            activebackground=CARD_BORDER,
            activeforeground=TEXT_LIGHT,
            bd=1,
            cursor="hand2",
            padx=15,
            pady=6,
            command=self._view_field_dataset,
        )
        self.btn_view_data.pack(side="left", padx=10)

        self.lbl_progress_info = tk.Label(
            btn_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg=ACCENT_YELLOW,
            bg=BG_DARK,
        )
        self.lbl_progress_info.pack(side="right", padx=10)

    def _create_stat_card(
        self, parent: tk.Widget, col: int, title: str, val: str, sub: str
    ) -> Dict[str, tk.Label]:
        """Create styled stat card frame."""
        card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)

        t_lbl = tk.Label(card, text=title, font=("Segoe UI", 8, "bold"), fg=ACCENT_BLUE, bg=CARD_BG)
        t_lbl.pack(anchor="w", padx=12, pady=(10, 2))

        v_lbl = tk.Label(card, text=val, font=("Segoe UI", 13, "bold"), fg=TEXT_LIGHT, bg=CARD_BG)
        v_lbl.pack(anchor="w", padx=12, pady=2)

        s_lbl = tk.Label(card, text=sub, font=("Segoe UI", 8), fg=TEXT_MUTED, bg=CARD_BG)
        s_lbl.pack(anchor="w", padx=12, pady=(0, 10))

        return {"val": v_lbl, "sub": s_lbl}

    def _create_main_content(self) -> None:
        """Create table and progress bar container."""
        content_frame = tk.Frame(self, bg=BG_DARK)
        content_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)

        # Progress bar
        self.progress_bar = ttk.Progressbar(content_frame, mode="determinate")
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Table container
        table_card = tk.Frame(
            content_frame,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        table_card.grid(row=1, column=0, sticky="nsew")
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(0, weight=1)

        columns = (
            "idx",
            "domain",
            "input_type",
            "ip",
            "country",
            "dns_time",
            "api_time",
            "status",
        )
        self.tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            style="FieldTest.Treeview",
        )

        self.tree.heading("idx", text="#")
        self.tree.heading("domain", text="DOMAIN")
        self.tree.heading("input_type", text="TYPE")
        self.tree.heading("ip", text="SELECTED IP")
        self.tree.heading("country", text="COUNTRY")
        self.tree.heading("dns_time", text="DNS (ms)")
        self.tree.heading("api_time", text="API (ms)")
        self.tree.heading("status", text="STATUS")

        self.tree.column("idx", width=40, anchor="center")
        self.tree.column("domain", width=180, anchor="w")
        self.tree.column("input_type", width=70, anchor="center")
        self.tree.column("ip", width=130, anchor="w")
        self.tree.column("country", width=120, anchor="w")
        self.tree.column("dns_time", width=75, anchor="center")
        self.tree.column("api_time", width=75, anchor="center")
        self.tree.column("status", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_card, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def refresh_status(self) -> None:
        """Query SQLite History and update UI cards and observation data."""
        self.status_data = get_field_project_status()

        avail = self.status_data["available_count"]
        rem = self.status_data["remaining"]
        st = self.status_data["status"]

        self.card_available["val"].config(text=f"{avail} / 50")
        self.card_manual["val"].config(text=str(avail))
        self.card_remaining["val"].config(text=str(rem))

        if st == "TARGET_REACHED":
            self.card_status["val"].config(text="TARGET REACHED ✓", fg=ACCENT_GREEN)
            self.btn_auto.config(state="disabled", text="TARGET COMPLETED ✓", bg=CARD_BORDER)
        else:
            self.card_status["val"].config(text="INCOMPLETE", fg=ACCENT_YELLOW)
            self.btn_auto.config(
                state="normal",
                text=f"COMPLETE REMAINING {rem} AUTOMATICALLY",
                bg=ACCENT_BLUE,
            )

        self._populate_table_from_records(self.status_data["unique_records"])

    def _populate_table_from_records(self, records: List) -> None:
        """Populate Treeview table with records from History."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, rec in enumerate(records[:50], start=1):
            domain = rec.domain or rec.input_value
            self.tree.insert(
                "",
                "end",
                values=(
                    idx,
                    domain,
                    rec.input_type or "DOMAIN",
                    rec.ip_address or "N/A",
                    rec.country or "N/A",
                    f"{rec.dns_response_time_ms:.1f}",
                    f"{rec.api_response_time_ms:.1f}",
                    rec.status,
                ),
            )

    def _start_automatic_completion(self) -> None:
        """Launch background thread for automatic completion of remaining lookups."""
        rem = self.status_data.get("remaining", 0)
        if rem <= 0:
            messagebox.showinfo("Target Reached", "The 50-observation field project target is already completed.")
            return

        confirm = messagebox.askyesno(
            "Confirm Automatic Completion",
            f"You have {self.status_data['available_count']} valid observations in History.\n\n"
            f"Would you like to automatically complete the remaining {rem} website lookups to reach the 50-observation target?",
        )
        if not confirm:
            return

        self.is_running = True
        self.stop_event.clear()
        self.btn_auto.config(state="disabled")
        self.btn_refresh.config(state="disabled")
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = rem

        thread = threading.Thread(
            target=self._run_completion_thread, args=(rem,), daemon=True
        )
        thread.start()

    def _run_completion_thread(self, remaining_count: int) -> None:
        """Background thread executing automatic completion lookups."""
        def progress_cb(current: int, total: int, domain: str, res: LookupResult):
            self.after(
                0, self._update_progress_ui, current, total, domain, res
            )

        try:
            run_automatic_completion(
                progress_callback=progress_cb,
                stop_event=self.stop_event,
                delay_seconds=0.5,
            )
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Completion Error", str(e)))
        finally:
            self.after(0, self._on_completion_finished)

    def _update_progress_ui(
        self, current: int, total: int, domain: str, res: LookupResult
    ) -> None:
        """Update UI progress bar and table during execution."""
        self.progress_bar["value"] = current
        self.lbl_progress_info.config(
            text=f"Running Auto Completion: {current}/{total} ({domain})"
        )
        self.refresh_status()

    def _on_completion_finished(self) -> None:
        """Clean up state after completion finishes."""
        self.is_running = False
        self.btn_refresh.config(state="normal")
        self.lbl_progress_info.config(text="Automatic completion finished.")
        export_field_dataset_from_history()
        self.refresh_status()
        messagebox.showinfo("Field Project Complete", "Field project observations updated and saved successfully.")

    def _view_field_dataset(self) -> None:
        """Export and open field dataset view."""
        export_field_dataset_from_history()
        self.refresh_status()
        out_p = get_default_output_path()
        messagebox.showinfo(
            "Field Dataset Exported",
            f"Field project dataset exported to:\n{out_p}\n\nTotal observations: {self.status_data['available_count']}",
        )
