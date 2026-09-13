"""
GUI Package for IP Address Tracker & Geolocation Tool.

Note: The primary presentation layer of IP PULSE is the modern Stitch Web Application
(frontend/ and api/server.py). The desktop GUI modules in this directory are optional legacy components.
"""
try:
    from gui.main_window import MainWindow
    __all__ = ["MainWindow"]
except ImportError:
    __all__ = []

