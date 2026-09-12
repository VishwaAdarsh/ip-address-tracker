# IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform

**Version:** 2.0.0 (Integrated Production Release)  
**UI Design:** Stitch Obsidian Dark Theme Integration (PySide6 + QFluentWidgets)  
**Backend:** Python 3 (Socket DNS, Multi-Provider Geolocation, SSL/TLS Probing, Risk Analytics, SQLite Persistence)  
**Field Study Dataset:** 50 Predefined Research Websites (`data/field_test/websites.csv`)  

---

## 1. Executive Summary & Purpose

**IP PULSE** is an advanced academic and research platform designed for performing non-intrusive domain resolution, IP geolocation tracking, website security auditing, network infrastructure classification, and empirical data analysis across a controlled sample of 50 websites.

The system combines a modern Stitch-designed PySide6 + QFluentWidgets desktop user interface with an asynchronous Python backend engine, an interactive Leaflet.js + OpenStreetMap tile renderer, and a local SQLite history database.

> **Academic & Security Disclaimer Notice:**  
> *"IP geolocation coordinates, Website Security Intelligence signals, and IP Risk Scores are analytical and approximate indicators. They do not constitute definitive proof of physical location, website legitimacy, safety, or maliciousness."*

---

## 2. Platform Features

- **Domain & IP Resolution:** Resolves IPv4 and IPv6 addresses via native socket DNS resolution.
- **Multi-Provider Geolocation:** Retrieves country, region, city, coordinates, timezone, organization, ISP, and ASN with automatic endpoint fallback (`ipapi.co` -> `ip-api.com`).
- **Interactive OpenStreetMap Visualization:** Embedded PySide6 `QWebEngineView` rendering Leaflet.js tiles with custom target markers, zoom (+/-) controls, and fallback state handling.
- **Website Security Intelligence (Phase 15):** Probes HTTPS status, HTTP -> HTTPS redirect chains, TLS protocol versions, and SSL certificate validity, issuer, and expiry days.
- **IP Intelligence & Infrastructure Analysis (Phase 16):** Classifies network categories (`CDN / Edge Hub`, `Cloud Hosting`, `Commercial ISP`, `Enterprise Network`) and anonymizer signals (`VPN`, `Proxy`, `Tor`) via extensible provider abstraction (`IPIntelligenceProvider`).
- **Trust & Risk Engine:** Computes transparent 0–100 Website Trust Scores and IP Risk Scores with weighted factor attribution.
- **Evidence-Based AI Explainer:** Generates natural language risk reports strictly grounded in empirical scan findings without hallucinating missing data.
- **Manual-First Field Study Workflow:** Collects user Dashboard lookups into SQLite history (`ip_tracker.db`), deduplicates observations, tracks progress (`N / 50`), and provides optional controlled auto-completion ONLY when `N < 50`.
- **Descriptive Data Analysis:** Computes mean, median, standard deviation, IQR across timing metrics, exports CSV datasets, and generates 7 Matplotlib research plots (`data/analysis/charts/`).

---

## 3. Technology Stack

- **UI Framework:** PySide6 (v6.11.2) + QFluentWidgets (v1.11.3) + QWebEngineView + Leaflet.js (OpenStreetMap)
- **Programming Language:** Python 3.10+
- **Data Analysis & Plotting:** Pandas, NumPy, Matplotlib
- **Database:** SQLite 3 (`data/ip_tracker.db`)
- **Testing Framework:** Python `unittest` (86+ Automated Tests)

---

## 4. Software Architecture & Data Flow

```text
                                  +---------------------------------------+
                                  |         User Domain / IP Input        |
                                  +---------------------------------------+
                                                      |
                                                      v
                                        +---------------------------+
                                        |   Existing Lookup Engine  |
                                        | (DNS + Geolocation Client)|
                                        +---------------------------+
                                                      |
                                                      v
                                           LookupResult (Base Data)
                                                      |
                    +---------------------------------+---------------------------------+
                    |                                 |                                 |
                    v                                 v                                 v
    +-------------------------------+ +-------------------------------+ +-------------------------------+
    |   Module A: Security Scanner  | |    Module B: IP Intel Engine  | |   Module D: Intel Chain Engine|
    | (HTTPS, SSL, Cert, Redirects) | |  (Hosting, Proxy/VPN, ASN)  | |  (IP Personality, Provenance)|
    +-------------------------------+ +-------------------------------+ +-------------------------------+
                    |                                 |                                 |
                    +---------------------------------+---------------------------------+
                                                      |
                                                      v
                                        +---------------------------+
                                        | Module C: Risk & Trust    |
                                        |       Scoring Engine      |
                                        +---------------------------+
                                                      |
                                                      v
                                        +---------------------------+
                                        | Module G: AI Evidence     |
                                        |     Explainer Engine      |
                                        +---------------------------+
                                                      |
                                                      v
                                      FullIntelligenceResult Schema
                                                      |
                                  +-------------------+-------------------+
                                  |                   |                   |
                                  v                   v                   v
                          PySide6 GUI        SQLite History       Risk Analytics
                          (Dashboard)         (ip_tracker.db)     & Research Plots
```

---

## 5. Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git

### Installation Steps
```bash
# 1. Clone repository
git clone https://github.com/VishwaAdarsh/ip-address-tracker.git
cd ip-address-tracker

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 6. How to Run the Application

```bash
# Run Modern Stitch PySide6 + QFluentWidgets Desktop Application:
python app.py

# Run Legacy Tkinter Fallback Interface (Optional):
python app.py --legacy
```

---

## 7. How to Run the Automated Test Suite

```bash
# Run all 86+ automated unit and integration tests:
python -m unittest discover -s tests -p "test_*.py"
```

---

## 8. Directory Structure Overview

```text
IP_PULSE_FINAL/
├── app.py                     # Main Application Entry Point
├── requirements.txt           # Dependency Requirements
├── README.md                  # Comprehensive Documentation
├── architecture.md            # Master Architecture Blueprint
├── config/                    # Global Configuration & Settings
├── core/                      # Core Analysis & Security Modules
├── services/                  # Business Logic Orchestration Services
├── database/                  # SQLite Database Engine & Models
├── gui/                       # PySide6 + QFluentWidgets UI Views & Map Widgets
├── analysis/                  # Statistical Analysis & Matplotlib Visualizer
├── data/                      # SQLite DB, Field Test Datasets, CSVs & PNG Charts
├── docs/                      # Academic & Technical Documentation Reports
└── tests/                     # Automated Test Suite (86+ Unit & Integration Tests)
```
