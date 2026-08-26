"""
PySide6 Field Project View Module for IP Address Tracker & Geolocation Tool.

Implements the Manual-First Field Project Interface:
- Displays available observations loaded from SQLite Lookup History (N / 50).
- Shows Manual Observations, Remaining count, and Target Status.
- Provides REFRESH FROM HISTORY control.
- Provides optional COMPLETE REMAINING N AUTOMATICALLY button (only active when N < 50).
- Displays live progress bar and table during controlled automatic completion via QThread.
"""
from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import PrimaryPushButton, PushButton, TableWidget

from gui.modern.style_system import (
    ACCENT_ERROR,
    ACCENT_PRIMARY,
    ACCENT_SUCCESS,
    ACCENT_WARNING,
    GLASS_CARD_QSS,
    SURFACE_BG,
    SURFACE_BORDER,
    TEXT_LIGHT,
    TEXT_MUTED,
)
from services.field_test_service import (
    export_field_dataset_from_history,
    get_default_output_path,
    get_field_project_status,
    run_automatic_completion,
)
from services.lookup_service import LookupResult


class AutoCompletionWorker(QObject):
    """Background QThread worker for executing automatic field completion."""

    progress = Signal(int, int, str, object)
    finished = Signal()

    def __init__(self, remaining_needed: int):
        super().__init__()
        self.remaining_needed = remaining_needed

    def run(self):
        def _cb(curr, tot, domain, res):
            self.progress.emit(curr, tot, domain, res)

        try:
            run_automatic_completion(
                progress_callback=_cb,
                delay_seconds=0.5,
            )
        except Exception as e:
            pass
        finally:
            self.finished.emit()


class FieldProjectView(QWidget):
    """Modern PySide6 Field Project view module."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_data = {}
        self._init_ui()

        # Load initial status from History
        self.refresh_status()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header bar
        header_card = QFrame()
        header_card.setObjectName("GlassCard")
        header_card.setStyleSheet(GLASS_CARD_QSS)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)

        title_lbl = QLabel("FIELD PROJECT — 50-WEBSITE DATA COLLECTION")
        title_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {ACCENT_PRIMARY};")
        header_layout.addWidget(title_lbl)

        banner_lbl = QLabel(
            "* MANUAL-FIRST METHODOLOGY: Normal lookups executed on Dashboard are automatically collected in History for this field project."
        )
        banner_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {TEXT_MUTED};")
        header_layout.addWidget(banner_lbl)

        layout.addWidget(header_card)

        # 4 Stat Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_available = self._create_stat_card("AVAILABLE OBSERVATIONS", "0 / 50", "History Records")
        self.card_manual = self._create_stat_card("MANUAL OBSERVATIONS", "0", "Dashboard Lookups")
        self.card_remaining = self._create_stat_card("REMAINING", "50", "Needed for Target")
        self.card_status = self._create_stat_card("STATUS", "INCOMPLETE", "Target: 50 Sites")

        stats_layout.addWidget(self.card_available)
        stats_layout.addWidget(self.card_manual)
        stats_layout.addWidget(self.card_remaining)
        stats_layout.addWidget(self.card_status)
        layout.addLayout(stats_layout)

        # Controls Bar
        btn_layout = QHBoxLayout()

        self.btn_refresh = PushButton("REFRESH FROM HISTORY")
        self.btn_refresh.setStyleSheet(f"background-color: {SURFACE_BG}; color: {TEXT_LIGHT}; border: 1px solid {SURFACE_BORDER}; border-radius: 6px; padding: 6px 14px;")
        self.btn_refresh.clicked.connect(self.refresh_status)
        btn_layout.addWidget(self.btn_refresh)

        self.btn_auto = PrimaryPushButton("COMPLETE REMAINING AUTOMATICALLY")
        self.btn_auto.setStyleSheet(f"background-color: {ACCENT_PRIMARY}; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 6px 16px;")
        self.btn_auto.clicked.connect(self._start_automatic_completion)
        btn_layout.addWidget(self.btn_auto)

        self.btn_view_data = PushButton("VIEW FIELD DATA")
        self.btn_view_data.setStyleSheet(f"background-color: {SURFACE_BG}; color: {TEXT_LIGHT}; border: 1px solid {SURFACE_BORDER}; border-radius: 6px; padding: 6px 14px;")
        self.btn_view_data.clicked.connect(self._view_field_dataset)
        btn_layout.addWidget(self.btn_view_data)

        self.progress_lbl = QLabel("")
        self.progress_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {ACCENT_WARNING};")
        btn_layout.addWidget(self.progress_lbl)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {SURFACE_BORDER};
                border-radius: 4px;
                background-color: #0F172A;
                text-align: center;
                color: {TEXT_LIGHT};
                font-weight: bold;
                height: 16px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT_PRIMARY};
                border-radius: 3px;
            }}
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Observations Table
        table_card = QFrame()
        table_card.setObjectName("GlassCard")
        table_card.setStyleSheet(GLASS_CARD_QSS)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)

        self.table = TableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "#", "DOMAIN", "TYPE", "SELECTED IP", "COUNTRY", "DNS (ms)", "API (ms)", "STATUS"
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

        table_layout.addWidget(self.table)
        layout.addWidget(table_card, 1)

    def _create_stat_card(self, title: str, main_val: str, sub_val: str) -> QFrame:
        """Create styled stat card frame."""
        card = QFrame()
        card.setObjectName("GlassCard")
        card.setStyleSheet(GLASS_CARD_QSS)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {ACCENT_PRIMARY};")
        layout.addWidget(t_lbl)

        v_lbl = QLabel(main_val)
        v_lbl.setObjectName("main_val")
        v_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {TEXT_LIGHT};")
        layout.addWidget(v_lbl)

        s_lbl = QLabel(sub_val)
        s_lbl.setObjectName("sub_val")
        s_lbl.setStyleSheet(f"font-size: 10px; color: {TEXT_MUTED};")
        layout.addWidget(s_lbl)

        return card

    def refresh_status(self):
        """Query SQLite History and update UI cards and observation data."""
        self.status_data = get_field_project_status()

        avail = self.status_data["available_count"]
        rem = self.status_data["remaining"]
        st = self.status_data["status"]

        self._update_card_val(self.card_available, f"{avail} / 50")
        self._update_card_val(self.card_manual, str(avail))
        self._update_card_val(self.card_remaining, str(rem))

        st_lbl = self.card_status.findChild(QLabel, "main_val")
        if st == "TARGET_REACHED":
            if st_lbl:
                st_lbl.setText("TARGET REACHED ✓")
                st_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {ACCENT_SUCCESS};")
            self.btn_auto.setEnabled(False)
            self.btn_auto.setText("TARGET COMPLETED ✓")
        else:
            if st_lbl:
                st_lbl.setText("INCOMPLETE")
                st_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {ACCENT_WARNING};")
            self.btn_auto.setEnabled(True)
            self.btn_auto.setText(f"COMPLETE REMAINING {rem} AUTOMATICALLY")

        self._populate_table(self.status_data["unique_records"])

    def _update_card_val(self, card: QFrame, val: str):
        lbl = card.findChild(QLabel, "main_val")
        if lbl:
            lbl.setText(val)

    def _populate_table(self, records: list):
        """Populate QTableWidget with field records."""
        self.table.setRowCount(0)

        for idx, rec in enumerate(records[:50], start=1):
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            domain = rec.domain or rec.input_value

            items = [
                QTableWidgetItem(str(idx)),
                QTableWidgetItem(domain),
                QTableWidgetItem(rec.input_type or "DOMAIN"),
                QTableWidgetItem(rec.ip_address or "N/A"),
                QTableWidgetItem(rec.country or "N/A"),
                QTableWidgetItem(f"{rec.dns_response_time_ms:.1f}"),
                QTableWidgetItem(f"{rec.api_response_time_ms:.1f}"),
                QTableWidgetItem(rec.status),
            ]

            for col_idx, item in enumerate(items):
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

    def _start_automatic_completion(self):
        """Start automatic completion via background QThread."""
        rem = self.status_data.get("remaining", 0)
        if rem <= 0:
            QMessageBox.information(self, "Target Reached", "The 50-observation field project target is already completed.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Automatic Completion",
            f"You have {self.status_data['available_count']} valid observations in History.\n\n"
            f"Would you like to automatically complete the remaining {rem} website lookups to reach the 50-observation target?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.btn_auto.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(rem)

        self.thread = QThread()
        self.worker = AutoCompletionWorker(rem)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_auto_progress)
        self.worker.finished.connect(self._on_auto_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _on_auto_progress(self, curr: int, tot: int, domain: str, res: LookupResult):
        self.progress_bar.setValue(curr)
        self.progress_lbl.setText(f"Running Auto Completion: {curr}/{tot} ({domain})")
        self.refresh_status()

    def _on_auto_finished(self):
        self.btn_refresh.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_lbl.setText("Automatic completion finished.")
        export_field_dataset_from_history()
        self.refresh_status()
        QMessageBox.information(self, "Field Project Complete", "Field project observations updated and saved successfully.")

    def _view_field_dataset(self):
        export_field_dataset_from_history()
        self.refresh_status()
        out_p = get_default_output_path()
        QMessageBox.information(
            self,
            "Field Dataset Exported",
            f"Field project dataset exported to:\n{out_p}\n\nTotal observations: {self.status_data['available_count']}",
        )
