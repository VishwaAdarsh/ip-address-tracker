# IP PULSE — Phase 19: 50-Site Intelligence Field Study Upgrade
## Academic Methodology & Architectural Specification

**Project:** IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform  
**Component:** 50-Site Empirical Field Study Upgrade  
**Modules:** `database/models.py`, `database/db.py`, `services/field_test_service.py`, `api/server.py`  
**Frontend Views:** `#results-action-bar` ("Add to Field Study"), `#view-field-study` (Obsidian Telemetry Dashboard), `#field-study-detail-modal`  
**Database Table:** `field_study_observations` (26 structured telemetry attributes)  
**API Endpoints:** `POST /api/field-study/add`, `GET /api/field-study`, `GET /api/export/csv?type=field-study`, `POST /api/field-study/complete-remaining`  

---

## 1. Executive Summary & Research Protocol

In compliance with empirical network research guidelines and academic field test requirements (*"Field test on 50 websites and analyze results"*), Phase 19 transforms the legacy ad-hoc field test into an intentional, reproducible, and verifiable **50-Website Intelligence Field Study**.

### Core Operational Principles
1. **Manual-First Protocol:** The platform strictly adheres to a manual-first paradigm. Opening the Field Study view does not trigger automated queries or background network scans. Automated completion remains an explicit, user-authorized fallback available only when sample quota $N < 50$.
2. **Intentional Sample Curation:** Normal lookup activity is logged in the general lookup history table (`history`). Curated research samples enter the scientific study only through deliberate user action (the **"Add to Field Study"** action bar in Home/Dashboard results) or controlled dataset completion.
3. **Strict Deduplication:** An empirical study on 50 websites requires 50 distinct domain entities. Re-evaluating the same domain (across protocol variations, ports, subpaths, or URL queries) updates observation telemetry rather than inflating the sample quota count.
4. **Deterministic Evidence Attribution:** Observations record concrete observables across identity, geolocation, network infrastructure, transport security, and deterministic trust/risk ratings without synthetic data inflation. Missing or unresolvable attributes remain explicitly labeled as `"Unknown"` or `"N/A"`.

---

## 2. Architectural Schema & Data Retention

The field study preserves a dedicated, backward-compatible SQLite table named `field_study_observations` inside `data/ip_tracker.db`. When initialized, existing unique historical domains are migrated into the field study without record loss or table drop.

### 26 Standardized Field Observation Attributes

| # | Attribute Name | Type | Telemetry Classification | Description / Academic Role |
|---|---|---|---|---|
| 1 | `id` | INTEGER PK | Metadata | Unique SQLite observation row identifier |
| 2 | `test_id` | INTEGER | Metadata | Sample index counter ($1 \dots 50$) |
| 3 | `domain` | TEXT | Target Identity | Normalized fully qualified domain name (FQDN) |
| 4 | `category` | TEXT | Target Identity | Website category (e.g. Search, Education, E-Commerce) |
| 5 | `resolved_ip` | TEXT | Target Identity | Selected IPv4 or IPv6 IP address resolved via DNS |
| 6 | `ip_version` | TEXT | Target Identity | IP version identifier (`IPv4` or `IPv6`) |
| 7 | `country` | TEXT | Geolocation | Country name resolved from GeoIP telemetry |
| 8 | `country_code` | TEXT | Geolocation | ISO 3166-1 alpha-2 country code (e.g. `US`, `IN`, `DE`) |
| 9 | `region` | TEXT | Geolocation | State, province, or administrative subdivision |
| 10 | `city` | TEXT | Geolocation | Municipal city name |
| 11 | `latitude` | REAL | Geolocation | WGS84 geographic coordinate latitude |
| 12 | `longitude` | REAL | Geolocation | WGS84 geographic coordinate longitude |
| 13 | `timezone` | TEXT | Geolocation | Timezone identifier (e.g. `America/New_York`) |
| 14 | `geolocation_confidence` | TEXT | Geolocation | Telemetry confidence assessment (`HIGH`, `MEDIUM`, `UNKNOWN`) |
| 15 | `asn` | TEXT | Network & Infra | Autonomous System Number (e.g. `AS15169`) |
| 16 | `organization` | TEXT | Network & Infra | BGP Autonomous System entity or registered owner |
| 17 | `isp` | TEXT | Network & Infra | Internet Service Provider delivering transit |
| 18 | `network_type` | TEXT | Network & Infra | Network classification (`Commercial`, `Hosting`, `Residential`) |
| 19 | `infrastructure_type` | TEXT | Network & Infra | Infrastructure type (`Cloud / Datacenter`, `CDN`, `Standard`) |
| 20 | `https_status` | TEXT | Transport Security | HTTPS protocol availability (`Enabled`, `Disabled`, `Unknown`) |
| 21 | `tls_status` | TEXT | Transport Security | X.509 TLS certificate validity (`Valid`, `Invalid`, `Unknown`) |
| 22 | `vpn_status` | TEXT | Threat Intel | VPN proxy egress detection flag (`DETECTED`, `NOT_DETECTED`) |
| 23 | `proxy_status` | TEXT | Threat Intel | HTTP/SOCKS open proxy detection flag |
| 24 | `tor_status` | TEXT | Threat Intel | Onion routing exit relay status (`DETECTED`, `NOT_DETECTED`) |
| 25 | `website_trust_score` | REAL | Scoring Engine | Deterministic cryptographic posture score ($0 \dots 100$) |
| 26 | `website_trust_classification` | TEXT | Scoring Engine | Qualitative trust tier (`LIKELY SAFE`, `GENERALLY SAFE`, etc.) |
| 27 | `ip_risk_score` | REAL | Scoring Engine | Deterministic infrastructure risk score ($0 \dots 100$) |
| 28 | `ip_risk_classification` | TEXT | Scoring Engine | Qualitative risk tier (`LOW RISK`, `MODERATE`, `HIGH RISK`) |
| 29 | `score_confidence` | TEXT | Scoring Engine | Scoring confidence level (`HIGH`, `MEDIUM`, `LOW`) |
| 30 | `evidence_coverage` | REAL | Scoring Engine | Available signal ratio ($0.0 \dots 1.0$) |
| 31 | `dns_response_time_ms` | REAL | Latency | Authoritative DNS resolution latency in milliseconds |
| 32 | `api_response_time_ms` | REAL | Latency | Telemetry API query round-trip latency in milliseconds |
| 33 | `observation_status` | TEXT | Metadata | Lifecycle flag (`RECORDED`, `VERIFIED`, `INCOMPLETE`) |
| 34 | `observed_at` | TEXT | Metadata | ISO 8601 UTC timestamp of empirical capture |

---

## 3. Workflow Integration & Deduplication Policy

### Domain Normalization Pipeline (`normalize_field_domain`)
To prevent duplicate cohort entries caused by superficial URL formatting differences, the system implements RFC 3986 URL parsing:
$$\text{URL} \longrightarrow \text{lowercase} \longrightarrow \text{strip scheme } (\texttt{http://}, \texttt{https://}) \longrightarrow \text{strip port} \longrightarrow \text{strip path/queries} \longrightarrow \text{canonical FQDN}$$

Examples:
- `https://www.google.com/` $\longrightarrow$ `www.google.com`
- `http://GITHUB.COM:443/features` $\longrightarrow$ `github.com`
- `cloudflare.com?source=test#node` $\longrightarrow$ `cloudflare.com`

### Verification of Duplicate Policy
If a normalized domain is already recorded in `field_study_observations`:
- Attempting to add via `POST /api/field-study/add` returns HTTP status `409 Conflict` with `{"duplicate": true, "message": "Domain '...' is already recorded in the 50-Site Field Study."}`.
- Existing records are never duplicated, preserving the integrity of the sample denominator.

---

## 4. UI/UX Implementation (Stitch Obsidian Dark)

The Field Study view (`#view-field-study`) features:
1. **Dynamic Progress Indicator:** Displays current sample count ($X / 50$), completion percentage ($\%$), and status badge (`TARGET REACHED` or `X% COMPLETE`).
2. **Compact Research Summary:** 4 high-level metric cards:
   - **Websites Tested:** Current sample size vs 50 target.
   - **HTTPS Adoption:** Percentage of observed endpoints serving valid TLS/HTTPS.
   - **Average Trust Score:** Mean deterministic trust rating across cohort.
   - **Average IP Risk:** Mean infrastructure risk rating across cohort.
3. **Secondary Telemetry Strip:** Displays dominant hosting provider, cloud-vs-traditional hosting ratio, and threat detection totals (VPN, Proxy, Tor).
4. **9-Column Observation Table:** Detailed tabular view (`#`, `Domain`, `IP Address`, `Country`, `Infrastructure`, `HTTPS`, `Trust`, `Risk`, `Observed`).
5. **Observation Detail Modal:** Clicking any row opens `#field-study-detail-modal`, displaying all 26 attributes partitioned into 5 clean visual sections:
   - Target Identity
   - Geolocation Telemetry
   - Network & Infrastructure
   - Security Intelligence
   - Deterministic Scoring & Latency Telemetry

---

## 5. Verification Matrix (16 Scenarios)

All 16 required verification scenarios are tested in `tests/test_field_test_service.py` and pass 100%:

| Test Scenario | Purpose | Result |
|---|---|---|
| 1. Add Valid Observation | Persists all 26 attributes accurately to SQLite | PASS |
| 2. Reject Invalid Observation | Rejects empty strings, unresolved IPs, invalid inputs | PASS |
| 3. Duplicate Domain Rejection | Prevents duplicate domain inflation | PASS |
| 4. Domain Normalization | Normalizes schemes, ports, subpaths, casing | PASS |
| 5. Accurate Progress Calculation | Computes percentage and remaining accurately (e.g. 42/50 = 84%) | PASS |
| 6. 50-Site Target Logic | Verifies target reached behavior at $N = 50$ | PASS |
| 7. Target Reached State | Disables automatic completion once quota fulfilled | PASS |
| 8. Unknown Security Fields | Defaults unknown security telemetry cleanly | PASS |
| 9. Missing Geolocation | Handles null coordinates/country without exceptions | PASS |
| 10. Missing Infrastructure | Handles missing ASN/ISP/Org gracefully | PASS |
| 11. Missing Trust Score | Allows fallback without analytical failures | PASS |
| 12. Missing Risk Score | Allows fallback without analytical failures | PASS |
| 13. Backward Compatibility | Legacy property aliases (`ip_address`, `status`) work seamlessly | PASS |
| 14. History vs Study Separation | Casual lookups do not pollute curated field study | PASS |
| 15. Manual-First Behavior | Status check does not trigger automated network queries | PASS |
| 16. Optional Auto-Completion | Fulfills exactly remaining sites up to target 50 | PASS |
