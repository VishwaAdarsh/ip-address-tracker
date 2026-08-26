"""
IP Address Tracker & Geolocation Tool
Main Application Entry Point (Phase 7 GUI Integration)
"""
import sys
from database.db import init_db
from gui.main_window import MainWindow


def main() -> None:
    # Initialize SQLite database schema
    init_db()

    # Launch GUI application
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
