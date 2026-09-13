# Phase 24: Advanced Visualization & Research Dashboard

## 1. Executive Summary

Phase 24 delivers the **Advanced Visualization & Research Dashboard** for IP PULSE ("IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform").

Operating strictly as an analytical presentation and research visualization suite within `#view-analytics`, this dashboard renders empirical distributions, statistical metrics, infrastructure telemetry, and interactive maps using **ONLY existing real Field Study and analytics data**.

### Core Architectural Guarantees
- **Strictly Read-Only:** Zero synthetic data generation, zero score manipulation, zero secondary scoring engines, and zero automated web re-scanning.
- **Single Source of Truth:** Operates exclusively within the established repository root (`ip-address-tracker`) and SQLite database (`data/ip_tracker.db`).
- **Field Study Progress Component:** Displays target sample quota (50), collected observations count, remaining observations needed, percentage complete, visual progress bar, quota fulfillment badge, valid observations count, and failed observations count.
- **Mathematical Equivalence:** When no filters are active, dashboard statistics are **100% identical** to Phase 20 analytics output.
- **Interactive Multi-Factor Filtering:** Non-destructive in-memory cohort filtering across 7 dimensions (Country, Infrastructure Type, Trust Classification, Risk Classification, HTTPS Status, IP Version, and Observation Scope/Range). Dropdown options are dynamically populated strictly from distinct real database values.
- **Interactive Leaflet Geographic Mapping:** Embedded map (`#analytics-map`) plots valid coordinates (`lat ∈ [-90, 90], lon ∈ [-180, 180]`), with dark CartoDB tiles, custom cyan glowing markers, information popups, auto-scaling `fitBounds()`, and an explicit missing coordinates counter.
- **Neutrality on Unknowns:** Endpoints with unknown/untested HTTPS or TLS status are rendered visually neutral (never assumed insecure).
- **Graceful Data States:** Supports full loading skeletons, empty database state, partial cohort state, target-fulfilled state (N >= 50), filter-empty state (zero filter matches with one-click reset), and error fallback.

---

## 2. Architecture & Data Flow

```
+----------------------------------------------------------------------------------------------------+
|                                    STITCH WEB FRONTEND (SPA)                                       |
|                                 #view-analytics (Research Dashboard)                              |
+----------------------------------------------------------------------------------------------------+
       |                                       |                                       |
  [Filter Toolbar]                    [Fetch Cohort Analytics]                   [Leaflet Map & DOM]
  - Country, Infra, Trust, Risk,       - GET /api/analytics?<query>              - Render 7 sections
    HTTPS, IP Version, Scope           - POST /api/analytics {filters}           - Auto-fit map bounds
  - Dynamic select options             - Synchronous execution                   - Dual histograms
       |                                       |                                       |
       v                                       v                                       v
+----------------------------------------------------------------------------------------------------+
|                                      API LAYER (api/server.py)                                     |
|                                       GET & POST /api/analytics                                    |
|                                  GET /api/status (capability flag)                                 |
+----------------------------------------------------------------------------------------------------+
                                               |
                                               v
+----------------------------------------------------------------------------------------------------+
|                              ANALYTICS SERVICE (services/analytics_service.py)                     |
|                                                                                                    |
|  1. extract_filter_options(records)                                                                |
|     - Extracts distinct countries, infrastructures, classes, versions from real SQLite records     |
|                                                                                                    |
|  2. apply_observation_filters(records, filters)                                                    |
|     - Non-destructive filtering by country, infra, trust class, risk class, https, ip_ver, range   |
|     - Returns (filtered_records, is_filtered, active_filters_summary)                              |
|                                                                                                    |
|  3. extract_map_coordinates_for_analytics(records)                                                 |
|     - Validates latitude ∈ [-90, 90] and longitude ∈ [-180, 180]                                  |
|     - Returns (map_points, mapped_count, missing_count)                                            |
|                                                                                                    |
|  4. compute_field_study_analytics(records, filters)                                                |
|     - Extended with filters & records parameters                                                   |
|     - Generates univariate stats, 5-bracket histograms, security, network, geo, ASN, & insights   |
|     - Appends Phase 24 metadata: is_filtered, unfiltered_total_count, filtered_count, map_points   |
+----------------------------------------------------------------------------------------------------+
                                               |
                                               v
+----------------------------------------------------------------------------------------------------+
|                                  DATABASE LAYER (database/db.py)                                   |
|                             field_study_observations table in SQLite                               |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Visualization Dashboard Sections

| Section | Title | Visualizations & Metrics |
|---|---|---|
| **Header** | Quota & Telemetry | Live N counter, incomplete/achieved badge, CSV/JSON/MD/PDF export buttons |
| **Progress** | Field Study Quota | Observations (X / 50), remaining needed, % complete, visual bar, valid/failed pills |
| **Toolbar** | Interactive Filters | 7 dropdowns (Country, Infra, Trust, Risk, HTTPS, IP Version, Scope), Reset, active filter pill |
| **Section 1** | Field Study Overview | 4 Glass KPI cards: Sample size, HTTPS adoption %, Mean Trust Score, Mean IP Risk |
| **Section 2** | Trust & Risk Analysis | Dual 5-bracket vertical histograms (0-20, 21-40, 41-60, 61-80, 81-100) with hover tooltips and classification badges |
| **Section 3** | Security & Transport | HTTPS enabled/disabled/unknown breakdown with visual distribution bars; TLS validity breakdown |
| **Section 4** | Infrastructure & Network | IPv4 vs IPv6 ratios, mean DNS/API query latencies, cloud datacenter hosting %, threat node tallies (VPN, Proxy, Tor) |
| **Section 5** | Geographic Analysis | Embedded Leaflet map (`#analytics-map`) with glowing coordinate pins, popups, auto-bounding, coordinate stats, and top countries breakdown |
| **Section 6** | Network Ownership | Top BGP Autonomous Systems and Organizations; 6 deterministic empirical research insights |
| **Section 7** | Cohort Rankings | Comparative ranking tables: Top 5 Highest Trust sites, Top 5 Highest Risk sites |

---

## 4. API Specification

### `GET /api/analytics`
Fetches analytics for the complete field study or a filtered cohort.

**Query Parameters (Optional):**
- `country`: Filter by country name or code (case-insensitive)
- `infrastructure`: Filter by infrastructure type (case-insensitive substring)
- `trust_class`: Filter by trust classification (e.g. `Highly Trusted`, `Moderate Trust`)
- `risk_class`: Filter by risk classification (e.g. `Minimal Risk`, `High Risk`)
- `https_status`: Filter by `Enabled`, `Disabled`, or `Unknown`
- `ip_version`: Filter by `IPv4` or `IPv6`
- `range`: Filter by scope (`recent_10`, `recent_25`, `first_25`, `all`)

**Response Schema:**
```json
{
  "success": true,
  "is_filtered": false,
  "unfiltered_total_count": 50,
  "filtered_count": 50,
  "filter_summary": {},
  "available_filter_options": {
    "countries": ["France", "Germany", "United States"],
    "infrastructures": ["Cloud / Datacenter", "Hosting / ISP"],
    "trust_classes": ["Highly Trusted", "Trusted", "Untrusted"],
    "risk_classes": ["Minimal Risk", "Low Risk", "High Risk"],
    "ip_versions": ["IPv4", "IPv6"],
    "https_statuses": ["Enabled", "Disabled", "Unknown"],
    "ranges": [...]
  },
  "map_points": [
    {
      "id": 1,
      "domain": "google.com",
      "ip": "142.250.190.46",
      "latitude": 37.422,
      "longitude": -122.084,
      "country": "United States",
      "city": "Mountain View",
      "organization": "Google LLC",
      "infrastructure": "Cloud / Datacenter",
      "trust_score": 85.0,
      "risk_score": 10.0
    }
  ],
  "mapped_points_count": 48,
  "missing_coordinates_count": 2,
  "overview": {
    "total_observations": 50,
    "sample_target": 50,
    "remaining_to_target": 0,
    "collection_progress_pct": 100.0,
    "target_reached": true,
    "https_adoption_pct": 92.0,
    "mean_trust_score": 81.4,
    "mean_risk_score": 14.8
  },
  "trust_analysis": { ... },
  "risk_analysis": { ... },
  "security_analysis": { ... },
  "network_analysis": { ... },
  "geographic_and_asn_distribution": { ... },
  "research_insights": [ ... ],
  "comparison_analytics": { ... }
}
```

### `POST /api/analytics`
Alternative endpoint for filtering via JSON payload (`{"filters": { ... }}`).

---

## 5. Verification & Testing

The Phase 24 implementation is validated by a 20-test dedicated suite in `tests/test_visualization_dashboard.py` and 2 integration tests in `tests/test_api_server.py`:
1. **Filter Tests:** Country, infrastructure, trust class, risk class, HTTPS status, IP version, range, combined multi-filters, and non-existent filter queries.
2. **Coordinate Tests:** Valid bounds checking (`[-90, 90]`, `[-180, 180]`), invalid coordinate rejection, and missing coordinate counters.
3. **Equivalence Tests:** Strict verification that unfiltered dashboard output is 100% mathematically equal to Phase 20 analytics.
4. **Data State Tests:** Empty database, zero-match filter cohorts, and partial cohorts.
5. **API Tests:** Query parameters, POST payloads, and `/api/status` capability verification.
