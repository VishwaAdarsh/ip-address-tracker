# IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform

A unified multi-layered cyber telemetry, IP geolocation, website security intelligence, and empirical network research platform. Built with a modern **Stitch Obsidian Dark Web Interface**, a high-performance **Python REST API Server**, and an extensible intelligence pipeline connecting public DNS resolution, geolocation APIs, SSL/TLS certificate probing, infrastructure classification, explainable dual trust/risk scoring, and local SQLite persistence.

---

## 1. System Architecture

```text
                                     IP PULSE PLATFORM
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      │                                             │
               STITCH WEB UI                                 PYTHON BACKEND
         (Obsidian Dark SPA Engine)                        (Core & Services)
                      │                                             │
      ┌───────────────┼───────────────┐                             │
      │ 1. Home Dashboard             │                      IP Resolution & DNS
      │ 2. Audit History              │                      Geolocation & Leaflet Map
      │ 3. 50-Site Field Study        │                      Website Security Intelligence
      │ 4. Research Dashboard         │                      IP Infrastructure Detection
      │ 5. Investigation Workspace    │                      Dual Trust / Risk Engine
      └───────────────┬───────────────┘                      6-Node Provenance Chain
                      │                                      IP Personality Archetypes
                      │                                      Explainable AI Layer
                      │                                      7-Dimension Research Analytics
                      │                                      Multi-Format Export Engine
                      │                                      SQLite DB (data/ip_tracker.db)
                      │                                             │
                      └────────────── HTTP / REST API ──────────────┘
                               (ThreadingHTTPServer / JSON)
```

---

## 2. Technology Stack

* **Runtime Environment:** Python 3.10+ (Standard Library `http.server.ThreadingHTTPServer`)
* **Persistence Layer:** SQLite 3 (`data/ip_tracker.db`) with Write-Ahead Logging (WAL) and enforced Foreign Keys
* **Frontend Interface:** Stitch Obsidian Dark Web Application (`frontend/index.html`, `frontend/assets/app.js`, `frontend/assets/style.css`)
* **Styling & UI Components:** Tailwind CSS utility framework, Google Fonts (Space Grotesk, JetBrains Mono, Syne), Material Symbols
* **Geospatial Visualization:** Leaflet JS + OpenStreetMap raster tiles
* **Data Processing & Analytics:** Python standard library, Pandas, ReportLab PDF generation engine
* **Quality Assurance & Testing:** Pytest, Unittest

---

## 3. Project Structure

```text
ip-address-tracker/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── server.py                   # ThreadingHTTPServer & REST routes
│   ├── services/                       # Business Logic & Orchestration
│   │   ├── __init__.py
│   │   ├── lookup_service.py           # Multi-provider DNS & IP normalization
│   │   ├── risk_analysis_service.py    # Master intelligence scan coordinator
│   │   ├── field_test_service.py       # Empirical 50-site field research protocol
│   │   └── comparison_service.py       # Investigation comparison matrix
│   ├── intelligence/                   # Autonomous Intelligence & Explanation
│   │   ├── __init__.py
│   │   ├── ai_explainer.py             # Dual deterministic & Gemini AI explainer
│   │   ├── intel_chain.py              # Provenance chain & IP personality engine
│   │   └── ip_intel.py                 # Autonomous infrastructure intelligence
│   ├── security/                       # Security & Threat Evaluation
│   │   ├── __init__.py
│   │   ├── security_scanner.py         # Website SSL/TLS & security scanner
│   │   └── risk_engine.py              # Mathematical risk & trust scoring
│   ├── analytics/                      # Statistical Aggregation & Research
│   │   ├── __init__.py
│   │   ├── analytics_service.py        # 7-dimension statistical metrics
│   │   ├── analyzer.py                 # Dataset validation & statistical summary
│   │   └── risk_analyzer.py            # Comparative risk computation
│   ├── providers/                      # Network & Geospatial Adapters
│   │   ├── __init__.py
│   │   ├── dns_resolver.py             # Public DNS resolution
│   │   ├── geo_service.py              # Multi-provider geolocation service
│   │   └── normalizer.py               # Response normalization
│   ├── models/                         # Data Models & Schemas
│   │   ├── __init__.py
│   │   └── models.py                   # Dataclass schemas (LookupRecord, FieldObservation)
│   ├── database/                       # Persistence Layer
│   │   ├── __init__.py
│   │   └── db.py                       # SQLite connection & transactions (WAL mode)
│   ├── reports/                        # Visualizer & Document Exporters
│   │   ├── __init__.py
│   │   ├── export_service.py           # Multi-format reports (CSV, JSON, MD, PDF)
│   │   ├── report_generator.py         # Research summary reports
│   │   └── visualizer.py               # Chart generation routines
│   ├── utils/                          # Utility & Validation Helper
│   │   ├── __init__.py
│   │   └── validator.py                # Input normalization & validation
│   ├── config/                         # Configuration Management
│   │   ├── __init__.py
│   │   └── settings.py                 # Central settings & path resolution
│   ├── tests/                          # Automated Pytest Suite (215+ tests)
│   │   ├── test_ai_explainer.py
│   │   ├── test_analytics_service.py
│   │   ├── test_api_server.py
│   │   ├── test_comparison_service.py
│   │   ├── test_database.py
│   │   ├── test_dns_resolver.py
│   │   ├── test_explainable_scoring.py
│   │   ├── test_export_service.py
│   │   ├── test_field_test_service.py
│   │   ├── test_geo_service.py
│   │   ├── test_intel_chain.py
│   │   ├── test_ip_intel.py
│   │   ├── test_lookup_service.py
│   │   ├── test_map_view.py
│   │   ├── test_normalizer.py
│   │   ├── test_risk_analysis_service.py
│   │   ├── test_risk_analyzer.py
│   │   ├── test_risk_engine.py
│   │   ├── test_security_scanner.py
│   │   ├── test_validator.py
│   │   └── test_visualization_dashboard.py
│   ├── app.py                          # Backend entrypoint (CLI & Web server)
│   ├── main.py                         # Secondary backend entrypoint
│   ├── requirements.txt                # Backend dependencies
│   └── pyproject.toml                  # Backend package definition
├── frontend/                           # Modern Vite-Ready Web Frontend
│   ├── src/                            # Source Assets
│   │   ├── app.js                      # SPA state manager & async REST client
│   │   ├── map.js                      # Leaflet interactive map controller
│   │   └── style.css                   # Custom theme tokens & obsidian styling
│   ├── public/                         # Static assets
│   ├── index.html                      # Unified Single Page Application (SPA)
│   ├── package.json                    # Frontend package metadata
│   └── vite.config.js                  # Frontend Vite configuration
├── data/                               # Stored Datasets & Single Source SQLite DB
│   ├── ip_tracker.db                   # Primary SQLite history & field study database
│   ├── analysis/                       # Historical research CSV datasets
│   ├── exports/                        # Generated field study exports & PDF reports
│   └── field_test/                     # Standardized 50-site seeds & results
├── docs/                               # Comprehensive Technical & Phase Documentation
│   ├── phase_17_explainable_scoring.md
│   ├── phase_18_ip_personality.md
│   ├── phase_19_field_study.md
│   ├── phase_20_analytics.md
│   ├── phase_21_research_report_and_export.md
│   ├── phase_22_ai_explainer.md
│   ├── phase_23_investigation_workspace.md
│   ├── phase_24_visualization_dashboard.md
│   ├── technical_documentation.md
│   └── viva_questions.md
├── logs/                               # Application log directory (.gitkeep)
├── app.py                              # Repository root launcher (delegates to backend)
├── requirements.txt                    # Project root dependencies
├── start_ip_pulse.bat                  # One-click Windows launcher
└── README.md
```

---

## 4. Subsystems & Key Capabilities

### A. Home Dashboard (`#view-home`)
* **Input Omnibar:** Accepts domain names (`github.com`), IPv4 addresses (`8.8.8.8`), and IPv6 addresses. Automatically normalizes schemes, ports, and trailing slashes.
* **4 Telemetry Badges:** Live Geolocation, IP Address & Reverse PTR, Autonomous System / ISP, and Infrastructure Type (`datacenter`, `cdn`, `residential`, `business`).
* **Interactive Leaflet Map:** Dynamic tile centering, glowing pulse marker, coordinate precision, and metadata popups.
* **Security & IP Intelligence:** TLS certificate validation, expiration countdown, HTTP security headers (HSTS, CSP, X-Frame-Options), VPN/Proxy/Tor exit node classification.
* **Trust & Risk Scoring:** Mathematically bounded dual scores ($0–100$, where $\text{Trust} + \text{Risk} = 100$) with evidence coverage confidence.
* **6-Node Provenance Chain & IP Personality:** Deterministic behavioral archetypes (`CLOUD_SENTINEL`, `RESIDENTIAL_PEER`, `PRIVACY_SHIELD`, etc.) and end-to-end evidence timeline.
* **Explainable AI:** Evidence-grounded natural language synthesis with dual-mode operation: Google Gemini LLM when configured, or deterministic rule-based fallback when offline.

### B. Audit History (`#view-history`)
* Persistent SQLite audit ledger storing historical inquiries.
* Search by domain, IP, or country, with pagination, single-record deletion, and full history purge.
* Complete read/write isolation from Field Study data.

### C. Standardized 50-Site Field Study (`#view-field-study`)
* Standardized empirical research protocol tracking 50 representative global web targets.
* Real-time progress quota tracking, observation validator (validating coordinates, ISO 8601 timestamps, score ranges, and unique tuples).
* Optional manual-triggered background observation completion.

### D. Research Dashboard (`#view-analytics`)
* Interactive 7-dimension filtering: Country, Infrastructure Type, Trust Classification, Risk Classification, HTTPS Status, IP Version, and Observation Scope/Range.
* Real-time statistical metrics: Mean, median, standard deviation, min, max, score distributions, and country frequencies.
* Filter-aware Leaflet map plotting observation coordinates with interactive popups.

### E. Investigation & Comparison Workspace (`#view-investigation`)
* Side-by-side comparative analysis of 2 to 5 candidates selected from Field Study observations or History records.
* Automatically rejects duplicate selections and enforces candidate boundary constraints.
* Extreme score identification (Highest Trust, Highest Risk, Lowest Evidence Confidence).
* Commonality matrix: Autonomous systems, countries, hosting providers, and infrastructure types.
* Guaranteed strictly read-only execution.

### F. Multi-Format Export Engine
* **RFC 4180 CSV:** Standard tabular export formatted for spreadsheets and data pipelines.
* **Structured JSON:** Comprehensive data structure with validation audit metadata and statistical metrics.
* **12-Section Research Markdown:** Complete academic-style research report with tables and footnotes.
* **ReportLab PDF:** Formatted executive report with tables, summary metrics, and distribution charts.

---

## 5. Configuration & Environment Variables

Copy `.env.example` to `.env` to configure optional overrides:

```powershell
copy .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `GEO_PROVIDER_NAME` | `ipapi.co` | Primary IP geolocation provider |
| `GEO_API_BASE_URL` | `https://ipapi.co` | Base URL for geolocation endpoint |
| `GEO_API_KEY` | *(None)* | Optional API key for paid/high-volume plans |
| `GEO_API_TIMEOUT` | `5.0` | Geolocation request timeout in seconds |
| `AI_PROVIDER` | `rule_based` | AI engine: `rule_based` (default), `gemini`, or `ollama` |
| `AI_API_KEY` | *(None)* | Google Gemini API key (or `GEMINI_API_KEY`) |
| `AI_MODEL` | `gemini-2.5-flash` | Model identifier for Gemini API |
| `AI_TIMEOUT` | `10.0` | AI explanation timeout in seconds |
| `AI_ENABLED` | `true` | Toggle AI explanation generation |
| `HOST` | `127.0.0.1` | Local server bind address |
| `PORT` | `8000` | Local server port |

---

## 6. How to Run Locally

### 1. Prerequisites
Ensure Python 3.10 or newer is installed. Install required dependencies:

```powershell
pip install -r requirements.txt
```

### 2. Launch the Application

#### Option A: One-Click Windows Launcher
Double-click `start_ip_pulse.bat` or run:
```powershell
.\start_ip_pulse.bat
```

#### Option B: Standard Python Command
```powershell
python app.py
```
This automatically starts the server at `http://127.0.0.1:8000/` and opens your default web browser.

#### Option C: Custom Port or Headless Mode
```powershell
# Custom port
python app.py --port 8080

# Headless server mode (no browser auto-launch)
python app.py --no-browser
```

---

## 7. Running Automated Tests

Run the full automated test suite using `pytest`:

```powershell
python -m pytest
```

To run a specific test suite:

```powershell
# API server integration tests
python -m pytest tests/test_api_server.py

# Risk engine & scoring tests
python -m pytest tests/test_explainable_scoring.py

# Visualization dashboard tests
python -m pytest tests/test_visualization_dashboard.py
```

---

## 8. Data Neutrality & Mandatory Disclaimer

Every signal displayed by IP PULSE is derived from observable network lookups or assigned an explicit `UNKNOWN` state. Missing data, unreachable hosts, or connection timeouts are never falsely classified as "malicious" or "insecure".

> [!IMPORTANT]
> **Mandatory Analytical Disclaimer:**  
> IP geolocation coordinates, Website Security Intelligence signals, and IP Risk Scores are analytical, heuristic indicators based on observable technical telemetry. They do not constitute definitive proof of physical location, website legitimacy, safety, or maliciousness, and should not be used as sole determinants for security enforcement.

