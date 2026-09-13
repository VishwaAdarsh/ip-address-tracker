# Phase 21: Research Report & Data Export

## 1. Executive Summary

Phase 21 establishes an end-to-end data export and publication-grade research reporting pipeline for IP PULSE ("IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform"). It enables empirical field study observations, validation audits, and analytical metrics to be programmatically packaged and exported in multiple academic and industry standard formats.

### Core Architectural Principles
- **Empirical Ground Truth:** All exports originate exclusively from genuine observational telemetry stored in `data/ip_tracker.db` (`field_study_observations` table). No simulated records, synthetic scores, or artificial threat telemetry are fabricated.
- **Uniform Handling of Missing Data:** Any unmeasured, unobserved, or unresolvable dimension (e.g. unknown ASN, missing DNSSEC, absent TLS issuer) is strictly standardized to `UNKNOWN`. Missing numeric metrics remain unskewed and are never assumed to be 0 or 100.
- **Dual Export Modalities:** Exports can be triggered via HTTP API endpoints with automatic streaming file downloads in the browser, or saved deterministically to `data/exports/` for archival and offline analysis.
- **Non-Destructive Data Validation:** Built-in automated dataset audits inspect duplicate normalized domains, score boundary violations ($0 \le \text{score} \le 100$), coordinate limits, and classification consistency without altering the primary database.
- **Stitch Obsidian Dark Frontend Integration:** 4-button Export Actions Bars in both the Field Study view (`#view-field-study`) and Analytics view (`#view-analytics`) with loading spinners, duplicate click prevention, and quota-aware toasts.

---

## 2. Export Formats & Specifications

### 2.1 Standardized CSV Dataset (`RFC 4180`)
- **Default Filename:** `IP_PULSE_Field_Study.csv` (or timestamped `IP_PULSE_Field_Study_YYYYMMDD_HHMMSS.csv`)
- **Content Type:** `text/csv; charset=utf-8`
- **Specification:** RFC 4180 compliant with header row and exact 38 standardized research columns:
  1. `observation_id`
  2. `domain`
  3. `ip_address`
  4. `ip_version`
  5. `country`
  6. `country_code`
  7. `region`
  8. `city`
  9. `postal_code`
  10. `latitude`
  11. `longitude`
  12. `timezone`
  13. `asn`
  14. `asn_org`
  15. `isp`
  16. `network_org`
  17. `is_hosting_provider`
  18. `is_vpn`
  19. `is_proxy`
  20. `is_tor`
  21. `is_relay`
  22. `website_trust_score`
  23. `website_trust_level`
  24. `ip_risk_score`
  25. `ip_risk_level`
  26. `personality_type`
  27. `personality_description`
  28. `https_supported`
  29. `tls_version`
  30. `tls_valid`
  31. `hsts_enabled`
  32. `dnssec_enabled`
  33. `dns_latency_ms`
  34. `http_latency_ms`
  35. `response_time_ms`
  36. `security_signals_count`
  37. `tested_at`
  38. `notes`

### 2.2 Structured JSON Dataset (`JSON Schema`)
- **Default Filename:** `IP_PULSE_Field_Study.json`
- **Content Type:** `application/json; charset=utf-8`
- **Structure:**
  - `metadata`: Platform identity, export ISO 8601 timestamp, schema version `1.0.0`, software version, observation count, target quota (50), completion percentage.
  - `validation_summary`: Quality audit flags, duplicate domains, missing domains/IPs, score violations, coordinate anomalies.
  - `analytics_summary`: Reuses full Phase 20 analytics payload (`field_study_overview`, `trust_and_risk_analysis`, `security_and_transport`, `infrastructure_and_network`, `geographic_distribution`, `autonomous_systems`, `rankings_and_extremes`).
  - `observations`: Array of 38-property observation objects with typed values (`int`, `float`, `bool`, `str`, or `None`).

### 2.3 Comprehensive Academic Markdown Report (`GFM`)
- **Default Filename:** `IP_PULSE_Research_Report.md`
- **Content Type:** `text/markdown; charset=utf-8`
- **Structure (12 Sections):**
  1. Title, Metadata & Academic Executive Summary
  2. Research Objectives & Methodology
  3. 50-Site Field Study Overview & Completion Status
  4. Website Trust & IP Risk Score Distribution (Statistical Tables)
  5. Security & Transport Encryption Findings (HTTPS, TLS, HSTS, DNSSEC)
  6. Infrastructure & Network Topology Analysis (IPv4/IPv6, Cloud Density)
  7. Geographic Distribution & Border Gateway Patterns
  8. Autonomous System Concentration & Consolidation
  9. Key Findings, Correlations & Anomalies
  10. Analytical Limitations & Non-Speculative Disclaimers
  11. Conclusion & Recommendations
  12. Raw Observation Summary Table

### 2.4 Publication-Grade PDF Report (`ReportLab 5.x`)
- **Default Filename:** `IP_PULSE_Research_Report.pdf`
- **Content Type:** `application/pdf`
- **Design & Layout:**
  - Generated using ReportLab Platypus (`SimpleDocTemplate`, `Paragraph`, `Table`, `Spacer`, `KeepTogether`).
  - Strict palette matching IP PULSE Obsidian Dark styling: Navy/Dark Slate (`#0f172a`), Dark Card Backgrounds (`#1e293b`), Primary Accent Cyan/Sky (`#0284c7`, `#38bdf8`), Neutral Text (`#f8fafc`, `#94a3b8`).
  - Includes executive metadata banner, statistical KPI summary tables, security adoption rates, top autonomous systems, methodology, and a compact observation reference table (capped at 25 rows for document conciseness).

---

## 3. Pre-Export Data Validation Engine

Before generating any report or data export, the validation engine (`validate_field_study_dataset()`) executes a non-destructive multi-point audit:
1. **Duplicate Domain Detection:** Checks for case-insensitive duplicate normalized domain names.
2. **Missing Essential Identifiers:** Detects rows lacking domain or IP address strings.
3. **Score Boundary Violations:** Validates that `website_trust_score` and `ip_risk_score` satisfy $0 \le x \le 100$.
4. **Coordinate Anomalies:** Ensures $-90 \le \text{latitude} \le 90$ and $-180 \le \text{longitude} \le 180$.
5. **Classification Consistency:** Verifies categorical labels (`personality_type`, `trust_level`, `risk_level`).

Validation results are returned via `GET /api/export/validate` and embedded in JSON and Markdown exports without throwing fatal errors or halting partial exports.

---

## 4. API Endpoints

| Endpoint | Method | Response Type | Description |
|---|---|---|---|
| `/api/export/csv` | `GET` | `text/csv` | Streams RFC 4180 CSV export with 38 columns. Automatically saves copy to `data/exports/`. |
| `/api/export/json` | `GET` | `application/json` | Streams structured JSON dataset with metadata, validation, analytics, and observations. |
| `/api/export/report` or `/markdown` | `GET` | `text/markdown` | Streams comprehensive 12-section academic Markdown report. |
| `/api/export/pdf` | `GET` | `application/pdf` | Streams publication-grade ReportLab PDF research report. |
| `/api/export/validate` | `GET` | `application/json` | Returns validation audit summary without downloading export files. |

Query Parameters supported on all endpoints:
- `save=true` (default): Persists export artifact to `data/exports/`. Set `save=false` to stream purely in-memory.

---

## 5. Frontend User Experience

### 5.1 Export Actions Bar
- Styled with Obsidian Dark glassmorphism (`bg-slate-800/80 border border-slate-700/60 rounded-xl p-4`).
- Four action buttons with clear icons:
  - **Export CSV** (Green accent `#22c55e`)
  - **Export JSON** (Amber accent `#f59e0b`)
  - **Report (.md)** (Indigo accent `#6366f1`)
  - **Report (.pdf)** (Rose accent `#f43f5e`)
- Located in both:
  - Field Study Screen (`#view-field-study`): Header area directly below the title and progress bar.
  - Analytics Screen (`#view-analytics`): Header area directly below the analytics title and quota pill.

### 5.2 Interactive State Management
- **Busy State:** Clicking an export button disables the button, replaces its icon with a rotating SVG spinner, and dims its opacity.
- **Browser Download Trigger:** Converts API response to a `Blob` and triggers a native file download dialog.
- **Quota-Aware Toast Feedback:** On completion, displays a non-intrusive floating toast confirming the exported count and remaining items to reach the 50-website quota (e.g. *"Exported 7 observations. Field Study currently contains 7/50 observations (43 remaining to reach target quota)."*).

---

## 6. Verification & Test Suite

The export engine is tested via comprehensive test suites:
- `tests/test_export_service.py` (12 unit tests):
  - Validation engine with clean datasets, duplicates, score bounds, and invalid coordinates.
  - CSV schema conformity (all 38 columns present, proper RFC 4180 formatting).
  - JSON metadata, schema, and observation structure.
  - Markdown report generation (all 12 required sections present).
  - ReportLab PDF byte output validity (`%PDF` header verification).
  - Behavior under empty ($N=0$), partial ($1 \le N < 50$), and full ($N=50$) datasets.
  - Strict preservation of `UNKNOWN` values without fabrication.
  - Analytics consistency between Phase 20 service and export payloads.
  - Physical file persistence in `data/exports/`.
- `tests/test_api_server.py` (14 API integration tests):
  - `GET /api/export/csv`, `GET /api/export/json`, `GET /api/export/report`, `GET /api/export/pdf`, and `GET /api/export/validate`.
- **Regression Suite:** 156 passed, 60 subtests passed across the entire project test suite.
