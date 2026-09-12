"""
PySide6 + QFluentWidgets Main Application Shell for IP PULSE Console.

Provides:
- Modern MSFluentWindow dark application shell
- Top header with status badge (● SYSTEM ONLINE)
- Sidebar navigation for Dashboard, History, Field Project, and Analytics
"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import (
    FluentIcon as FIF,
    MSFluentWindow,
    NavigationItemPosition,
    Theme,
    setTheme,
)

from gui.modern.analytics_view import AnalyticsView
from gui.modern.dashboard_view import DashboardView
from gui.modern.field_project_view import FieldProjectView
from gui.modern.history_view import HistoryView
from gui.modern.style_system import (
    ACCENT_PRIMARY,
    ACCENT_SUCCESS,
    BG_DARK,
    SURFACE_BG,
    SURFACE_BORDER,
    TEXT_LIGHT,
    TEXT_MUTED,
)


class MainWindow(MSFluentWindow):
    """PySide6 + QFluentWidgets main window application shell."""

    def __init__(self):
        super().__init__()
        # Force dark theme globally
        setTheme(Theme.DARK)

        self._init_window()
        self._init_subviews()
        self._init_navigation()

    def _init_window(self):
        self.setWindowTitle("IP PULSE — Network Intelligence Console")
        self.resize(1180, 800)
        self.setMinimumSize(960, 640)

        # Style main window container
        self.setStyleSheet(f"background-color: {BG_DARK}; color: {TEXT_LIGHT};")

    def _init_subviews(self):
        """Instantiate view modules."""
        self.dashboard_view = DashboardView(self)
        self.dashboard_view.setObjectName("dashboard_view")

        self.history_view = HistoryView(self)
        self.history_view.setObjectName("history_view")

        self.field_project_view = FieldProjectView(self)
        self.field_project_view.setObjectName("field_project_view")

        self.analytics_view = AnalyticsView(self)
        self.analytics_view.setObjectName("analytics_view")

    def _init_navigation(self):
        """Configure sidebar navigation items with QFluentWidgets icons."""
        self.addSubInterface(
            self.dashboard_view,
            FIF.SEARCH,
            "Dashboard",
            position=NavigationItemPosition.TOP,
        )

        self.addSubInterface(
            self.history_view,
            FIF.HISTORY,
            "History",
            position=NavigationItemPosition.TOP,
        )

        self.addSubInterface(
            self.field_project_view,
            FIF.DOCUMENT,
            "Field Project",
            position=NavigationItemPosition.TOP,
        )

        self.addSubInterface(
            self.analytics_view,
            FIF.PIE_SINGLE,
            "Analytics",
            position=NavigationItemPosition.TOP,
        )

        # Add header widget to title bar area with status indicator
        self.titleBar.titleLabel.setText("IP PULSE  |  Network Intelligence Console")
        self.titleBar.titleLabel.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {ACCENT_PRIMARY}; padding-left: 10px;"
        )
