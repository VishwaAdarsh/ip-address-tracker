"""
Map Visualization View Module for IP Address Tracker & Geolocation Tool.

Provides:
- Coordinate validation logic for Latitude (-90 to +90) and Longitude (-180 to +180)
- Interactive OpenStreetMap rendering via tkintermapview
- Fallback UI states for missing coordinates, invalid values, or network loading failures
- Prominent approximate-location disclaimer notice
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Try importing tkintermapview; handle gracefully if uninstalled or failing
try:
    import tkintermapview

    HAS_MAPVIEW = True
except ImportError:
    HAS_MAPVIEW = False

# Palette constants
BG_DARK = "#0F172A"       # Deep slate 900
CARD_BG = "#1E293B"       # Slate 800
CARD_BORDER = "#334155"   # Slate 700
ACCENT_BLUE = "#0EA5E9"   # Sky 500
ACCENT_RED = "#EF4444"    # Red 500
TEXT_LIGHT = "#F8FAFC"    # Slate 50
TEXT_MUTED = "#94A3B8"    # Slate 400


def validate_coordinates(
    lat: Any, lon: Any
) -> Tuple[bool, Optional[float], Optional[float], Optional[str]]:
    """
    Validate latitude and longitude values.

    Returns:
    - (is_valid, latitude_float, longitude_float, error_message)
    Valid Ranges:
    - Latitude: -90.0 to +90.0
    - Longitude: -180.0 to +180.0
    """
    if lat is None or lon is None or lat == "" or lon == "":
        return False, None, None, "Coordinates were not provided for this IP lookup"

    try:
        lat_float = float(lat)
        lon_float = float(lon)
    except (ValueError, TypeError):
        return False, None, None, "Invalid non-numeric coordinate format"

    if not (-90.0 <= lat_float <= 90.0):
        return (
            False,
            None,
            None,
            f"Latitude '{lat_float}' out of valid range (-90 to +90)",
        )

    if not (-180.0 <= lon_float <= 180.0):
        return (
            False,
            None,
            None,
            f"Longitude '{lon_float}' out of valid range (-180 to +180)",
        )

    return True, lat_float, lon_float, None


class MapView(tk.Frame):
    """Component for displaying geographic OpenStreetMap tile visualization with markers."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, bg=BG_DARK)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.map_widget: Optional[Any] = None
        self.current_marker: Optional[Any] = None

        self._create_disclaimer_header()
        self._create_map_container()

    def _create_disclaimer_header(self) -> None:
        """Create header displaying required approximate location disclaimer."""
        header_frame = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.columnconfigure(0, weight=1)

        disc_lbl = tk.Label(
            header_frame,
            text="* DISCLAIMER: Location shown is an approximate IP geolocation and may not represent the exact physical location of the server, device, or user.",
            font=("Segoe UI", 8.5, "bold"),
            fg=ACCENT_BLUE,
            bg=CARD_BG,
            anchor="w",
        )
        disc_lbl.pack(padx=12, pady=8, fill="x")

    def _create_map_container(self) -> None:
        """Create main container for map widget or fallback states."""
        self.map_container = tk.Frame(
            self,
            bg=BG_DARK,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        self.map_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.map_container.columnconfigure(0, weight=1)
        self.map_container.rowconfigure(0, weight=1)

        self._show_empty_map_state("READY FOR MAP VISUALIZATION\nPerform a lookup to display geographic coordinates.")

    def set_location(
        self,
        lat: Any,
        lon: Any,
        target_label: str = "",
        city: str = "N/A",
        country: str = "N/A",
    ) -> None:
        """
        Set and render map location for valid coordinates.

        - Validates coordinates.
        - Displays map marker if valid.
        - Displays graceful error/empty state if missing or invalid.
        """
        is_valid, lat_val, lon_val, err_msg = validate_coordinates(lat, lon)

        if not is_valid or lat_val is None or lon_val is None:
            self._show_empty_map_state(f"MAP UNAVAILABLE\n{err_msg or 'No coordinates available'}")
            return

        if not HAS_MAPVIEW:
            self._show_empty_map_state(
                f"MAP COMPONENT UNLOADED\nCoordinates: Lat {lat_val}, Lon {lon_val}\n(tkintermapview package not available)"
            )
            return

        # Clear existing container
        self._clear_map_container()

        try:
            # Instantiate TkinterMapView
            self.map_widget = tkintermapview.TkinterMapView(
                self.map_container, corner_radius=0
            )
            self.map_widget.pack(fill="both", expand=True)

            # Set position & zoom
            self.map_widget.set_position(lat_val, lon_val)
            self.map_widget.set_zoom(10)

            # Set marker
            marker_text = f"Approximate IP Location: {city}, {country}"
            if target_label:
                marker_text = f"[{target_label}] {marker_text}"

            self.current_marker = self.map_widget.set_marker(
                lat_val, lon_val, text=marker_text
            )

        except Exception as e:
            logger.error(f"Failed to render OpenStreetMap: {e}")
            self._show_empty_map_state(
                f"UNABLE TO LOAD MAP\n{str(e)}\n\nCoordinates: Lat {lat_val}, Lon {lon_val}"
            )

    def _show_empty_map_state(self, message: str) -> None:
        """Render fallback message when map is unavailable or unpopulated."""
        self._clear_map_container()

        fallback_frame = tk.Frame(
            self.map_container,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        fallback_frame.pack(fill="both", expand=True, padx=5, pady=5)
        fallback_frame.columnconfigure(0, weight=1)
        fallback_frame.rowconfigure(0, weight=1)

        msg_lbl = tk.Label(
            fallback_frame,
            text=message,
            font=("Segoe UI", 11, "bold"),
            fg=TEXT_MUTED,
            bg=CARD_BG,
            justify="center",
        )
        msg_lbl.pack(expand=True, padx=20, pady=40)

    def _clear_map_container(self) -> None:
        """Destroy widgets inside map container."""
        if self.map_widget:
            try:
                self.map_widget.destroy()
            except Exception:
                pass
            self.map_widget = None

        for widget in self.map_container.winfo_children():
            widget.destroy()
