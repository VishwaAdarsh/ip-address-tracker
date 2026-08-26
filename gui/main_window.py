"""
Main Application Window Module for IP Address Tracker & Geolocation Tool.

Provides:
- Top Header bar ("IP PULSE - Network Intelligence Console", "SYSTEM ONLINE" status badge)
- Slim dark sidebar navigation (Dashboard, History)
- Main container switching between ResultsView and HistoryView
- Clean window geometry management and dark styling
"""
import tkinter as tk
from typing import Optional

from gui.history_view import HistoryView
from gui.results_view import ResultsView

# Palette constants
BG_DARK = "#0F172A"       # Deep slate 900
SIDEBAR_BG = "#1E293B"    # Slate 800
BORDER_COLOR = "#334155"  # Slate 700
ACCENT_BLUE = "#0EA5E9"   # Sky 500
ACCENT_GREEN = "#10B981"  # Emerald 500
TEXT_LIGHT = "#F8FAFC"    # Slate 50
TEXT_MUTED = "#94A3B8"    # Slate 400


class MainWindow(tk.Tk):
    """Main Application Window for IP PULSE Network Intelligence Console."""

    def __init__(self) -> None:
        super().__init__()
        self.title("IP PULSE — Network Intelligence Console")
        self.geometry("1100x740")
        self.minsize(920, 620)
        self.configure(bg=BG_DARK)

        # Configure root layout grid
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self._create_header()
        self._create_sidebar()
        self._create_content_area()

        # Default view: Dashboard
        self.show_dashboard()

    def _create_header(self) -> None:
        """Create application header bar."""
        header_frame = tk.Frame(
            self,
            bg=BG_DARK,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        header_frame.columnconfigure(1, weight=1)

        title_box = tk.Frame(header_frame, bg=BG_DARK)
        title_box.grid(row=0, column=0, padx=20, pady=12, sticky="w")

        title_lbl = tk.Label(
            title_box,
            text="IP PULSE",
            font=("Segoe UI", 14, "bold"),
            fg=ACCENT_BLUE,
            bg=BG_DARK,
        )
        title_lbl.pack(side="left")

        sub_lbl = tk.Label(
            title_box,
            text="  |  Network Intelligence Console",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=BG_DARK,
        )
        sub_lbl.pack(side="left")

        status_lbl = tk.Label(
            header_frame,
            text="● SYSTEM ONLINE",
            font=("Segoe UI", 9, "bold"),
            fg=ACCENT_GREEN,
            bg=BG_DARK,
        )
        status_lbl.grid(row=0, column=1, sticky="e", padx=20, pady=12)

    def _create_sidebar(self) -> None:
        """Create slim left sidebar navigation."""
        sidebar_frame = tk.Frame(
            self,
            bg=SIDEBAR_BG,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
            width=180,
        )
        sidebar_frame.grid(row=1, column=0, sticky="nsew")
        sidebar_frame.pack_propagate(False)

        nav_title = tk.Label(
            sidebar_frame,
            text="NAVIGATION",
            font=("Segoe UI", 8, "bold"),
            fg=TEXT_MUTED,
            bg=SIDEBAR_BG,
        )
        nav_title.pack(anchor="w", padx=20, pady=(20, 10))

        self.dash_btn = tk.Button(
            sidebar_frame,
            text="DASHBOARD",
            font=("Segoe UI", 9, "bold"),
            bg=ACCENT_BLUE,
            fg="#FFFFFF",
            activebackground="#0284C7",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            anchor="w",
            padx=15,
            pady=8,
            command=self.show_dashboard,
        )
        self.dash_btn.pack(fill="x", padx=10, pady=4)

        self.hist_btn = tk.Button(
            sidebar_frame,
            text="HISTORY",
            font=("Segoe UI", 9, "bold"),
            bg=SIDEBAR_BG,
            fg=TEXT_LIGHT,
            activebackground="#334155",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            anchor="w",
            padx=15,
            pady=8,
            command=self.show_history,
        )
        self.hist_btn.pack(fill="x", padx=10, pady=4)

    def _create_content_area(self) -> None:
        """Create container frame housing views."""
        self.content_container = tk.Frame(self, bg=BG_DARK)
        self.content_container.grid(row=1, column=1, sticky="nsew")
        self.content_container.columnconfigure(0, weight=1)
        self.content_container.rowconfigure(0, weight=1)

        # Instantiate view modules
        self.results_view = ResultsView(
            self.content_container, on_lookup_complete=self._on_lookup_complete
        )
        self.history_view = HistoryView(self.content_container)

    def show_dashboard(self) -> None:
        """Switch view to Dashboard."""
        self.history_view.grid_forget()
        self.results_view.grid(row=0, column=0, sticky="nsew")
        self._update_nav_buttons(active="dashboard")

    def show_history(self) -> None:
        """Switch view to History."""
        self.results_view.grid_forget()
        self.history_view.refresh_history()
        self.history_view.grid(row=0, column=0, sticky="nsew")
        self._update_nav_buttons(active="history")

    def _update_nav_buttons(self, active: str) -> None:
        """Highlight active sidebar navigation button."""
        if active == "dashboard":
            self.dash_btn.config(bg=ACCENT_BLUE, fg="#FFFFFF")
            self.hist_btn.config(bg=SIDEBAR_BG, fg=TEXT_LIGHT)
        else:
            self.dash_btn.config(bg=SIDEBAR_BG, fg=TEXT_LIGHT)
            self.hist_btn.config(bg=ACCENT_BLUE, fg="#FFFFFF")

    def _on_lookup_complete(self) -> None:
        """Callback triggered when a lookup completes to update history data."""
        if hasattr(self, "history_view"):
            self.history_view.refresh_history()


def main() -> None:
    """Launch the main GUI application loop."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
