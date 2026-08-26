"""
PySide6 Dashboard View Module for IP Address Tracker & Geolocation Tool.

Provides:
- Target search bar (TARGET INTEL) with LineEdit input and ANALYZE trigger
- QThread asynchronous background worker to prevent GUI freezing
- Status indicator badges (SUCCESS, GEO_FAILED, DNS_FAILED, etc.)
- 3 Summary KPI cards (Target IP, Location, Network Owner)
- Geolocation and network performance details panels
- Integrated MapView visualization with coordinate validation
"""
from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import LineEdit, PrimaryPushButton, ProgressRing

from gui.modern.map_view import MapView
from gui.modern.style_system import (
    ACCENT_ERROR,
    ACCENT_HOVER,
    ACCENT_PRIMARY,
    ACCENT_SUCCESS,
    ACCENT_WARNING,
    BADGE_FAILED_QSS,
    BADGE_SUCCESS_QSS,
    GLASS_CARD_QSS,
    SURFACE_BG,
    SURFACE_BORDER,
    TEXT_LIGHT,
    TEXT_MUTED,
)
from services.lookup_service import LookupResult, LookupStatus, perform_lookup


class LookupWorker(QObject):
    """Async worker for running perform_lookup in background QThread."""

    finished = Signal(object)

    def __init__(self, target_input: str):
        super().__init__()
        self.target_input = target_input

    def run(self):
        result = perform_lookup(self.target_input, save_to_db=True)
        self.finished.emit(result)


class DashboardView(QWidget):
    """Modern PySide6 Dashboard view module."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 1. Search Bar Frame (TARGET INTEL)
        search_card = QFrame()
        search_card.setObjectName("GlassCard")
        search_card.setStyleSheet(GLASS_CARD_QSS)
        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(16, 12, 16, 12)
        search_layout.setSpacing(12)

        intel_lbl = QLabel("TARGET INTEL:")
        intel_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {ACCENT_PRIMARY};")
        search_layout.addWidget(intel_lbl)

        self.input_edit = LineEdit()
        self.input_edit.setPlaceholderText("Enter domain or public IP address (e.g. google.com or 8.8.8.8)...")
        self.input_edit.setStyleSheet(f"background-color: #0F172A; color: {TEXT_LIGHT}; border: 1px solid {SURFACE_BORDER}; border-radius: 6px; padding: 6px 12px;")
        self.input_edit.returnPressed.connect(self._start_lookup)
        search_layout.addWidget(self.input_edit, 1)

        self.analyze_btn = PrimaryPushButton("ANALYZE")
        self.analyze_btn.setStyleSheet(f"background-color: {ACCENT_PRIMARY}; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 6px 20px;")
        self.analyze_btn.clicked.connect(self._start_lookup)
        search_layout.addWidget(self.analyze_btn)

        main_layout.addWidget(search_card)

        # 2. Status Badge & Loading Indicator Bar
        self.status_frame = QHBoxLayout()

        self.status_badge = QLabel("● READY FOR INPUT")
        self.status_badge.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: bold;")
        self.status_frame.addWidget(self.status_badge)

        self.loading_spinner = ProgressRing()
        self.loading_spinner.setFixedSize(20, 20)
        self.loading_spinner.setVisible(False)
        self.status_frame.addWidget(self.loading_spinner)

        self.info_lbl = QLabel("")
        self.info_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self.status_frame.addWidget(self.info_lbl)
        self.status_frame.addStretch()

        main_layout.addLayout(self.status_frame)

        # 3. Scrollable Content Area for Results
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout(scroll_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

        # A. Summary KPI Cards Layout (Target IP, Location, Network)
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)

        self.card_ip = self._create_kpi_card("TARGET IP", "N/A", "Version: N/A")
        self.card_location = self._create_kpi_card("LOCATION", "N/A, N/A", "Region: N/A")
        self.card_network = self._create_kpi_card("NETWORK", "N/A", "ASN: N/A")

        kpi_layout.addWidget(self.card_ip)
        kpi_layout.addWidget(self.card_location)
        kpi_layout.addWidget(self.card_network)
        self.content_layout.addLayout(kpi_layout)

        # B. Geolocation Details Card
        geo_card = QFrame()
        geo_card.setObjectName("GlassCard")
        geo_card.setStyleSheet(GLASS_CARD_QSS)
        geo_layout = QVBoxLayout(geo_card)
        geo_layout.setContentsMargins(16, 16, 16, 16)
        geo_layout.setSpacing(10)

        geo_title = QLabel("APPROXIMATE IP GEOLOCATION DETAILS")
        geo_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {ACCENT_PRIMARY};")
        geo_layout.addWidget(geo_title)

        details_grid = QVBoxLayout()
        details_grid.setSpacing(6)

        self.lbl_country = self._create_detail_row(details_grid, "Country / Code:", "N/A")
        self.lbl_region = self._create_detail_row(details_grid, "Region / State:", "N/A")
        self.lbl_city = self._create_detail_row(details_grid, "City:", "N/A")
        self.lbl_coords = self._create_detail_row(details_grid, "Coordinates:", "N/A")
        self.lbl_tz = self._create_detail_row(details_grid, "Timezone:", "N/A")
        self.lbl_org = self._create_detail_row(details_grid, "Organization:", "N/A")
        self.lbl_isp = self._create_detail_row(details_grid, "ISP:", "N/A")
        self.lbl_timing = self._create_detail_row(details_grid, "Performance:", "DNS: 0.0 ms | API: 0.0 ms | Total: 0.0 ms")

        geo_layout.addLayout(details_grid)
        self.content_layout.addWidget(geo_card)

        # C. Integrated Map Component
        self.map_view = MapView()
        self.content_layout.addWidget(self.map_view)

        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area, 1)

    def _create_kpi_card(self, title: str, main_val: str, sub_val: str) -> QFrame:
        """Create styled summary KPI card."""
        card = QFrame()
        card.setObjectName("GlassCard")
        card.setStyleSheet(GLASS_CARD_QSS)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
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

    def _create_detail_row(self, parent_layout: QVBoxLayout, key: str, default_val: str) -> QLabel:
        """Create a key-value label detail row."""
        row_layout = QHBoxLayout()
        k_lbl = QLabel(key)
        k_lbl.setFixedWidth(130)
        k_lbl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {TEXT_MUTED};")
        row_layout.addWidget(k_lbl)

        v_lbl = QLabel(default_val)
        v_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_LIGHT};")
        row_layout.addWidget(v_lbl, 1)

        parent_layout.addLayout(row_layout)
        return v_lbl

    def _start_lookup(self):
        """Initiate asynchronous background lookup thread."""
        target = self.input_edit.text().strip()
        if not target:
            self.status_badge.setText("● PLEASE ENTER TARGET DOMAIN OR IP")
            self.status_badge.setStyleSheet(f"color: {ACCENT_WARNING}; font-size: 11px; font-weight: bold;")
            return

        self.analyze_btn.setEnabled(False)
        self.input_edit.setEnabled(False)
        self.loading_spinner.setVisible(True)
        self.status_badge.setText(f"● ANALYZING TARGET '{target}'...")
        self.status_badge.setStyleSheet(f"color: {ACCENT_PRIMARY}; font-size: 11px; font-weight: bold;")

        # Set up QThread
        self.thread = QThread()
        self.worker = LookupWorker(target)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_lookup_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_lookup_finished(self, result: LookupResult):
        """Process returned LookupResult on Qt main thread."""
        self.analyze_btn.setEnabled(True)
        self.input_edit.setEnabled(True)
        self.loading_spinner.setVisible(False)

        st_val = result.overall_status.value
        if result.overall_status == LookupStatus.SUCCESS:
            self.status_badge.setText("● STATUS: SUCCESS")
            self.status_badge.setStyleSheet(f"color: {ACCENT_SUCCESS}; font-size: 11px; font-weight: bold;")
        else:
            self.status_badge.setText(f"● STATUS: {st_val}")
            self.status_badge.setStyleSheet(f"color: {ACCENT_ERROR}; font-size: 11px; font-weight: bold;")

        self.info_lbl.setText(f"Input: '{result.input}' ({result.input_type}) | Timestamp: {result.timestamp[:19]}")

        # Update Summary Cards
        ip_card_val = self.card_ip.findChild(QLabel, "main_val")
        ip_card_sub = self.card_ip.findChild(QLabel, "sub_val")
        if ip_card_val and ip_card_sub:
            ip_card_val.setText(result.selected_ip or "N/A")
            ip_card_sub.setText(f"Version: {result.ip_version}")

        loc_card_val = self.card_location.findChild(QLabel, "main_val")
        loc_card_sub = self.card_location.findChild(QLabel, "sub_val")
        if loc_card_val and loc_card_sub:
            loc_card_val.setText(f"{result.city}, {result.country}")
            loc_card_sub.setText(f"Region: {result.region} ({result.country_code})")

        net_card_val = self.card_network.findChild(QLabel, "main_val")
        net_card_sub = self.card_network.findChild(QLabel, "sub_val")
        if net_card_val and net_card_sub:
            net_card_val.setText(result.organization or "N/A")
            net_card_sub.setText(f"ASN: {result.asn}")

        # Update Geolocation details
        self.lbl_country.setText(f"{result.country} ({result.country_code})")
        self.lbl_region.setText(result.region)
        self.lbl_city.setText(result.city)

        if result.latitude is not None and result.longitude is not None:
            self.lbl_coords.setText(f"{result.latitude:.4f}, {result.longitude:.4f}")
        else:
            self.lbl_coords.setText("N/A")

        self.lbl_tz.setText(result.timezone)
        self.lbl_org.setText(result.organization)
        self.lbl_isp.setText(result.isp)
        self.lbl_timing.setText(
            f"DNS: {result.dns_response_time_ms:.1f} ms | API: {result.api_response_time_ms:.1f} ms | Total: {result.total_response_time_ms:.1f} ms"
        )

        # Update Map View
        self.map_view.set_location(
            result.latitude,
            result.longitude,
            title=result.selected_ip or result.input,
            city=result.city,
            country=result.country,
        )
