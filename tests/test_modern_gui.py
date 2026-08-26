"""
Automated Unit Tests for Modern PySide6 + QFluentWidgets GUI Component Views.
"""
import sys
import unittest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from gui.modern.analytics_view import AnalyticsView
from gui.modern.dashboard_view import DashboardView
from gui.modern.field_project_view import FieldProjectView
from gui.modern.history_view import HistoryView
from gui.modern.main_window import MainWindow
from gui.modern.map_view import MapView, validate_coordinates

# Initialize single QApplication instance for Qt test environment
app = QApplication.instance() or QApplication(sys.argv)


class TestModernGUI(unittest.TestCase):
    """Test suite for PySide6 + QFluentWidgets GUI views."""

    def test_map_coordinate_validation(self):
        """Test coordinate validation helper logic."""
        is_valid, lat, lon, err = validate_coordinates(37.7749, -122.4194)
        self.assertTrue(is_valid)
        self.assertEqual(lat, 37.7749)
        self.assertEqual(lon, -122.4194)

        is_valid_none, _, _, err_none = validate_coordinates(None, None)
        self.assertFalse(is_valid_none)
        self.assertIn("not provided", err_none)

        is_valid_out, _, _, _ = validate_coordinates(120.0, 45.0)
        self.assertFalse(is_valid_out)

    def test_map_view_instantiation(self):
        """Test MapView widget instantiation and location setting."""
        map_w = MapView()
        self.assertIsNotNone(map_w)
        map_w.set_location(37.4225, -122.085, title="google.com", city="Mountain View", country="United States")

    def test_dashboard_view_instantiation(self):
        """Test DashboardView widget initialization."""
        dash = DashboardView()
        self.assertIsNotNone(dash.input_edit)
        self.assertIsNotNone(dash.analyze_btn)

    def test_history_view_instantiation(self):
        """Test HistoryView widget initialization and refresh."""
        hist = HistoryView()
        self.assertIsNotNone(hist.table)
        hist.refresh_history()

    def test_field_project_view_instantiation(self):
        """Test FieldProjectView widget initialization and refresh."""
        fp = FieldProjectView()
        self.assertIsNotNone(fp.card_available)
        fp.refresh_status()

    def test_analytics_view_instantiation(self):
        """Test AnalyticsView widget initialization and refresh."""
        an = AnalyticsView()
        self.assertIsNotNone(an.card_obs)
        an.refresh_analysis()

    def test_main_window_instantiation(self):
        """Test PySide6 MainWindow application shell."""
        win = MainWindow()
        self.assertIn("IP PULSE", win.windowTitle())
        self.assertIsNotNone(win.dashboard_view)
        self.assertIsNotNone(win.history_view)
        self.assertIsNotNone(win.field_project_view)
        self.assertIsNotNone(win.analytics_view)


if __name__ == "__main__":
    unittest.main()
