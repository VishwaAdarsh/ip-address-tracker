"""
Field Test GUI View Module for IP Address Tracker & Geolocation Tool.

Provides:
- Controls for starting and stopping the 50-website batch research test
- Non-blocking background thread execution for batch lookups
- Real-time progress bar and status updates
- Live Treeview table displaying results as each website is processed
"""
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from services.field_test_service import load_test_websites, run_field_test
from services.lookup_service import LookupResult

# Palette constants
BG_DARK = "#0F172A"       # Deep slate 900
CARD_BG = "#1E293B"       # Slate 800
CARD_BORDER = "#334155"   # Slate 700
ACCENT_BLUE = "#0EA5E9"   # Sky 500
ACCENT_GREEN = "#10B981"  # Emerald 500
ACCENT_RED = "#EF4444"    # Red 500
TEXT_LIGHT = "#F8FAFC"    # Slate 50
TEXT_MUTED = "#94A3B8"    # Slate 400


class FieldTestView(tk.Frame):
    """View module for controlling and displaying live 50-website field tests."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, bg=BG_DARK)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.stop_event: Optional[threading.Event] = None
        self.is_running = False

        self._configure_styles()
        self._create_header_controls()
        self._create_progress_section()
        self._create_results_table()

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
            bordercolor=CARD_BORDER,
            borderwidth=1,
            font=("Segoe UI", 9),
        )
        style.configure(
            "FieldTest.Treeview.Heading",
            background="#0F172A",
            foreground=ACCENT_BLUE,
            font=("Segoe UI", 9, "bold"),
            bordercolor=CARD_BORDER,
            borderwidth=1,
        )

    def _create_header_controls(self) -> None:
        """Create header title and start/stop action buttons."""
        header_frame = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.columnconfigure(1, weight=1)

        title = tk.Label(
            header_frame,
            text="50-WEBSITE FIELD STUDY & DATA COLLECTION",
            font=("Segoe UI", 11, "bold"),
            fg=ACCENT_BLUE,
            bg=CARD_BG,
        )
        title.grid(row=0, column=0, padx=15, pady=12)

        btn_box = tk.Frame(header_frame, bg=CARD_BG)
        btn_box.grid(row=0, column=2, padx=15, pady=8)

        self.start_btn = tk.Button(
            btn_box,
            text="START FIELD TEST",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_BLUE,
            fg="#FFFFFF",
            activebackground="#0284C7",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=15,
            pady=5,
            command=self._start_field_test,
        )
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = tk.Button(
            btn_box,
            text="STOP / PAUSE",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_RED,
            fg="#FFFFFF",
            activebackground="#DC2626",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            state="disabled",
            padx=15,
            pady=5,
            command=self._stop_field_test,
        )
        self.stop_btn.pack(side="left", padx=5)

    def _create_progress_section(self) -> None:
        """Create progress bar and status text section."""
        prog_frame = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        prog_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        prog_frame.columnconfigure(0, weight=1)

        self.progress_lbl = tk.Label(
            prog_frame,
            text="Dataset Ready: 50 predefined websites loaded from data/field_test/websites.csv",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_LIGHT,
            bg=CARD_BG,
            anchor="w",
        )
        self.progress_lbl.pack(fill="x", padx=15, pady=(8, 4))

        self.progress_bar = ttk.Progressbar(
            prog_frame, orient="horizontal", mode="determinate", maximum=50
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 10))

    def _create_results_table(self) -> None:
        """Create Treeview table for live field test results."""
        table_container = tk.Frame(self, bg=BG_DARK)
        table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(5, 20))
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(0, weight=1)

        columns = (
            "id",
            "domain",
            "category",
            "ip",
            "location",
            "org",
            "dns_ms",
            "api_ms",
            "status",
        )

        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            style="FieldTest.Treeview",
            selectmode="browse",
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("domain", text="DOMAIN")
        self.tree.heading("category", text="CATEGORY")
        self.tree.heading("ip", text="SELECTED IP")
        self.tree.heading("location", text="LOCATION")
        self.tree.heading("org", text="ORGANIZATION")
        self.tree.heading("dns_ms", text="DNS TIME")
        self.tree.heading("api_ms", text="API TIME")
        self.tree.heading("status", text="STATUS")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("domain", width=130, anchor="w")
        self.tree.column("category", width=100, anchor="w")
        self.tree.column("ip", width=120, anchor="w")
        self.tree.column("location", width=130, anchor="w")
        self.tree.column("org", width=140, anchor="w")
        self.tree.column("dns_ms", width=75, anchor="center")
        self.tree.column("api_ms", width=75, anchor="center")
        self.tree.column("status", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_container, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _start_field_test(self) -> None:
        """Launch background worker thread for 50-website experiment."""
        if self.is_running:
            return

        self.is_running = True
        self.stop_event = threading.Event()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        # Clear existing table rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.progress_bar["value"] = 0
        self.progress_lbl.config(
            text="● RUNNING EXPERIMENT: 0 / 50 (0%)", fg=ACCENT_BLUE
        )

        threading.Thread(target=self._worker_run_test, daemon=True).start()

    def _worker_run_test(self) -> None:
        """Worker thread executing sequential field lookups."""
        try:
            websites = load_test_websites()

            def _progress_cb(current: int, total: int, domain: str, res: LookupResult):
                self.after(
                    0, self._update_progress_ui, current, total, domain, res
                )

            run_field_test(
                websites=websites,
                progress_callback=_progress_cb,
                stop_event=self.stop_event,
                delay_seconds=0.5,
            )

        except Exception as e:
            self.after(
                0,
                messagebox.showerror,
                "Field Test Error",
                f"Field test execution error: {e}",
            )
        finally:
            self.after(0, self._field_test_finished)

    def _update_progress_ui(
        self, current: int, total: int, domain: str, res: LookupResult
    ) -> None:
        """Update progress bar, status text, and insert result row into Treeview."""
        pct = int((current / total) * 100)
        self.progress_bar["value"] = current
        self.progress_lbl.config(
            text=f"● RUNNING EXPERIMENT: {current} / {total} ({pct}%) — Testing: '{domain}'",
            fg=ACCENT_BLUE,
        )

        loc_str = (
            f"{res.city}, {res.country_code}"
            if res.city != "N/A"
            else res.country
        )
        self.tree.insert(
            "",
            "end",
            values=(
                current,
                domain,
                res.input_type,
                res.selected_ip or "N/A",
                loc_str,
                res.organization,
                f"{res.dns_response_time_ms}ms",
                f"{res.api_response_time_ms}ms",
                res.overall_status.value,
            ),
        )

    def _stop_field_test(self) -> None:
        """Set stop event to halt batch execution."""
        if self.stop_event:
            self.stop_event.set()
            self.progress_lbl.config(
                text="Stopping field test... preserving completed observations.",
                fg=ACCENT_RED,
            )

    def _field_test_finished(self) -> None:
        """Clean up buttons and status when batch experiment finishes or stops."""
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

        if self.stop_event and self.stop_event.is_set():
            self.progress_lbl.config(
                text="Field test stopped. Completed observations saved to data/field_test/field_test_results.csv",
                fg=ACCENT_RED,
            )
        else:
            self.progress_lbl.config(
                text="✔ FIELD TEST COMPLETE (50/50). Research dataset saved to data/field_test/field_test_results.csv",
                fg=ACCENT_GREEN,
            )
