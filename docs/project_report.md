# FIELD PROJECT REPORT

## Python-Based IP Address Tracker & Geolocation Tool
**A Controlled Field Study of Domain Resolution, Public IP Geolocation, and Network Infrastructure Across 50 Public Websites**

---

### TITLE PAGE PLACEHOLDERS

**Project Title:** Python-based IP Address Tracker & Geolocation Tool  
**Submitted by:** [Student Name]  
**Roll Number:** [Roll Number]  
**Course:** [Course Name]  
**Semester:** [Semester]  
**Department:** [Department / Field of Study]  
**College:** [College Name]  
**Academic Year:** [Academic Year]  
**Guided by:** [Teacher Name / Project Guide]  

---

## EXECUTIVE ABSTRACT

This project presents the design, implementation, and empirical evaluation of a desktop-based software application—the **IP Address Tracker & Geolocation Tool**—developed in Python 3. The software performs automated domain name validation, socket-based DNS resolution, HTTPS-based public IP geolocation, persistent local database logging, interactive OpenStreetMap visualization, and controlled batch field testing. 

To evaluate system performance and public web infrastructure patterns, a empirical field study was conducted across a fixed sample of **50 public websites** spanning 11 functional categories. The lookup pipeline executed sequentially, enforcing a deterministic IP selection rule (prioritizing the first valid IPv4 address returned by DNS) while preserving complete DNS address records.

Empirical results demonstrated a **98.0% DNS resolution success rate** (49/50 domains resolved), with a median DNS resolution latency of **22.27 ms** (Mean: 101.05 ms, IQR: 5.97 ms). Geolocation querying via the primary HTTPS provider (`ipapi.co`) achieved a median API latency of **80.75 ms**, resulting in a overall median pipeline execution time of **108.64 ms** (Mean: 358.00 ms). IPv4 addresses represented 98.0% of selected primary IPs. Observed geolocation data mapped public infrastructure across 4 distinct countries, with the United States representing the largest proportion of hosting registries (35 sites).

The report emphasizes that IP geolocation reflects regional network registry allocations rather than exact physical server locations or user coordinates. All unreturned database fields were preserved as explicit missing values (`"N/A"`) to maintain data integrity.

---

## 1. INTRODUCTION

### 1.1 Background & Context
The modern Internet relies on the Domain Name System (DNS) to translate human-readable domain names (such as `google.com`) into numeric IP addresses (such as `142.250.190.46`). Understanding where target servers reside and how network infrastructure is distributed across the globe is fundamental to network engineering, cybersecurity investigation, and internet research.

### 1.2 IP Geolocation Concepts
IP geolocation is the process of mapping a public IP address to geographic metadata, including country, region, city, coordinates (latitude/longitude), timezone, and network owner (ISP / Autonomous System Number). Geolocation databases compile data from Regional Internet Registries (RIRs such as ARIN, RIPE, APNIC), internet service providers, and BGP routing tables.

> **Crucial Distinction:** IP geolocation identifies **approximate network registry locations**. It does NOT provide GPS-level tracking, physical device location, or exact building addresses.

---

## 2. PROBLEM STATEMENT & OBJECTIVES

### 2.1 Problem Statement
While command-line tools such as `nslookup` or `dig` provide raw DNS records, students and analysts frequently lack a single, unified open-source tool that:
1. Validates user input before execution;
2. Performs DNS resolution and deterministic IP selection;
3. Retrieves structured geolocation and network metadata over secure HTTPS;
4. Logs lookup history to a safe local database;
5. Visualizes coordinates interactively;
6. Conducts reproducible batch field research across datasets.

### 2.2 Project Objectives
1. **Architecture & Modular Design:** Develop a clean, phase-structured Python architecture adhering to master specification [architecture.md](../architecture.md).
2. **Core Processing Engine:** Implement native domain/IP validation, socket DNS resolution, and HTTPS geolocation retrieval.
3. **Persistent Local Database:** Build safe SQLite CRUD routines using parameterized SQL query binding.
4. **Desktop GUI Console:** Construct a dark-themed desktop interface (`IP PULSE`) utilizing non-blocking daemon threads to prevent UI freezes.
5. **Interactive Mapping:** Integrate OpenStreetMap tile rendering with marker placement and coordinate validation.
6. **Field Study & Data Analysis:** Conduct a controlled 50-website experiment, collect standardized CSV observations, and generate descriptive statistical summaries and charts.

---

## 3. TECHNICAL BOUNDARIES & SCOPE

### 3.1 Included Scope
- Input validation for syntactically valid domains, IPv4, and IPv6 addresses.
- Socket-based DNS A/AAAA record resolution.
- HTTPS geolocation querying via `ipapi.co`.
- Parameterized SQLite local history storage (`data/ip_tracker.db`).
- Tkinter dark console UI with embedded OpenStreetMap view (`gui/map_view.py`).
- 50-website sequential batch field testing (`data/field_test/websites.csv`).
- Descriptive timing statistics and 7 matplotlib research plots (`data/analysis/charts/`).

### 3.2 Excluded Scope
- No GPS-level or physical device tracking.
- No live network packet capturing or sniffer functionality.
- No dynamic replacing of failed website observations during research runs.
- No fabrication or artificial padding of unreturned API attributes.

---

## 4. SYSTEM ARCHITECTURE & DATA FLOW

### 4.1 High-Level Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER (GUI)                         │
│   gui/main_window.py | gui/results_view.py | gui/history_view.py       │
│   gui/field_test_view.py | gui/analytics_view.py | gui/map_view.py       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ (Asynchronous Thread Call)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      SERVICE ORCHESTRATION LAYER                        │
│             services/lookup_service.py | services/field_test_service.py  │
└───────┬────────────────────────────┬────────────────────────────┬───────┘
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│ CORE ENGINE   │            │ DATABASE      │            │ ANALYSIS      │
│ validator.py  │            │ database/db.py│            │ analyzer.py   │
│ dns_resolver  │            │ models.py     │            │ visualizer.py │
│ geo_service   │            │ ip_tracker.db │            │ reports       │
│ normalizer.py │            └───────────────┘            └───────────────┘
└───────────────┘
```

---

## 5. TECHNICAL METHODOLOGY

### 5.1 Input Validation & Normalization (`core/validator.py`)
User inputs undergo whitespace trimming, lowercase conversion, and syntactic validation:
- **IPv4:** Evaluated using standard dotted-quad notation rules (4 octets, 0–255).
- **IPv6:** Evaluated using standard colon-hexadecimal notation rules.
- **Domain:** Evaluated against RFC-compliant domain regex (`^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$`).

### 5.2 DNS Resolution Engine (`core/dns_resolver.py`)
Performs address lookup using Python's standard `socket.getaddrinfo()`:
- Records timing in milliseconds using high-precision `time.perf_counter()`.
- Separates resolved IPs into `ipv4_addresses` and `ipv6_addresses` without duplicates.
- Categorizes DNS outcomes into `SUCCESS`, `DNS_FAILED`, or `INVALID_DOMAIN`.

### 5.3 Deterministic IP Selection Rule
When a domain name resolves to multiple IP addresses (e.g., due to Anycast or CDN load balancing):
1. The **first valid IPv4 address** in the resolved set is selected as `selected_ip`.
2. If no IPv4 address is present, the **first valid IPv6 address** is selected.
3. All returned IPv4 and IPv6 addresses are preserved in the result model.

### 5.4 Geolocation API Client (`core/geo_service.py`)
Queries `ipapi.co` over HTTPS using standard library `urllib.request`:
- Configured with explicit timeout bounds (5.0s) and User-Agent headers.
- Handles HTTP status codes: HTTP 429 (Rate Limit), HTTP 401/403 (Auth Error), HTTP 500 (Server Error).
- Maps raw JSON responses into an internal normalized `GeoResult` dataclass via `core/normalizer.py`.

---

## 6. FIELD-TEST EXPERIMENT & EMPIRICAL RESULTS

### 6.1 Sample Design
The field test evaluated **50 predefined public websites** across 11 categories: Search, Technology, Social Media, E-commerce, Reference, Education, News, Government, Finance, Entertainment, and Cloud Services (`data/field_test/websites.csv`).

### 6.2 Empirical Summary Table

| Parameter / Metric | Empirical Value |
|---|---|
| **Total Test Dataset Size** | 50 Public Websites |
| **DNS Resolution Success Rate** | **98.0%** (49/50 domains resolved) |
| **Selected IP Protocol Ratio** | IPv4: 98.0% (49/50) \| IPv6: 0.0% (0/50) |
| **Unique Countries Identified** | 4 Distinct Geolocation Countries |
| **Primary Country Representation** | United States (35 sites), India, Germany |
| **Median DNS Latency** | **22.27 ms** (IQR: 5.97 ms) |
| **Median Geolocation API Latency** | **80.75 ms** (IQR: 277.48 ms) |
| **Median Total Pipeline Latency** | **108.64 ms** (IQR: 353.58 ms) |

### 6.3 Timing Performance Descriptive Statistics

| Metric | Sample Size | Mean (ms) | Std Dev (ms) | Min (ms) | P25 (ms) | Median (ms) | P75 (ms) | Max (ms) | IQR (ms) |
|---|---|---|---|---|---|---|---|---|---|
| **DNS Resolution** | 50 | 101.05 | 258.69 | 12.00 | 21.09 | **22.27** | 27.06 | 1321.91 | 5.97 |
| **Geolocation API** | 50 | 256.55 | 336.38 | 0.00 | 64.50 | **80.75** | 341.98 | 1593.56 | 277.48 |
| **Total Pipeline** | 50 | 358.00 | 481.96 | 73.84 | 90.12 | **108.64** | 443.69 | 2915.82 | 353.58 |

*Note: Median latency is reported as the primary metric of central tendency because network response distributions exhibit characteristic right-skewness caused by occasional transient latencies.*

---

## 7. ETHICAL & PRIVACY CONSIDERATIONS

1. **Public Information Usage:** The software queries publicly routable IP addresses and DNS A/AAAA records. It does not access private networks or personal identifiers.
2. **Responsible API Usage:** Sequential batch execution incorporates request delays (0.5s) to adhere strictly to external provider rate limits.
3. **No GPS-Level Tracking:** Geolocation data represents corporate network registration blocks and is explicitly documented as approximate.

---

## 8. SOFTWARE TESTING & QUALITY ASSURANCE

Automated unit and integration tests were developed using Python's native `unittest` framework:
- **Test Suite Files:** 9 test modules in `tests/` (`test_validator`, `test_dns_resolver`, `test_geo_service`, `test_normalizer`, `test_lookup_service`, `test_database`, `test_map_view`, `test_field_test_service`, `test_analysis`).
- **Total Executed Tests:** **54 unit/integration test cases**.
- **Pass Rate:** **100% passing** (0 failures, 0 errors in 3.697 seconds).

---

## 9. CONCLUSION & FUTURE SCOPE

### 9.1 Conclusion
The **IP Address Tracker & Geolocation Tool** successfully fulfills all architectural objectives specified in [architecture.md](../architecture.md). The application provides a robust, dark-themed desktop interface for single-target intelligence lookups as well as automated 50-website batch field research. Empirical field study results demonstrate fast median DNS resolution (22.27 ms) and API latency (80.75 ms), proving the system's efficiency, reliability, and academic utility.

### 9.2 Future Scope
1. **Multi-Provider Failover:** Support automatic dynamic fallback across multiple geolocation APIs (e.g., ipinfo.io, MaxMind GeoIP2).
2. **BGP & ASN Route Analysis:** Integrate Autonomous System path tracing and BGP route origin validation.
3. **Web Application Deployment:** Port the Tkinter interface to a lightweight web console using FastAPI/React.

---

## 10. REFERENCES

1. **RFC 1035:** Mockapetris, P. (1987). *Domain Names - Implementation and Specification*. Internet Engineering Task Force (IETF).
2. **Python Software Foundation:** Python 3.14 Standard Library Documentation (`socket`, `urllib.request`, `sqlite3`, `tkinter`).
3. **ipapi.co Documentation:** *IP Address Geolocation API Specification*. HTTPS REST Service Guidelines.
4. **Matplotlib & Pandas:** Hunter, J. D. (2007). *Matplotlib: A 2D Graphics Environment*. Computing in Science & Engineering.
