# Technical Architecture & Engineering Documentation

## 1. System Architecture Overview

The **IP PULSE** platform is architected as a modular, deployment-ready multi-tier system. The system follows strict separation of concerns, ensuring that the modern Stitch Web Application interacts with network engines, security analyzers, and local SQLite persistence exclusively through a high-performance REST API.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       STITCH OBSIDIAN WEB FRONTEND                          │
│   Home Dashboard │ History Ledger │ Field Study │ Analytics │ Workspace     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (Async Fetch JSON / REST API)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND REST API LAYER                             │
│   ThreadingHTTPServer [backend/api/server.py]                               │
└────────┬─────────────────────────────┬─────────────────────────────┬────────┘
         │                             │                             │
         ▼                             ▼                             ▼
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│ INTELLIGENCE &   │          │ SERVICE LAYER    │          │ DATABASE &       │
│ SECURITY ENGINES │          │ & ANALYTICS      │          │ REPORTS          │
│ ai_explainer.py  │          │ lookup_service   │          │ database/db.py   │
│ intel_chain.py   │          │ field_test_svc   │          │ models/models.py │
│ ip_intel.py      │          │ comparison_svc   │          │ export_service   │
│ risk_engine.py   │          │ analytics_svc    │          │ data/            │
│ security_scanner │          │ dns / geo provs  │          │   ip_tracker.db  │
└──────────────────┘          └──────────────────┘          └──────────────────┘
```

---

## 2. Directory Layout & Module Specifications

### 2.1 Backend Modules (`backend/`)
- **`backend.api` (`backend/api/server.py`):** Multi-threaded REST API server supporting CORS, JSON payloads, static asset delivery, and Vercel serverless exports.
- **`backend.services`:** Orchestrates lookups (`lookup_service.py`), empirical research (`field_test_service.py`), risk analysis coordinator (`risk_analysis_service.py`), and candidate comparisons (`comparison_service.py`).
- **`backend.intelligence`:** Autonomous infrastructure intelligence (`ip_intel.py`), 6-node provenance chain & IP personality archetypes (`intel_chain.py`), and explainable AI (`ai_explainer.py`).
- **`backend.security`:** SSL/TLS certificate inspection & security headers (`security_scanner.py`), and mathematically bounded dual trust/risk scoring (`risk_engine.py`).
- **`backend.analytics`:** 7-dimension statistical aggregation engine (`analytics_service.py`), dataset validation (`analyzer.py`), and comparative risk analytics (`risk_analyzer.py`).
- **`backend.providers`:** Public DNS resolver (`dns_resolver.py`), multi-provider geolocation client (`geo_service.py`), and response normalizer (`normalizer.py`).
- **`backend.models` (`backend/models/models.py`):** Dataclass representations for `LookupRecord` and `FieldObservation`.
- **`backend.database` (`backend/database/db.py`):** SQLite persistence engine operating in WAL mode with parameterized queries against `data/ip_tracker.db`.
- **`backend.reports`:** Multi-format export engine (`export_service.py`), research reports (`report_generator.py`), and headless visualizations (`visualizer.py`).
- **`backend.utils` (`backend/utils/validator.py`):** Input normalization and coordinate boundary validation.
- **`backend.config` (`backend/config/settings.py`):** Centralized configuration and path resolution relative to repo root.

### 2.2 Frontend Application (`frontend/`)
- **`frontend/index.html`:** Unified SPA hosting Home, History, Field Study, Research Analytics, and Investigation Workspace.
- **`frontend/src/app.js`:** State management, asynchronous API communications, and view router.
- **`frontend/src/map.js`:** Leaflet mapping engine with pulse animations and responsive tile management.
- **`frontend/src/style.css`:** Obsidian dark design tokens, glassmorphism styling, and custom utilities.
- **`frontend/vite.config.js`:** Modern Vite bundler configuration with API reverse proxy.

---

## 3. Automated Test Suite Specifications

All automated unit and integration tests are housed in `backend/tests/`:
```text
backend/tests/
├── test_ai_explainer.py                 # Dual AI explainer & fallback tests
├── test_analytics_service.py            # 7-dimension statistical metrics
├── test_api_server.py                   # REST endpoints, headers & static serving
├── test_comparison_service.py           # Investigation workspace logic
├── test_database.py                     # SQLite CRUD, schema migrations, WAL mode
├── test_dns_resolver.py                 # DNS resolution & normalization
├── test_explainable_scoring.py          # Trust & Risk score invariants
├── test_export_service.py               # CSV, JSON, Markdown, and PDF generation
├── test_field_test_service.py           # Standardized 50-site research protocol
├── test_geo_service.py                  # Geolocation provider & timeout handling
├── test_intel_chain.py                  # Provenance chain & IP Personality
├── test_ip_intel.py                     # Infrastructure classification & VPN detection
├── test_lookup_service.py               # Multi-provider lookup workflow
├── test_map_view.py                     # Coordinate bounding validation
├── test_normalizer.py                   # Data normalization & missing field guarantees
├── test_risk_analysis_service.py        # Master scan coordinator
├── test_risk_analyzer.py                # Comparative risk analysis
├── test_risk_engine.py                  # Trust/Risk mathematical bounds
├── test_security_scanner.py             # SSL/TLS & security header audits
├── test_validator.py                    # Input validation & normalization
└── test_visualization_dashboard.py      # Cohort filtering & geographic popups
```
**Total Test Count:** 215 Automated Tests (100% Pass Rate).

