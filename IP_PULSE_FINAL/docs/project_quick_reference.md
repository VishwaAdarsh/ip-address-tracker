# Project Quick Reference Cheat Sheet (Viva Revision)

## 1. Project Overview & Tech Stack

| Property | Value / Specification |
|---|---|
| **Project Title** | Python-based IP Address Tracker & Geolocation Tool |
| **Primary Purpose** | College Semester Field Project evaluating IP/DNS infrastructure & geolocation |
| **Master Blueprint** | `architecture.md` |
| **Main Entry Point** | `python app.py` |
| **Core Language** | Python 3 (3.14+) |
| **GUI Framework** | Python Tkinter / ttk (`gui/main_window.py`) |
| **Map Renderer** | `tkintermapview` (`gui/map_view.py`) |
| **Database Engine** | SQLite (`data/ip_tracker.db`, `database/db.py`) |
| **Geolocation Provider** | `ipapi.co` over HTTPS (`core/geo_service.py`) |
| **Data Analysis** | `pandas`, `matplotlib`, `numpy` (`analysis/`) |
| **Automated Tests** | 54 Unit/Integration Tests in `tests/` (100% Pass Rate) |

---

## 2. Core Operational Workflows

### A. Single Lookup Data Flow
```text
User Input
    ↓
Input Validation (core/validator.py)
    ↓
DNS Resolution (core/dns_resolver.py)
    ↓
Deterministic IP Selection Rule (1st IPv4 -> fallback 1st IPv6)
    ↓
IP Geolocation API Query (core/geo_service.py)
    ↓
Response Normalization (core/normalizer.py)
    ↓
SQLite History Database Persistence (database/db.py)
    ↓
Dashboard Display Cards & OpenStreetMap Visualization (gui/)
```

### B. 50-Website Research Workflow
```text
50 Predefined Websites (data/field_test/websites.csv)
    ↓
Sequential Batch Runner (services/field_test_service.py - 0.5s delay pacing)
    ↓
Raw Research Observation Output (data/field_test/field_test_results.csv)
    ↓
Descriptive Statistics & Dataset Validation (analysis/analyzer.py)
    ↓
7 Matplotlib PNG Charts & Report Output (analysis/visualizer.py & report_generator.py)
```

---

## 3. Key Empirical Findings (Phase 10 Dataset)

- **Total Sample Size:** 50 Public Websites across 11 categories
- **DNS Resolution Success Rate:** **98.0%** (49/50 resolved)
- **IPv4 Selection Ratio:** **98.0%** IPv4 (49/50) | 0.0% IPv6
- **Median DNS Resolution Latency:** **22.27 ms** (IQR: 5.97 ms)
- **Median Geolocation API Latency:** **80.75 ms** (IQR: 277.48 ms)
- **Median Total Pipeline Latency:** **108.64 ms** (IQR: 353.58 ms)
- **Top Geolocation Registry Country:** United States (35 sites)

---

## 4. Crucial Limitations to Remember for Viva

1. **Approximate Geolocation:** IP geolocation identifies regional network registry allocations—it is **NOT GPS-level tracking** and does not show exact physical building addresses.
2. **Time-Dependent DNS:** DNS results vary over time due to CDNs, Anycast routing, and dynamic load balancers.
3. **Sample Scope:** The 50-website dataset is a **purposive convenience sample**, not a random statistical representation of the global Internet.
4. **Median vs. Mean:** Network timing data exhibits strong right-skewness; therefore, **median** is reported as the primary metric of central tendency.
