"""
PySide6 Map Visualization View for IP Address Tracker & Geolocation Tool.

Integrates real QWebEngineView + Leaflet.js map component.
"""
from gui.modern.widgets.map_widget import MapWidget, validate_coordinates


class MapView(MapWidget):
    """
    MapView class wrapping MapWidget.
    
    Provides set_location(latitude, longitude, title, city, country)
    and set_location(latitude, longitude, ip_address, location_name) interfaces.
    """

    def set_location(
        self,
        latitude,
        longitude,
        title="",
        city="",
        country="",
        ip_address="",
        location_name="",
    ):
        target_ip = ip_address or title
        target_loc = location_name or f"{city}, {country}".strip(", ")

        super().set_location(
            latitude=latitude,
            longitude=longitude,
            ip_address=target_ip,
            location_name=target_loc,
        )
