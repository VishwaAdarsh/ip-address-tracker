"""
Analytics & Research Dashboard GUI View Module for IP Address Tracker & Geolocation Tool.

Provides:
- Key Performance Indicator (KPI) summary cards (Records, Success Rate, Median Lookup Time, Unique Countries)
- Performance metrics descriptive statistics table (DNS, API, Total execution times)
- Interactive chart image preview gallery displaying generated research plots
"""
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Optional

from PIL import Image, ImageTk

from analysis.report_generator import generate_analysis_outputs

# Palette constants
BG_DARK = "#0F172A"       # Deep slate 900
CARD_BG = "#1E293B"       # Slate 800
CARD_BORDER = "#334155"   # Slate 700
ACCENT_BLUE = "#0EA5E9"   # Sky 500
ACCENT_GREEN = "#10B981"  # Emerald 500
ACCENT_PURPLE = "#8B5CF6" # Purple 500
TEXT_LIGHT = "#F8FAFC"    # Slate 50
TEXT_MUTED = "#94A3B8"    # Slate 400


class AnalyticsView(tk.Frame):
    """View module for displaying research analytics, statistics, and charts."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, bg=BG_DARK)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.analysis_data: Dict = {}
        self.chart_image_tk: Optional[ImageTk.PhotoImage] = None

        self._create_header()
        self._create_main_content()

        # Load initial analysis
        self.refresh_analysis()

    def _create_header(self) -> None:
        """Create analytics header and refresh button bar."""
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
            text="FIELD STUDY ANALYTICS & RESEARCH FINDINGS",
            font=("Segoe UI", 11, "bold"),
            fg=ACCENT_BLUE,
            bg=CARD_BG,
        )
        title.grid(row=0, column=0, padx=15, pady=12)

        refresh_btn = tk.Button(
            header_frame,
            text="RE-RUN ANALYSIS",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_BLUE,
            fg="#FFFFFF",
            activebackground="#0284C7",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=15,
            pady=5,
            command=self.refresh_analysis,
        )
        refresh_btn.grid(row=0, column=2, padx=15, pady=8)

    def _create_main_content(self) -> None:
        """Create container area housing KPI cards, table, and chart preview."""
        self.content_container = tk.Frame(self, bg=BG_DARK)
        self.content_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=5)
        self.content_container.columnconfigure(0, weight=1)
        self.content_container.rowconfigure(0, weight=1)

    def refresh_analysis(self) -> None:
        """Run analysis engine and render outputs in GUI."""
        for w in self.content_container.winfo_children():
            w.destroy()

        try:
            self.analysis_data = generate_analysis_outputs()
            self._render_dashboard()
        except FileNotFoundError:
            self._render_empty_state("NO FIELD TEST DATASET FOUND\nRun a 50-website field test in the FIELD TEST tab first.")
        except Exception as e:
            self._render_empty_state(f"ANALYSIS ERROR\n{str(e)}")

    def _render_empty_state(self, message: str) -> None:
        """Render placeholder message when analysis data is unavailable."""
        empty_frame = tk.Frame(
            self.content_container,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        empty_frame.grid(row=0, column=0, sticky="nsew", pady=10)
        empty_frame.columnconfigure(0, weight=1)
        empty_frame.rowconfigure(0, weight=1)

        msg_lbl = tk.Label(
            empty_frame,
            text=message,
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            justify="center",
        )
        msg_lbl.pack(expand=True, padx=40, pady=80)

    def _render_dashboard(self) -> None:
        """Render complete analytics dashboard."""
        canvas = tk.Canvas(self.content_container, bg=BG_DARK, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", command=canvas.yview)
        scroll_window = tk.Frame(canvas, bg=BG_DARK)

        scroll_window.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_window, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        scroll_window.columnconfigure(0, weight=1)

        # 1. KPI Cards Frame
        kpi_frame = tk.Frame(scroll_window, bg=BG_DARK)
        kpi_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for i in range(4):
            kpi_frame.columnconfigure(i, weight=1)

        rec_cnt = self.analysis_data.get("record_count", 0)
        succ_rate = self.analysis_data.get("success_rate", 0.0)
        desc_stats = self.analysis_data.get("descriptive_stats", {})
        tot_med = desc_stats.get("total_response_time_ms", {}).get("median", 0.0)
        c_dist = self.analysis_data.get("distributions", {}).get("country_distribution", {})

        self._create_kpi_card(kpi_frame, 0, "OBSERVATIONS", f"{rec_cnt} Sites", "Sample Size")
        self._create_kpi_card(kpi_frame, 1, "SUCCESS RATE", f"{succ_rate}%", "Pipeline Reliability")
        self._create_kpi_card(kpi_frame, 2, "MEDIAN TIME", f"{tot_med} ms", "Total Lookup Latency")
        self._create_kpi_card(kpi_frame, 3, "COUNTRIES", f"{len(c_dist)} Countries", "Geographic Spread")

        # 2. Timing Metrics Table Section
        sec_table = tk.Frame(scroll_window, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        sec_table.grid(row=1, column=0, sticky="ew", pady=10)

        t_lbl = tk.Label(sec_table, text="DESCRIPTIVE PERFORMANCE METRICS (ms)", font=("Segoe UI", 10, "bold"), fg=ACCENT_BLUE, bg=CARD_BG)
        t_lbl.pack(anchor="w", padx=15, pady=(10, 5))

        tree = ttk.Treeview(
            sec_table,
            columns=("metric", "cnt", "mean", "std", "min", "p25", "median", "p75", "max", "iqr"),
            show="headings",
            style="FieldTest.Treeview",
            height=4,
        )
        tree.heading("metric", text="METRIC")
        tree.heading("cnt", text="COUNT")
        tree.heading("mean", text="MEAN")
        tree.heading("std", text="STD DEV")
        tree.heading("min", text="MIN")
        tree.heading("p25", text="P25")
        tree.heading("median", text="MEDIAN")
        tree.heading("p75", text="P75")
        tree.heading("max", text="MAX")
        tree.heading("iqr", text="IQR")

        tree.column("metric", width=140, anchor="w")
        for c in ("cnt", "mean", "std", "min", "p25", "median", "p75", "max", "iqr"):
            tree.column(c, width=70, anchor="center")

        for metric_name, s in desc_stats.items():
            tree.insert("", "end", values=(
                metric_name.replace("_response_time_ms", "").upper(),
                s["count"], s["mean"], s["std"], s["min"], s["p25"], s["median"], s["p75"], s["max"], s["iqr"]
            ))
        tree.pack(fill="x", padx=15, pady=(0, 15))

        # 3. Chart Viewer Section
        chart_sec = tk.Frame(scroll_window, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        chart_sec.grid(row=2, column=0, sticky="ew", pady=10)

        c_header = tk.Frame(chart_sec, bg=CARD_BG)
        c_header.pack(fill="x", padx=15, pady=10)

        c_title = tk.Label(c_header, text="RESEARCH CHART GALLERY", font=("Segoe UI", 10, "bold"), fg=ACCENT_BLUE, bg=CARD_BG)
        c_title.pack(side="left")

        chart_paths = self.analysis_data.get("chart_paths", [])
        if chart_paths:
            self.chart_var = tk.StringVar(value=chart_paths[0])
            self.chart_combo = ttk.Combobox(
                c_header,
                textvariable=self.chart_var,
                values=chart_paths,
                state="readonly",
                width=45,
            )
            self.chart_combo.pack(side="right")
            self.chart_combo.bind("<<ComboboxSelected>>", lambda e: self._display_selected_chart())

            self.chart_canvas_frame = tk.Frame(chart_sec, bg=BG_DARK)
            self.chart_canvas_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

            self.chart_label = tk.Label(self.chart_canvas_frame, bg=BG_DARK)
            self.chart_label.pack(expand=True, pady=10)

            self._display_selected_chart()

    def _create_kpi_card(
        self, parent: tk.Widget, col: int, title: str, val: str, sub: str
    ) -> None:
        """Create styled KPI card."""
        card = tk.Frame(parent, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)

        t_lbl = tk.Label(card, text=title, font=("Segoe UI", 8.5, "bold"), fg=ACCENT_BLUE, bg=CARD_BG)
        t_lbl.pack(anchor="w", padx=12, pady=(10, 2))

        v_lbl = tk.Label(card, text=val, font=("Segoe UI", 13, "bold"), fg=TEXT_LIGHT, bg=CARD_BG)
        v_lbl.pack(anchor="w", padx=12, pady=2)

        s_lbl = tk.Label(card, text=sub, font=("Segoe UI", 8.5), fg=TEXT_MUTED, bg=CARD_BG)
        s_lbl.pack(anchor="w", padx=12, pady=(0, 10))

    def _display_selected_chart(self) -> None:
        """Display selected chart image inside Tkinter Label widget."""
        path_str = self.chart_var.get()
        if not path_str:
            return

        try:
            img = Image.open(path_str)
            img.thumbnail((720, 360))
            self.chart_image_tk = ImageTk.PhotoImage(img)
            self.chart_label.config(image=self.chart_image_tk)
        except Exception as e:
            self.chart_label.config(text=f"Failed to load chart image: {e}", fg=TEXT_MUTED)
