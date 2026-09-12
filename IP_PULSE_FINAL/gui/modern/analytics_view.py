"""
PySide6 Analytics View Module for IP Address Tracker & Geolocation Tool.

Provides:
- Key Performance Indicator (KPI) summary cards (Records, Success Rate, Median Lookup Time, Unique Countries)
- Performance metrics descriptive statistics table (DNS, API, Total execution times)
- Interactive chart image preview gallery displaying generated research plots
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import ComboBox, PrimaryPushButton, TableWidget

from analysis.report_generator import generate_analysis_outputs
from gui.modern.style_system import (
    ACCENT_PRIMARY,
    ACCENT_SUCCESS,
    GLASS_CARD_QSS,
    SURFACE_BG,
    SURFACE_BORDER,
    TEXT_LIGHT,
    TEXT_MUTED,
)


class AnalyticsView(QWidget):
    """Modern PySide6 Analytics view module."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_data = {}
        self._init_ui()

        # Load initial analysis outputs
        self.refresh_analysis()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header bar
        header_card = QFrame()
        header_card.setObjectName("GlassCard")
        header_card.setStyleSheet(GLASS_CARD_QSS)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 10, 16, 10)

        title_lbl = QLabel("FIELD STUDY ANALYTICS & RESEARCH FINDINGS")
        title_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {ACCENT_PRIMARY};")
        header_layout.addWidget(title_lbl)

        header_layout.addStretch()

        self.btn_rerun = PrimaryPushButton("RE-RUN ANALYSIS")
        self.btn_rerun.setStyleSheet(f"background-color: {ACCENT_PRIMARY}; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 5px 16px;")
        self.btn_rerun.clicked.connect(self.refresh_analysis)
        header_layout.addWidget(self.btn_rerun)

        layout.addWidget(header_card)

        # Scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout(scroll_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(14)

        # 1. 4 KPI Cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)

        self.card_obs = self._create_kpi_card("OBSERVATIONS", "0 Sites", "Sample Size")
        self.card_rate = self._create_kpi_card("SUCCESS RATE", "0.0%", "Pipeline Reliability")
        self.card_time = self._create_kpi_card("MEDIAN TIME", "0.0 ms", "Total Lookup Latency")
        self.card_countries = self._create_kpi_card("COUNTRIES", "0 Countries", "Geographic Spread")

        kpi_layout.addWidget(self.card_obs)
        kpi_layout.addWidget(self.card_rate)
        kpi_layout.addWidget(self.card_time)
        kpi_layout.addWidget(self.card_countries)
        self.content_layout.addLayout(kpi_layout)

        # 2. Performance Metrics Table
        table_card = QFrame()
        table_card.setObjectName("GlassCard")
        table_card.setStyleSheet(GLASS_CARD_QSS)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 14, 16, 14)
        table_layout.setSpacing(10)

        t_title = QLabel("DESCRIPTIVE PERFORMANCE METRICS (ms)")
        t_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {ACCENT_PRIMARY};")
        table_layout.addWidget(t_title)

        self.table = TableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "METRIC", "COUNT", "MEAN", "STD DEV", "MIN", "P25", "MEDIAN", "P75", "MAX", "IQR"
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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.table)

        self.content_layout.addWidget(table_card)

        # 3. Chart Viewer Frame
        chart_card = QFrame()
        chart_card.setObjectName("GlassCard")
        chart_card.setStyleSheet(GLASS_CARD_QSS)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(16, 14, 16, 14)
        chart_layout.setSpacing(10)

        c_header = QHBoxLayout()
        c_title = QLabel("RESEARCH CHART GALLERY")
        c_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {ACCENT_PRIMARY};")
        c_header.addWidget(c_title)
        c_header.addStretch()

        self.chart_combo = ComboBox()
        self.chart_combo.setFixedWidth(380)
        self.chart_combo.currentIndexChanged.connect(self._display_selected_chart)
        c_header.addWidget(self.chart_combo)

        chart_layout.addLayout(c_header)

        self.chart_display_lbl = QLabel()
        self.chart_display_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_display_lbl.setStyleSheet("padding: 10px;")
        chart_layout.addWidget(self.chart_display_lbl)

        self.content_layout.addWidget(chart_card)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area, 1)

    def _create_kpi_card(self, title: str, main_val: str, sub_val: str) -> QFrame:
        """Create styled KPI summary card."""
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

    def refresh_analysis(self):
        """Re-run analysis engine and update GUI cards, table, and charts."""
        try:
            self.analysis_data = generate_analysis_outputs()
            self._render_outputs()
        except Exception as e:
            QMessageBox.warning(self, "Analysis Warning", f"Could not load analysis outputs:\n{e}")

    def _render_outputs(self):
        """Render analysis metrics and populate table/charts."""
        rec_cnt = self.analysis_data.get("record_count", 0)
        succ_rate = self.analysis_data.get("success_rate", 0.0)
        desc_stats = self.analysis_data.get("descriptive_stats", {})
        tot_med = desc_stats.get("total_response_time_ms", {}).get("median", 0.0)
        c_dist = self.analysis_data.get("distributions", {}).get("country_distribution", {})

        self._update_kpi(self.card_obs, f"{rec_cnt} Sites")
        self._update_kpi(self.card_rate, f"{succ_rate}%")
        self._update_kpi(self.card_time, f"{tot_med} ms")
        self._update_kpi(self.card_countries, f"{len(c_dist)} Countries")

        # Table
        self.table.setRowCount(0)
        for metric_name, s in desc_stats.items():
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            items = [
                QTableWidgetItem(metric_name.replace("_response_time_ms", "").upper()),
                QTableWidgetItem(str(s["count"])),
                QTableWidgetItem(str(s["mean"])),
                QTableWidgetItem(str(s["std"])),
                QTableWidgetItem(str(s["min"])),
                QTableWidgetItem(str(s["p25"])),
                QTableWidgetItem(str(s["median"])),
                QTableWidgetItem(str(s["p75"])),
                QTableWidgetItem(str(s["max"])),
                QTableWidgetItem(str(s["iqr"])),
            ]

            for col_idx, item in enumerate(items):
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

        # Charts Combo
        chart_paths = self.analysis_data.get("chart_paths", [])
        self.chart_combo.clear()
        if chart_paths:
            self.chart_combo.addItems(chart_paths)
            self._display_selected_chart()

    def _update_kpi(self, card: QFrame, val: str):
        lbl = card.findChild(QLabel, "main_val")
        if lbl:
            lbl.setText(val)

    def _display_selected_chart(self):
        """Render selected chart image in QLabel."""
        chart_path = self.chart_combo.currentText()
        if not chart_path:
            return

        pixmap = QPixmap(chart_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(720, 360, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.chart_display_lbl.setPixmap(scaled)
