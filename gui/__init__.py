"""
GUI Package for IP Address Tracker & Geolocation Tool.

Note: PySide6 GUI is retained for backward-compatibility; the primary presentation
layer is now the Stitch Web Application (frontend/ and api/server.py).
"""
try:
    from gui.modern.main_window import MainWindow
    __all__ = ["MainWindow"]
except ImportError:
    __all__ = []
