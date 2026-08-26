# Python-based IP Address Tracker & Geolocation Tool

A modern, desktop-based network intelligence console and field-research software designed to perform domain input validation, public DNS resolution, approximate IP geolocation, persistent lookup history logging, interactive map visualization, and controlled 50-website batch field testing.

Developed as a College Semester Field Project adhering strictly to the architecture master blueprint in [architecture.md](architecture.md).

---

## Key Features

- **Input Normalization & Validation:** Validates domain names, IPv4 addresses, and IPv6 addresses natively (`core/validator.py`).
- **DNS Resolution Engine:** Resolves domain names to IPv4/IPv6 addresses via Python's standard `socket` module (`core/dns_resolver.py`). Preserves complete IP lists.
- **Deterministic IP Selection:** Automatically selects the first valid IPv4 address (or first valid IPv6 address if no IPv4 exists) for geolocation while preserving all returned addresses.
- **Approximate IP Geolocation:** Integrates with `ipapi.co` over HTTPS to retrieve country, region, city, coordinates, timezone, organization, ISP, and ASN (`core/geo_service.py`).
- **Persistent Local SQLite History:** Auto-saves completed lookups to `data/ip_tracker.db` with parameterized queries (`database/db.py`).
- **IP PULSE Desktop GUI Console:** Dark-themed desktop UI built with Python Tkinter/ttk featuring non-blocking background daemon threads (`gui/main_window.py`).
- **Interactive Map Visualization:** Renders OpenStreetMap tiles with location markers via `tkintermapview` (`gui/map_view.py`).
- **Manual-First Field-Test Engine:** Collects research observations from regular user lookups in SQLite History (`data/ip_tracker.db`). Offers controlled automatic completion only when fewer than 50 valid observations exist (`services/field_test_service.py`).
- **Data Analysis & Visualizations:** Computes descriptive statistics (mean, median, min, max, std, percentiles) and renders 7 dark-themed PNG research plots (`analysis/analyzer.py` & `analysis/visualizer.py`).

---

## Technology Stack

- **Language:** Python 3 (3.14+)
- **GUI Framework:** Python Tkinter / ttk (`gui/main_window.py`)
- **Map Renderer:** `tkintermapview` (OpenStreetMap tile renderer)
- **Data Analysis & Plotting:** `pandas`, `matplotlib`, `numpy`
- **Database Engine:** SQLite (built-in `sqlite3`, parameterized SQL)
- **Network Protocol:** Standard library `urllib.request`, `socket`

---

## Environment Setup & Installation

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/VishwaAdarsh/ip-address-tracker.git
cd ip-address-tracker

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. API Configuration (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Configuration variables:
```env
GEO_PROVIDER_NAME=ipapi.co
GEO_API_BASE_URL=https://ipapi.co
GEO_API_KEY=YOUR_API_KEY
GEO_API_TIMEOUT=5.0
```
*(Free tier operates up to 1,000 requests/day out of the box without requiring an API key)*

---

## Application Startup & Usage

### Running the Desktop GUI Console
```bash
python app.py
```
- **Dashboard Tab:** Enter a domain or IP and click **ANALYZE** (or press `Enter`).
- **History Tab:** View past lookups, inspect records, or clear history.
- **Field Test Tab:** Click **START FIELD TEST** to execute batch testing across 50 websites.
- **Analytics Tab:** View KPI summary cards, descriptive metrics, and chart gallery.

### Running Test Suite
```bash
python -m unittest discover -s tests
```
Runs 54 automated unit and integration tests across all modules.

---

## Project Structure

```text
ip-address-tracker/
├── analysis/                 # Data analysis & visualization modules
│   ├── __init__.py
│   ├── analyzer.py           # Descriptive statistics & dataset validation
│   ├── visualizer.py         # Matplotlib 7-chart rendering pipeline
│   └── report_generator.py   # Analysis summary & report generator
├── config/                   # Application configuration & .env loader
│   ├── __init__.py
│   └── settings.py
├── core/                     # Core backend processing engines
│   ├── __init__.py
│   ├── validator.py          # Domain / IPv4 / IPv6 validation
│   ├── dns_resolver.py       # Socket-based DNS resolver
│   ├── geo_service.py        # Geolocation HTTPS API client
│   └── normalizer.py         # Response normalizer & GeoResult dataclass
├── data/                     # Local data storage & research datasets
│   ├── ip_tracker.db         # SQLite persistent lookup history
│   ├── field_test/           # 50-website dataset & research CSV output
│   │   ├── websites.csv
│   │   └── field_test_results.csv
│   └── analysis/             # Derived analysis summaries & charts
│       ├── cleaned_results.csv
│       ├── summary_statistics.csv
│       ├── country_distribution.csv
│       ├── status_distribution.csv
│       ├── research_analysis_report.md
│       └── charts/           # Rendered PNG research plots
├── database/                 # SQLite storage layer
│   ├── __init__.py
│   ├── db.py
│   └── models.py
├── docs/                     # Academic documentation & guides
│   ├── field_test_methodology.md
│   ├── project_report.md
│   ├── technical_documentation.md
│   └── user_guide.md
├── gui/                      # Desktop GUI presentation layer
│   ├── __init__.py
│   ├── main_window.py        # IP PULSE main window & navigation
│   ├── results_view.py       # Dashboard result cards & map frame
│   ├── history_view.py       # History treeview table & details pane
│   ├── field_test_view.py    # 50-website batch runner GUI
│   ├── analytics_view.py     # Analytics KPI cards & chart viewer
│   └── map_view.py           # OpenStreetMap tile component
├── services/                 # Workflow orchestration services
│   ├── __init__.py
│   ├── lookup_service.py     # Integrated end-to-end lookup pipeline
│   └── field_test_service.py # Field-test execution service
├── tests/                    # Automated unit & integration test suite
│   ├── test_validator.py
│   ├── test_dns_resolver.py
│   ├── test_geo_service.py
│   ├── test_normalizer.py
│   ├── test_lookup_service.py
│   ├── test_database.py
│   ├── test_map_view.py
│   ├── test_field_test_service.py
│   └── test_analysis.py
├── app.py                    # Application entry point
├── architecture.md           # Master architectural blueprint
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
└── README.md                 # Project documentation
```

---

## Documentation Directory

Detailed project documentation is available in the `docs/` folder:
- [project_report.md](docs/project_report.md): Formal Academic Field Project Report
- [technical_documentation.md](docs/technical_documentation.md): Engineering Architecture & System Specifications
- [user_guide.md](docs/user_guide.md): Comprehensive Desktop User Guide
- [field_test_methodology.md](docs/field_test_methodology.md): Research Design & 50-Website Sampling Methodology

---

## Project Status & Roadmap

- [x] Phase 1: Development Environment Setup
- [x] Phase 2: Input Validation Module
- [x] Phase 3: DNS Resolution Engine
- [x] Phase 4: IP Geolocation Service
- [x] Phase 5: Integrated Lookup Engine
- [x] Phase 6: Database & Lookup History
- [x] Phase 7: Premium GUI Console
- [x] Phase 8: Map Visualization
- [x] Phase 9: 50-Website Field-Test Module
- [x] Phase 10: Data Analysis & Visualization
- [x] Phase 11: Final Academic Documentation
