"""
Dashboard / Results View Module for IP Address Tracker & Geolocation Tool.

Provides:
- Prominent input section with keyboard Enter trigger support
- Non-blocking background thread execution for network lookups
- Summary cards (IP, Location, Network)
- Detailed Approximate Geolocation and Network Information sections
- Component execution timing metrics
- Polished empty, loading, and error UI states
"""
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from services.lookup_service import LookupResult, LookupStatus, perform_lookup


# Color Palette Definitions (Dark Network Intelligence Theme)
BG_DARK = "#0F172A"       # Deep slate 900
CARD_BG = "#1E293B"       # Slate 800
CARD_BORDER = "#334155"   # Slate 700
ACCENT_BLUE = "#0EA5E9"   # Sky 500
ACCENT_GREEN = "#10B981"  # Emerald 500
ACCENT_RED = "#EF4444"    # Red 500
TEXT_LIGHT = "#F8FAFC"    # Slate 50
TEXT_MUTED = "#94A3B8"    # Slate 400


class ResultsView(tk.Frame):
    """Main Dashboard View for performing lookups and displaying intelligence results."""

    def __init__(
        self, parent: tk.Widget, on_lookup_complete: Optional[Callable[[], None]] = None
    ) -> None:
        super().__init__(parent, bg=BG_DARK)
        self.on_lookup_complete = on_lookup_complete

        # Configure frame weights
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._create_input_section()
        self._create_main_content_area()

        # Display initial empty state
        self._show_empty_state()

    def _create_input_section(self) -> None:
        """Create the top IP/Domain search bar."""
        input_container = tk.Frame(self, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        input_container.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        input_container.columnconfigure(1, weight=1)

        label = tk.Label(
            input_container,
            text="TARGET INTEL:",
            font=("Segoe UI", 10, "bold"),
            fg=ACCENT_BLUE,
            bg=CARD_BG,
        )
        label.grid(row=0, column=0, padx=(15, 10), pady=12)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            input_container,
            textvariable=self.entry_var,
            font=("Consolas", 12),
            bg="#0F172A",
            fg=TEXT_LIGHT,
            insertbackground=TEXT_LIGHT,
            bd=0,
            highlightthickness=1,
            highlightbackground=CARD_BORDER,
            highlightcolor=ACCENT_BLUE,
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=5, pady=8, ipady=6)
        self.entry.bind("<Return>", lambda e: self._start_lookup_thread())

        self.analyze_btn = tk.Button(
            input_container,
            text="ANALYZE",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_BLUE,
            fg="#FFFFFF",
            activebackground="#0284C7",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=20,
            command=self._start_lookup_thread,
        )
        self.analyze_btn.grid(row=0, column=2, padx=(10, 15), pady=8, ipady=6)

    def _create_main_content_area(self) -> None:
        """Create scrollable/container area for results, loading, and empty states."""
        self.content_frame = tk.Frame(self, bg=BG_DARK)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

    def _show_empty_state(self) -> None:
        """Render initial empty dashboard state."""
        self._clear_content_frame()
        empty_frame = tk.Frame(self.content_frame, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        empty_frame.grid(row=0, column=0, sticky="nsew", pady=10)
        empty_frame.columnconfigure(0, weight=1)
        empty_frame.rowconfigure(0, weight=1)

        title = tk.Label(
            empty_frame,
            text="READY FOR INTELLIGENCE LOOKUP",
            font=("Segoe UI", 14, "bold"),
            fg=TEXT_LIGHT,
            bg=CARD_BG,
        )
        title.pack(pady=(80, 10))

        sub = tk.Label(
            empty_frame,
            text="Enter a domain name (e.g., google.com) or public IP address (e.g., 8.8.8.8) above\nto perform automated DNS resolution, geolocation, and network analysis.",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            justify="center",
        )
        sub.pack(pady=(0, 80))

    def _show_loading_state(self) -> None:
        """Render active loading state during background lookup execution."""
        self._clear_content_frame()
        loading_frame = tk.Frame(self.content_frame, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        loading_frame.grid(row=0, column=0, sticky="nsew", pady=10)
        loading_frame.columnconfigure(0, weight=1)
        loading_frame.rowconfigure(0, weight=1)

        title = tk.Label(
            loading_frame,
            text="● ANALYZING NETWORK & GEOLOCATION DATA...",
            font=("Segoe UI", 12, "bold"),
            fg=ACCENT_BLUE,
            bg=CARD_BG,
        )
        title.pack(pady=(100, 10))

        sub = tk.Label(
            loading_frame,
            text="Validating input  ➔  Resolving DNS  ➔  Querying Geolocation API",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        sub.pack(pady=(0, 100))

    def _clear_content_frame(self) -> None:
        """Remove existing child widgets from content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _start_lookup_thread(self) -> None:
        """Trigger non-blocking background lookup thread."""
        target = self.entry_var.get().strip()
        if not target:
            messagebox.showwarning("Input Required", "Please enter a domain or IP address.")
            return

        self.analyze_btn.config(state="disabled")
        self._show_loading_state()

        # Run lookup in daemon background thread to keep GUI responsive
        threading.Thread(target=self._run_lookup_worker, args=(target,), daemon=True).start()

    def _run_lookup_worker(self, target: str) -> None:
        """Worker method executed in background thread."""
        res = perform_lookup(target, save_to_db=True)
        # Schedule GUI update on main thread
        self.after(0, self._render_lookup_result, res)

    def _render_lookup_result(self, res: LookupResult) -> None:
        """Render complete LookupResult in dashboard."""
        self.analyze_btn.config(state="normal")
        self._clear_content_frame()

        if self.on_lookup_complete:
            self.on_lookup_complete()

        # Canvas & Scrollbar for scrollable results
        canvas = tk.Canvas(self.content_frame, bg=BG_DARK, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scroll_window = tk.Frame(canvas, bg=BG_DARK)

        scroll_window.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_window, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        scroll_window.columnconfigure(0, weight=1)

        # 1. Header / Status Bar
        status_bar = tk.Frame(scroll_window, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        status_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        status_bar.columnconfigure(1, weight=1)

        status_color = ACCENT_GREEN if res.overall_status == LookupStatus.SUCCESS else ACCENT_RED
        status_lbl = tk.Label(
            status_bar,
            text=f"● STATUS: {res.overall_status.value}",
            font=("Segoe UI", 11, "bold"),
            fg=status_color,
            bg=CARD_BG,
        )
        status_lbl.grid(row=0, column=0, padx=15, pady=10)

        meta_text = f"Input: '{res.input}' ({res.input_type}) | Timestamp: {res.timestamp[:19]}"
        meta_lbl = tk.Label(
            status_bar,
            text=meta_text,
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        meta_lbl.grid(row=0, column=1, sticky="e", padx=15, pady=10)

        # 2. Summary Cards Frame
        cards_frame = tk.Frame(scroll_window, bg=BG_DARK)
        cards_frame.grid(row=1, column=0, sticky="ew", pady=5)
        for i in range(3):
            cards_frame.columnconfigure(i, weight=1)

        self._create_summary_card(
            cards_frame, 0, "TARGET IP", res.selected_ip or "N/A", f"Version: {res.ip_version}"
        )
        self._create_summary_card(
            cards_frame, 1, "LOCATION", f"{res.city}, {res.country}", f"Region: {res.region} ({res.country_code})"
        )
        self._create_summary_card(
            cards_frame, 2, "NETWORK", res.organization, f"ASN: {res.asn}"
        )

        # 3. Geolocation Section
        geo_sec = self._create_section_frame(scroll_window, 2, "APPROXIMATE IP GEOLOCATION")
        self._add_detail_row(geo_sec, "Country / Code", f"{res.country} ({res.country_code})")
        self._add_detail_row(geo_sec, "Region / State", res.region)
        self._add_detail_row(geo_sec, "City", res.city)
        coords_str = f"Lat {res.latitude}, Lon {res.longitude}" if res.latitude is not None else "N/A"
        self._add_detail_row(geo_sec, "Coordinates", coords_str)
        self._add_detail_row(geo_sec, "Timezone", res.timezone)

        disc_lbl = tk.Label(
            geo_sec,
            text="* Note: IP Geolocation represents network registry associations and is inherently approximate.",
            font=("Segoe UI", 8, "italic"),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        disc_lbl.pack(anchor="w", padx=15, pady=(5, 10))

        # 4. Network Details Section
        net_sec = self._create_section_frame(scroll_window, 3, "NETWORK & INFRASTRUCTURE")
        self._add_detail_row(net_sec, "Organization", res.organization)
        self._add_detail_row(net_sec, "ISP Provider", res.isp)
        self._add_detail_row(net_sec, "Autonomous System", res.asn)
        self._add_detail_row(net_sec, "Resolved IPv4 List", ", ".join(res.ipv4_addresses) if res.ipv4_addresses else "None")
        self._add_detail_row(net_sec, "Resolved IPv6 List", ", ".join(res.ipv6_addresses) if res.ipv6_addresses else "None")

        # 5. Performance Section
        perf_sec = self._create_section_frame(scroll_window, 4, "PERFORMANCE METRICS")
        self._add_detail_row(perf_sec, "DNS Resolution Time", f"{res.dns_response_time_ms} ms (Status: {res.dns_status})")
        self._add_detail_row(perf_sec, "Geolocation API Time", f"{res.api_response_time_ms} ms (Status: {res.geolocation_status})")
        self._add_detail_row(perf_sec, "Total Execution Time", f"{res.total_response_time_ms} ms")

        # Error details if failed
        if res.error_message:
            err_sec = self._create_section_frame(scroll_window, 5, "ERROR DETAILS")
            err_lbl = tk.Label(
                err_sec,
                text=res.error_message,
                font=("Consolas", 10),
                fg=ACCENT_RED,
                bg=CARD_BG,
                justify="left",
                wraplength=700,
            )
            err_lbl.pack(anchor="w", padx=15, pady=10)

    def _create_summary_card(
        self, parent: tk.Widget, col: int, title: str, main_val: str, sub_val: str
    ) -> None:
        """Create a styled summary card."""
        card = tk.Frame(parent, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)

        t_lbl = tk.Label(card, text=title, font=("Segoe UI", 9, "bold"), fg=ACCENT_BLUE, bg=CARD_BG)
        t_lbl.pack(anchor="w", padx=12, pady=(10, 2))

        v_lbl = tk.Label(
            card,
            text=main_val,
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_LIGHT,
            bg=CARD_BG,
            wraplength=220,
            justify="left",
        )
        v_lbl.pack(anchor="w", padx=12, pady=2)

        s_lbl = tk.Label(card, text=sub_val, font=("Segoe UI", 9), fg=TEXT_MUTED, bg=CARD_BG)
        s_lbl.pack(anchor="w", padx=12, pady=(0, 10))

    def _create_section_frame(self, parent: tk.Widget, row: int, title: str) -> tk.Frame:
        """Create a section container frame."""
        sec_frame = tk.Frame(parent, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        sec_frame.grid(row=row, column=0, sticky="ew", pady=8)

        sec_title = tk.Label(
            sec_frame, text=title, font=("Segoe UI", 10, "bold"), fg=ACCENT_BLUE, bg=CARD_BG
        )
        sec_title.pack(anchor="w", padx=15, pady=(10, 5))
        return sec_frame

    def _add_detail_row(self, parent: tk.Frame, label: str, val: str) -> None:
        """Add a label-value pair row inside a section frame."""
        row_frame = tk.Frame(parent, bg=CARD_BG)
        row_frame.pack(fill="x", padx=15, pady=2)

        lbl = tk.Label(row_frame, text=f"{label}:", font=("Segoe UI", 9, "bold"), fg=TEXT_MUTED, bg=CARD_BG, width=22, anchor="w")
        lbl.pack(side="left")

        val_lbl = tk.Label(row_frame, text=val, font=("Segoe UI", 9), fg=TEXT_LIGHT, bg=CARD_BG, anchor="w")
        val_lbl.pack(side="left", fill="x", expand=True)
