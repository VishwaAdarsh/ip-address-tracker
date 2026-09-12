"""
PySide6 QWebEngineView + Leaflet.js Map Widget for IP Address Tracker & Geolocation Tool.

Provides:
- Real interactive geographic map rendering using Leaflet.js and OpenStreetMap tiles
- Interactive marker at target (latitude, longitude) with detailed IP popup
- Zoom (+/-), pan, drag controls, and mandatory OpenStreetMap attribution
- Fallback UI states for missing coordinates (MAP UNAVAILABLE) and network failure
- Preserves mandatory approximate IP geolocation disclaimer
"""
import html
from typing import Optional, Tuple
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFrame, QLabel, QStackedLayout, QVBoxLayout, QWidget

from gui.modern.style_system import (
    ACCENT_ERROR,
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


def generate_leaflet_html(
    lat: float, lon: float, ip_address: str = "", location_name: str = ""
) -> str:
    """Generate controlled Leaflet.js HTML with OpenStreetMap tile layer and marker popup."""
    safe_ip = html.escape(ip_address or "Target IP")
    safe_loc = html.escape(location_name or "Target Location")

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
    <style>
        html, body, #map {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            background-color: #0F172A;
        }}
        .leaflet-container {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .custom-popup .leaflet-popup-content-wrapper {{
            background-color: #1E293B;
            color: #F8FAFC;
            border: 1px solid #0EA5E9;
            border-radius: 8px;
            padding: 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }}
        .custom-popup .leaflet-popup-tip {{
            background-color: #1E293B;
        }}
        .popup-title {{
            color: #0EA5E9;
            font-weight: bold;
            font-size: 13px;
            margin-bottom: 4px;
        }}
        .popup-info {{
            color: #CBD5E1;
            font-size: 11px;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        try {{
            var lat = {lat};
            var lon = {lon};
            var ip = "{safe_ip}";
            var locationName = "{safe_loc}";

            var map = L.map('map', {{
                center: [lat, lon],
                zoom: 12,
                zoomControl: true
            }});

            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors'
            }}).addTo(map);

            var customPopup = `
                <div class="custom-popup">
                    <div class="popup-title">📍 IP: ${{ip}}</div>
                    <div class="popup-info">
                        <b>Location:</b> ${{locationName}}<br>
                        <b>Coordinates:</b> ${{lat.toFixed(4)}}, ${{lon.toFixed(4)}}<br>
                        <span style="color:#10B981;font-weight:bold;">● Geolocation Active</span>
                    </div>
                </div>
            `;

            var marker = L.marker([lat, lon]).addTo(map);
            marker.bindPopup(customPopup).openPopup();
        }} catch(e) {{
            document.body.innerHTML = '<div style="color:#EF4444;padding:20px;text-align:center;font-weight:bold;">Map Loading Exception: ' + e.message + '</div>';
        }}
    </script>
</body>
</html>"""


class MapWidget(QFrame):
    """
    PySide6 Map Component using QWebEngineView + Leaflet.js.
    
    Provides stacked layout to seamlessly switch between:
    1. Real interactive QWebEngineView map display (when coordinates exist)
    2. Fallback info panel (when coordinates are missing or network fails)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setStyleSheet(GLASS_CARD_QSS)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # Header Title
        title_lbl = QLabel("GEOGRAPHIC LOCATION MAP")
        title_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {ACCENT_PRIMARY};")
        main_layout.addWidget(title_lbl)

        # Disclaimer Notice
        disc_lbl = QLabel(
            "* DISCLAIMER: Location shown is an approximate IP geolocation and may not represent the exact physical location of the server, device, or user."
        )
        disc_lbl.setWordWrap(True)
        disc_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {ACCENT_PRIMARY};")
        main_layout.addWidget(disc_lbl)

        # Map display container with stacked layout (0: WebEngineView, 1: Fallback Panel)
        self.container_frame = QFrame()
        self.container_frame.setStyleSheet(
            f"background-color: #0F172A; border: 1px solid {SURFACE_BORDER}; border-radius: 6px;"
        )
        self.stacked_layout = QStackedLayout(self.container_frame)

        # 0. QWebEngineView for Leaflet map
        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("background-color: #0F172A; border-radius: 6px;")
        self.stacked_layout.addWidget(self.web_view)

        # 1. Fallback Info Panel
        self.fallback_widget = QWidget()
        fallback_layout = QVBoxLayout(self.fallback_widget)
        fallback_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_layout.setContentsMargins(20, 40, 20, 40)

        self.fallback_lbl = QLabel("MAP UNAVAILABLE\n\nEnter a domain or IP address to perform a lookup.")
        self.fallback_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fallback_lbl.setWordWrap(True)
        self.fallback_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {TEXT_MUTED};")
        fallback_layout.addWidget(self.fallback_lbl)

        self.stacked_layout.addWidget(self.fallback_widget)

        # Default to fallback view
        self.stacked_layout.setCurrentWidget(self.fallback_widget)

        main_layout.addWidget(self.container_frame, 1)

    def set_location(
        self,
        latitude: Optional[float],
        longitude: Optional[float],
        ip_address: str = "",
        location_name: str = "",
    ):
        """
        Update map display with target coordinates or fallback panel.
        
        Args:
        - latitude: float latitude (-90 to +90)
        - longitude: float longitude (-180 to +180)
        - ip_address: Target IP string for marker popup
        - location_name: City/Country string for marker popup
        """
        is_valid, lat, lon, reason = validate_coordinates(latitude, longitude)

        if not is_valid or lat is None or lon is None:
            msg = reason or "Coordinates were not provided for this IP lookup."
            self.fallback_lbl.setText(f"MAP UNAVAILABLE\n\n{msg}")
            self.fallback_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {TEXT_MUTED};")
            self.stacked_layout.setCurrentWidget(self.fallback_widget)
        else:
            # Generate and load Leaflet HTML into QWebEngineView
            leaflet_html = generate_leaflet_html(
                lat=lat,
                lon=lon,
                ip_address=ip_address,
                location_name=location_name,
            )
            self.web_view.setHtml(leaflet_html, QUrl("https://localhost/"))
            self.stacked_layout.setCurrentWidget(self.web_view)

    def show_map_failure(self):
        """Display MAP CONNECTION UNAVAILABLE error panel."""
        self.fallback_lbl.setText(
            "MAP CONNECTION UNAVAILABLE\n\n"
            "The geographic coordinates were successfully retrieved,\n"
            "but map tiles could not be loaded."
        )
        self.fallback_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {ACCENT_ERROR};")
        self.stacked_layout.setCurrentWidget(self.fallback_widget)
