# IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform

A unified multi-layered cyber telemetry, IP geolocation, website security intelligence, and empirical network research platform. Built with a modern **Stitch Obsidian Dark Web Interface**, a multi-threaded **Python REST API Server**, and an extensible intelligence pipeline connecting public DNS resolution, geolocation APIs, SSL/TLS certificate probing, infrastructure classification, weighted trust/risk scoring, and local SQLite persistence.

---

## Target Architecture

```
                       IP PULSE PLATFORM
                               │
            ┌──────────────────┴──────────────────┐
            │                                     │
     STITCH WEB UI                         PYTHON BACKEND
 (Obsidian Dark Theme)                   (Core & Services)
            │                                     │
     ┌──────┴──────┐                              │
     │ Home        │                       IP Resolution & DNS
     │ History     │                       Geolocation & Leaflet Map
     │ Field Study │                       Website Security Intel
     │ Analytics   │                       IP Infrastructure Intel
     └──────┬──────┘                       Dual Trust / Risk Engine
            │                              Field Project & Analytics
            │                              SQLite DB (data/ip_tracker.db)
            │                                     │
            └────────── HTTP / REST API ──────────┘
                  (ThreadingHTTPServer / JSON)
```

---

## Key Features

1. **Stitch Obsidian Dark Web Application (`frontend/`):**
   - **Modern Aesthetic:** Dark palette (`#0F131C` surface, `#181C24` cards, `#00D2FF` electric cyan, `#69F6B9` emerald).
   - **Telemetry Dashboard:** Search omnibar, quick inquiry chips (`google.com`, `github.com`, `cloudflare.com`, `1.1.1.1`), 4 high-level telemetry metric cards (Location, IP, Org, Infrastructure).
   - **Interactive Geographic Map:** Leaflet + OpenStreetMap dynamic coordinate centering, glowing pulse marker, and popups.
   - **Multi-Tab Intelligence Strip:** Network Details, Website Security, IP Infrastructure, and AI Explanation with Provenance timeline.
   - **Investigation History:** Real audit ledger reading directly from SQLite database with domain search, single-item deletion, clear history, and CSV export.
   - **50-Site Field Study:** Manual-first research protocol tracker with live progress quota, real metric cards, and optional auto-completion.
   - **Field Study Analytics:** Real statistical distributions (Trust score histogram bins, geographic distribution, latency averages, IPv4/IPv6 ratios).

2. **Clean REST API Layer (`api/server.py`):**
   - Built on Python's standard library `ThreadingHTTPServer` for maximum concurrency, zero external dependencies, and instant startup.
   - CORS headers enabled for decoupled frontend development.
   - Endpoints:
     - `GET /` & `/assets/*`: Serves the Stitch web frontend and static assets.
     - `GET /api/status`: System health, capabilities, and version info.
     - `POST /api/analyze`: Unified domain/IP intelligence analysis pipeline.
     - `GET /api/history`: Returns SQLite lookup history records.
     - `DELETE /api/history/<id>` & `DELETE /api/history`: Deletes single record or clears table.
     - `GET /api/field-study`: Manual-first field study status and observation count.
     - `POST /api/field-study/complete-remaining`: Optional manual-triggered background completion for remaining observations up to 50.
     - `GET /api/analytics`: Statistical metrics calculated from actual stored observations.
     - `GET /api/export/csv`: Exports history or field study dataset as RFC-4180 CSV.

3. **Core Intelligence Backend (`core/` & `services/`):**
   - **Website Security Intelligence (`core/security_scanner.py`):** HTTPS enforcement, TLS certificate validation, expiration countdown, cipher suite, and security headers (HSTS, CSP, X-Frame-Options).
   - **IP Infrastructure Engine (`core/ip_intel.py`):** Provider pattern abstraction detecting VPN, Proxy, Tor exit nodes, and Datacenter hosting status.
   - **Dual Risk Engine (`core/risk_engine.py`):** Computes Website Trust Score (0–100) and IP Risk Score (0–100) with factor attribution.
   - **IP Personality & AI Explainer (`core/intel_chain.py`, `core/ai_explainer.py`):** Natural language personality statement and evidence-driven security report.
   - **Persistent SQLite Database (`database/db.py`):** Auto-saves completed lookups to `data/ip_tracker.db` with parameterized queries.

---

## Real Data & Disclaimer Policy

Every signal displayed by IP PULSE is derived from actual network lookups or explicit `Unknown` states. No fake, mock, or hardcoded demo values are presented as real.

> [!IMPORTANT]
> **Mandatory Analytical Disclaimer:**
> IP geolocation coordinates, Website Security Intelligence signals, and IP Risk Scores are analytical and approximate indicators. They do not constitute definitive proof of physical location, website legitimacy, safety, or maliciousness.

---

## Quick Start & Installation

### 1. Prerequisites & Setup
Clone the repository and activate your virtual environment:

```powershell
# Navigate to repository
cd C:\Users\Pradeep\Documents\GitHub\ip-address-tracker

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
```

### 2. Launch the Application

#### Option A: One-Click Windows Launcher
Double-click `start_ip_pulse.bat` or run:
```cmd
start_ip_pulse.bat
```

#### Option B: Python Command
```powershell
# Starts the server and automatically opens your default browser
python app.py

# Custom port
python app.py --port 8080

# Headless mode (server only, no browser auto-launch)
python app.py --no-browser
```

Open your browser at: **`http://127.0.0.1:8000/`**

---

## Running Automated Tests

Run the full automated unit and integration test suite:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

To run API server tests specifically:

```powershell
.\.venv\Scripts\python.exe -m unittest tests/test_api_server.py
```

---

## Project Structure

```text
ip-address-tracker/
├── api/                                # REST API Layer
│   ├── __init__.py
│   └── server.py                       # ThreadingHTTPServer & REST routes
├── frontend/                           # Stitch Obsidian Dark Web Application
│   ├── index.html                      # Unified Single Page Application (SPA)
│   └── assets/
│       ├── app.js                      # State manager & async fetch client
│       ├── map.js                      # Leaflet interactive map controller
│       └── style.css                   # Custom theme tokens & styles
├── core/                               # Network & Security Intelligence Engines
│   ├── dns_resolver.py                 # DNS resolution & address normalization
│   ├── geo_service.py                  # Geolocation multi-provider client
│   ├── security_scanner.py             # Website Security Intelligence
│   ├── ip_intel.py                     # IP Intelligence & Infrastructure Analysis
│   ├── risk_engine.py                  # Trust & Risk scoring engine
│   ├── intel_chain.py                  # Provenance chain & IP Personality
│   ├── ai_explainer.py                 # Evidence-based AI explanations
│   ├── normalizer.py                   # Response normalization
│   └── validator.py                    # Input validation
├── services/                           # Business Logic & Orchestration
│   ├── lookup_service.py               # Integrated lookup engine
│   ├── risk_analysis_service.py        # Master intelligence audit service
│   └── field_test_service.py           # Manual-first 50-site field study
├── database/                           # Persistence Layer
│   ├── db.py                           # SQLite parameterized query interface
│   └── models.py                       # Dataclass records
├── analysis/                           # Statistical Computation & Visualizations
│   ├── analyzer.py                     # Dataset validation & statistics
│   ├── visualizer.py                   # Chart generation pipeline
│   └── report_generator.py             # Analytical summary reports
├── data/                               # Stored Datasets & Database
│   ├── ip_tracker.db                   # Primary SQLite history database
│   └── field_test/                     # Predefined 50 sites & results CSV
├── stitch_ip_pulse_intelligence_platform/ # Original Stitch source designs
├── tests/                              # 100+ Automated Unit & Integration Tests
│   ├── test_api_server.py              # REST API route integration tests
│   ├── test_security_scanner.py        # Website security scanner tests
│   ├── test_ip_intel.py                # IP intelligence tests
│   ├── test_risk_engine.py             # Risk engine tests
│   └── ...                             # Core, DNS, Geo, DB, and Field tests
├── app.py                              # Primary application entrypoint
├── start_ip_pulse.bat                  # One-click Windows launcher
└── README.md
```
