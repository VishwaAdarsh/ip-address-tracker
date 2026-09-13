# Phase 23: Intelligence Comparison & Investigation Workspace

## 1. Executive Summary

Phase 23 delivers a dedicated, lightweight **Intelligence Comparison & Investigation Workspace** (`#view-investigation`) for the IP PULSE platform ("IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform"). 

Operating strictly as an analytical workbench, this workspace empowers analysts to compare between **2 (minimum) and 5 (maximum)** existing intelligence observations side-by-side across multidimensional telemetry—encompassing identity, autonomous routing, physical geography, transport security, anonymizer detections, explainable risk scores, and intelligence chain summaries.

### Core Architectural Guarantees
- **Strictly Read-Only:** The comparison engine performs **zero** network re-scanning, **zero** database mutations, and **zero** modifications to the 50-site Field Study dataset.
- **Score & Telemetry Preservation:** Website Trust Scores, IP Risk Scores, classifications, and observed attributes are never recalculated or modified during comparison.
- **Rigorous Input Boundary Validation:** Exactly 2 to 5 observations are allowed; duplicate domain selections (case-insensitive) are strictly blocked with explicit actionable error messages.
- **Deterministic Analytics:** Extreme values (highest/lowest trust/risk), commonalities, HTTPS adoption rates, and anonymizer counts are computed deterministically. If no unanimous commonality exists across all compared items, the engine reports `"No common value detected."` without guesswork.
- **Factual Difference Highlights:** Generates factual statements identifying empirical divergences (geography, ASN, transport encryption, infrastructure classification, and score spread) without speculative causation or threat conjecture.
- **Multi-Point Leaflet Visualization:** Automatically aggregates and renders markers for all valid geographic coordinates, centering and scaling via Leaflet's `fitBounds()`.
- **Optional Comparative AI Explanation:** Leverages Phase 22 provider abstraction (Rule-Based Factual Engine or Gemini) to generate comparative syntheses strictly sanitized against absolute security claims.
- **Export Capabilities:** Reuses Phase 21 export services to provide clean CSV and JSON downloads of the active comparison dataset.
- **Client-Side Analyst Notes:** An in-session scratchpad allows analysts to record investigative thoughts without polluting the backend database.

---

## 2. Architecture & Data Flow

```
+----------------------------------------------------------------------------------------------------+
|                                    STITCH WEB FRONTEND (SPA)                                       |
|                                    #view-investigation (Workspace)                                 |
+----------------------------------------------------------------------------------------------------+
       |                                       |                                       |
  [Select 2-5 Items]                   [Run Comparison]                         [Explain / Export]
  - Field Study candidate modal         - POST /api/compare                      - POST /api/compare/explain
  - History candidate modal             - Synchronous execution                  - POST /api/compare/export
  - Current Scan insertion              - Non-destructive                        - GET /api/compare/export
       |                                       |                                       |
       v                                       v                                       v
+----------------------------------------------------------------------------------------------------+
|                                      API LAYER (api/server.py)                                     |
|  GET /api/compare/candidates | POST /api/compare | POST /api/compare/explain | POST /api/compare/export|
+----------------------------------------------------------------------------------------------------+
                                               |
                                               v
+----------------------------------------------------------------------------------------------------+
|                             COMPARISON SERVICE (services/comparison_service.py)                    |
|                                                                                                    |
|  1. normalize_comparison_item()                                                                    |
|     - Standardizes FieldObservation, LookupRecord, or raw dict to NormalizedComparisonItem         |
|                                                                                                    |
|  2. execute_comparison(raw_items)                                                                  |
|     - Boundary checks: 2 <= len(items) <= 5                                                        |
|     - Duplicate domain prevention                                                                  |
|     - compute_comparison_statistics() [Deterministic extremes, commonalities, adoption rates]      |
|     - compute_difference_highlights()  [Factual divergence statements]                            |
|     - extract_map_coordinates()       [Filters valid lat/lon [-90..90, -180..180]]                 |
|                                                                                                    |
|  3. generate_comparison_ai_explanation()                                                           |
|     - Synthesizes infrastructure, security, and score divergences                                  |
|     - Sanitizes absolute claims ("100% safe", "definitely malicious")                              |
+----------------------------------------------------------------------------------------------------+
                                               |
                                               v
+----------------------------------------------------------------------------------------------------+
|                                 STITCH UI STRUCTURED RENDERING                                     |
|  - Multi-Column Side-by-Side Comparison Matrix (Identity, Network, Geo, Sec, Intel, Risk, Chain)   |
|  - Key Deterministic Commonalities & Adoption Metrics Grid                                         |
|  - Factual Difference Highlights Panel                                                             |
|  - Multi-Point Leaflet Map with Interactive Popups & Dynamic fitBounds()                            |
|  - Comparative AI Synthesis Panel with Authoritative Deterministic Limitations                     |
|  - In-Session Investigation Notes Scratchpad (Client-side localStorage/session memory)             |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Side-by-Side Comparison Matrix Schema

Each compared observation is normalized into a `NormalizedComparisonItem` containing standardized dimensions:

| Category | Attributes Included | Unmeasured Fallback |
|---|---|---|
| **Identity** | Domain, Resolved IP, IP Version, Source (Field Study / History / Current) | `UNKNOWN` |
| **Network** | ASN, Organization, ISP, Network Type, Infrastructure Type | `UNKNOWN` |
| **Location** | Country, Region, City, Latitude, Longitude, Geolocation Confidence | `UNKNOWN` / `None` |
| **Security** | HTTPS Status, Redirect Status, TLS Status, TLS Version, TLS Issuer, Expiry Days | `UNKNOWN` |
| **IP Intel** | Commercial VPN, Public Proxy, Tor Exit Node, Datacenter / Hosting IP | `UNKNOWN` |
| **Risk** | Website Trust Score & Class, IP Risk Score & Class, Confidence, Coverage | `UNKNOWN` / `None` |
| **Intelligence**| IP Personality Profile, Intelligence Chain Summary, Observation Timestamp | `UNKNOWN` |

---

## 4. API Specification

### 4.1. `GET /api/compare/candidates`
Returns candidate observations currently present in the SQLite database (Field Study and History) formatted for quick selection.
- **Request:** No parameters required.
- **Response:**
  ```json
  {
    "count": 52,
    "candidates": [
      {
        "id": 1,
        "source": "field_study",
        "domain": "google.com",
        "ip_address": "142.250.190.46",
        "country": "United States",
        "asn": "AS15169",
        "organization": "Google LLC",
        "trust_score": 95.0,
        "risk_score": 5.0,
        "timestamp": "2026-09-13T12:00:00Z",
        "badge": "Field Study"
      }
    ]
  }
  ```

### 4.2. `POST /api/compare`
Executes multi-observation normalization, deterministic statistics calculation, difference highlights generation, and map coordinate extraction.
- **Payload:**
  ```json
  {
    "observations": [
      { "domain": "siteA.com", "resolved_ip": "1.1.1.1", ... },
      { "domain": "siteB.com", "resolved_ip": "8.8.8.8", ... }
    ]
  }
  ```
- **Response (Success):**
  ```json
  {
    "success": true,
    "count": 2,
    "observations": [ ... ],
    "statistics": {
      "count": 2,
      "highest_trust_score": { "domain": "siteA.com", "score": 92.0 },
      "lowest_trust_score": { "domain": "siteB.com", "score": 85.0 },
      "highest_ip_risk_score": { "domain": "siteB.com", "score": 15.0 },
      "lowest_ip_risk_score": { "domain": "siteA.com", "score": 10.0 },
      "common_asn": "No common value detected.",
      "common_country": "United States",
      "https_adoption": { "enabled_count": 2, "total_count": 2, "percentage": 100.0, "formatted": "2 of 2 (100.0%) enforced" },
      "anonymizer_detections": { "vpn_count": 0, "proxy_count": 0, "tor_count": 0, "total_anonymizers": 0 }
    },
    "differences": [
      "Geographic convergence: All observations geolocate within United States.",
      "Autonomous System divergence: Targets route through 2 distinct ASNs."
    ],
    "map_points": [
      { "domain": "siteA.com", "latitude": 37.77, "longitude": -122.41, ... },
      { "domain": "siteB.com", "latitude": 37.42, "longitude": -122.08, ... }
    ]
  }
  ```
- **Response (Error):** Returns HTTP 400 with `error` string and error code (`INSUFFICIENT_OBSERVATIONS`, `EXCEEDED_MAX_OBSERVATIONS`, `DUPLICATE_SELECTION`).

### 4.3. `POST /api/compare/explain`
Produces an evidence-grounded comparative AI explanation synthesizing infrastructure, security, and score discrepancies across the compared targets.
- **Response:**
  ```json
  {
    "status": "success",
    "provider": "rule_based",
    "domains": ["siteA.com", "siteB.com"],
    "summary": "...",
    "infrastructure_comparison": "...",
    "security_comparison": "...",
    "key_differences": [ ... ],
    "takeaway": "...",
    "limitations": "AI comparison explains empirical telemetry recorded at test execution time..."
  }
  ```

### 4.4. `POST /api/compare/export` & `GET /api/compare/export`
Exports compared observation data as RFC 4180 CSV or structured JSON by reusing Phase 21 export routines without duplicating schema serializers.

---

## 5. Verification & Testing

The investigation workspace is thoroughly covered by automated test suites:
- `tests/test_comparison_service.py`: 17 unit tests covering normalization, validation limits, duplicate rejections, deterministic statistics calculations, factual difference generator, coordinate extraction, and claim sanitization.
- `tests/test_api_server.py`: Integration tests 18–22 covering candidates lookup, comparison execution, validation error handling, AI comparative explanation, and export streaming (CSV and JSON).
