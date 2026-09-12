"""
IP Address Tracker & Geolocation Tool
Main Application Entry Point (PySide6 + QFluentWidgets Integration)
"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from database.db import init_db


def main() -> None:
    # Initialize SQLite database schema
    init_db()

    # Check for legacy GUI flag
    if "--legacy" in sys.argv:
        from gui.legacy.main_window import MainWindow as LegacyWindow
        app = LegacyWindow()
        app.mainloop()
        return

    # Launch PySide6 + QFluentWidgets GUI Application
    app = QApplication(sys.argv)
    
    # Enable high-DPI scaling
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    from gui.modern.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
