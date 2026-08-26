"""
PySide6 History View Module for IP Address Tracker & Geolocation Tool.

Provides:
- QTableWidget logging past lookups stored in SQLite database (data/ip_tracker.db)
- Details inspection pane displaying selected lookup metadata
- Controls for manual refresh, single record deletion, and clearing history
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import PrimaryPushButton, PushButton, TableWidget

from database.db import clear_history, delete_lookup, get_lookup_history
from database.models import LookupRecord
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


class HistoryView(QWidget):
    """Modern PySide6 History view module."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

        # Load initial database records
        self.refresh_history()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header bar with title and action buttons
        header_card = QFrame()
        header_card.setObjectName("GlassCard")
        header_card.setStyleSheet(GLASS_CARD_QSS)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 10, 16, 10)

        title_lbl = QLabel("PERSISTENT LOOKUP HISTORY")
        title_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {ACCENT_PRIMARY};")
        header_layout.addWidget(title_lbl)

        header_layout.addStretch()

        self.btn_refresh = PushButton("REFRESH")
        self.btn_refresh.setStyleSheet(f"background-color: {SURFACE_BG}; color: {TEXT_LIGHT}; border: 1px solid {SURFACE_BORDER}; border-radius: 6px; padding: 4px 14px;")
        self.btn_refresh.clicked.connect(self.refresh_history)
        header_layout.addWidget(self.btn_refresh)

        self.btn_delete = PushButton("DELETE SELECTED")
        self.btn_delete.setStyleSheet(f"background-color: {SURFACE_BG}; color: {TEXT_LIGHT}; border: 1px solid {SURFACE_BORDER}; border-radius: 6px; padding: 4px 14px;")
        self.btn_delete.clicked.connect(self._delete_selected)
        header_layout.addWidget(self.btn_delete)

        self.btn_clear = PrimaryPushButton("CLEAR HISTORY")
        self.btn_clear.setStyleSheet(f"background-color: {ACCENT_ERROR}; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 4px 14px;")
        self.btn_clear.clicked.connect(self._clear_all)
        header_layout.addWidget(self.btn_clear)

        layout.addWidget(header_card)

        # History Table Widget
        table_card = QFrame()
        table_card.setObjectName("GlassCard")
        table_card.setStyleSheet(GLASS_CARD_QSS)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)

        self.table = TableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "TIMESTAMP", "INPUT", "TYPE", "IP ADDRESS", "LOCATION", "ORGANIZATION", "STATUS"
        ])
        self.table.verticalHeader().hide()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {SURFACE_BG};
                color: {TEXT_LIGHT};
                gridline-color: {SURFACE_BORDER};
                border: none;
            }}
            QHeaderView::section {{
                background-color: #0284C7;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                padding: 6px;
                border: none;
            }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)

        # Inspection Details Pane
        details_card = QFrame()
        details_card.setObjectName("GlassCard")
        details_card.setStyleSheet(GLASS_CARD_QSS)
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(16, 12, 16, 12)

        det_title = QLabel("INSPECTOR PANE")
        det_title.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {ACCENT_PRIMARY};")
        details_layout.addWidget(det_title)

        self.lbl_details = QLabel("Select a record row in the table above to view full metadata details.")
        self.lbl_details.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        self.lbl_details.setWordWrap(True)
        details_layout.addWidget(self.lbl_details)

        layout.addWidget(details_card)

    def refresh_history(self):
        """Reload records from SQLite database into QTableWidget."""
        records = get_lookup_history()
        self.table.setRowCount(0)

        for rec in records:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            loc = f"{rec.city}, {rec.country}".strip(", ")

            items = [
                QTableWidgetItem(str(rec.id)),
                QTableWidgetItem(rec.timestamp[:19] if rec.timestamp else ""),
                QTableWidgetItem(rec.input_value),
                QTableWidgetItem(rec.input_type),
                QTableWidgetItem(rec.ip_address),
                QTableWidgetItem(loc),
                QTableWidgetItem(rec.organization),
                QTableWidgetItem(rec.status),
            ]

            for col_idx, item in enumerate(items):
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

        self.table.resizeColumnsToContents()

    def _on_selection_changed(self):
        """Update inspection pane when user selects a row in history table."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.lbl_details.setText("Select a record row in the table above to view full metadata details.")
            return

        row = selected_items[0].row()
        rec_id = self.table.item(row, 0).text()
        records = get_lookup_history()
        target_rec = next((r for r in records if str(r.id) == rec_id), None)

        if target_rec:
            self.lbl_details.setText(
                f"Record ID #{target_rec.id} | Input: '{target_rec.input_value}' ({target_rec.input_type})\n"
                f"IP Address: {target_rec.ip_address} ({target_rec.ip_version}) | Location: {target_rec.city}, {target_rec.region}, {target_rec.country} ({target_rec.country_code})\n"
                f"Network: {target_rec.organization} | ISP: {target_rec.isp} | ASN: {target_rec.asn}\n"
                f"Timings: DNS {target_rec.dns_response_time_ms:.1f} ms | Geolocation API {target_rec.api_response_time_ms:.1f} ms\n"
                f"Status: {target_rec.status}"
            )

    def _delete_selected(self):
        """Delete highlighted record from database."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a record in the table to delete.")
            return

        row = selected_items[0].row()
        rec_id = int(self.table.item(row, 0).text())

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete lookup record #{rec_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            delete_lookup(rec_id)
            self.refresh_history()

    def _clear_all(self):
        """Clear all stored lookup records from database."""
        confirm = QMessageBox.question(
            self,
            "Confirm Clear History",
            "Are you sure you want to permanently clear all stored lookup records from history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            clear_history()
            self.refresh_history()
