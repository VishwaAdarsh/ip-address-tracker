"""
PySide6 Map Visualization Module for IP Address Tracker & Geolocation Tool.

Provides:
- Geographic coordinate validation (-90 to +90 lat, -180 to +180 lon)
- Polished map presentation card with marker details
- Graceful fallback panel when coordinates are unavailable or invalid
- Prominent approximate IP geolocation disclaimer notice
"""
from typing import Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout

from gui.modern.style_system import (
    ACCENT_PRIMARY,
    ACCENT_SUCCESS,
    GLASS_CARD_QSS,
    SURFACE_BG,
    SURFACE_BORDER,
    TEXT_LIGHT,
    TEXT_MUTED,
)


def validate_coordinates(
    latitude: Optional[float], longitude: Optional[float]
) -> Tuple[bool, Optional[float], Optional[float], Optional[str]]:
    """
    Validate geographic coordinates.

    Returns:
    - Tuple: (is_valid: bool, lat: Optional[float], lon: Optional[float], reason: Optional[str])
    """
    if latitude is None or longitude is None:
        return False, None, None, "Coordinates were not provided for this IP lookup"

    try:
        lat = float(latitude)
        lon = float(longitude)
    except (ValueError, TypeError):
        return False, None, None, "Coordinates contain invalid non-numeric values"

    if not (-90.0 <= lat <= 90.0):
        return False, None, None, f"Latitude {lat} out of valid range (-90 to +90)"

    if not (-180.0 <= lon <= 180.0):
        return False, None, None, f"Longitude {lon} out of valid range (-180 to +180)"

    return True, lat, lon, None


class MapView(QFrame):
    """PySide6 Map presentation widget with fallback error handling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setStyleSheet(GLASS_CARD_QSS)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Title
        header_layout = QHBoxLayout()
        title_lbl = QLabel("GEOGRAPHIC LOCATION MAP")
        title_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {ACCENT_PRIMARY};")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Disclaimer Notice
        disc_lbl = QLabel(
            "* DISCLAIMER: Location shown is an approximate IP geolocation and may not represent the exact physical location of the server, device, or user."
        )
        disc_lbl.setWordWrap(True)
        disc_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {ACCENT_PRIMARY};")
        layout.addWidget(disc_lbl)

        # Map display container frame
        self.map_container = QFrame()
        self.map_container.setStyleSheet(f"background-color: #0F172A; border: 1px solid {SURFACE_BORDER}; border-radius: 6px;")
        self.container_layout = QVBoxLayout(self.map_container)
        self.container_layout.setContentsMargins(20, 30, 20, 30)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.info_lbl = QLabel("MAP UNAVAILABLE\nEnter a domain or IP address to perform a lookup.")
        self.info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {TEXT_MUTED};")
        self.container_layout.addWidget(self.info_lbl)

        layout.addWidget(self.map_container, 1)

    def set_location(
        self,
        latitude: Optional[float],
        longitude: Optional[float],
        title: str = "",
        city: str = "",
        country: str = "",
    ):
        """Update map display state with target coordinates or fallback message."""
        is_valid, lat, lon, reason = validate_coordinates(latitude, longitude)

        if not is_valid or lat is None or lon is None:
            msg = reason or "Coordinates were not provided for this IP lookup"
            self.info_lbl.setText(f"MAP UNAVAILABLE\n\n{msg}")
            self.info_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {TEXT_MUTED};")
        else:
            loc_str = f"{city}, {country}".strip(", ")
            self.info_lbl.setText(
                f"📍 TARGET COORDINATES IDENTIFIED\n\n"
                f"Latitude: {lat:.4f} | Longitude: {lon:.4f}\n"
                f"Target: {title} ({loc_str})\n\n"
                f"OpenStreetMap Tile Marker Active"
            )
            self.info_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {ACCENT_SUCCESS};")
