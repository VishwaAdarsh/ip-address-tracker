# Comprehensive Viva Question Bank with Technical Answers

This document provides a complete viva question bank for the **Python-based IP Address Tracker & Geolocation Tool**, organized into 10 thematic categories with clear, concise, and technically accurate answers.

---

## SECTION A: BASIC CONCEPTS

### Q1: What is an IP address, and how does it differ from a MAC address?
- **Short answer:** An IP address is a logical network address used to route data across connected networks, whereas a MAC address is a permanent physical identifier assigned to a network interface card (NIC).
- **Technical explanation:** An IP address (IPv4 32-bit or IPv6 128-bit) operates at Layer 3 (Network Layer) of the OSI model and changes based on network location. A MAC address operates at Layer 2 (Data Link Layer) and remains burned into hardware.

### Q2: What is the Domain Name System (DNS)?
- **Short answer:** DNS is a distributed hierarchical database that translates human-readable domain names (e.g., `google.com`) into computer-routable IP addresses (e.g., `142.250.190.46`).
- **Technical explanation:** DNS operates on port 53 (UDP/TCP). Clients query recursive DNS resolvers, which consult root, top-level domain (TLD), and authoritative name servers to resolve A records (IPv4) or AAAA records (IPv6).

### Q3: What is the difference between IPv4 and IPv6?
- **Short answer:** IPv4 uses 32-bit addresses providing ~4.3 billion unique IPs, while IPv6 uses 128-bit hexadecimal addresses providing virtually unlimited addresses (\(3.4 \times 10^{38}\)).
- **Technical explanation:** IPv4 is written in dotted-quad notation (e.g., `192.168.1.1`). IPv6 is written in colon-separated hexadecimal groups (e.g., `2001:db8::1`). IPv6 includes native IPSec support and eliminates the need for Network Address Translation (NAT).

---

## SECTION B: PYTHON IMPLEMENTATION

### Q4: How is the application architecture structured in Python?
- **Short answer:** It follows a 4-tier modular architecture: Presentation (`gui/`), Service Orchestration (`services/`), Core Processing (`core/`), Database Storage (`database/`), and Data Analysis (`analysis/`).
- **Technical explanation:** The architecture enforces strict separation of concerns. GUI frames invoke high-level service functions (`perform_lookup`), which call specialized core functions (`resolve_domain`, `get_geolocation`). Presentation code contains zero direct socket or SQL logic.

### Q5: How are network operations executed without freezing the Tkinter GUI?
- **Short answer:** Network operations run in non-blocking background daemon threads using Python's `threading.Thread` module.
- **Technical explanation:** Tkinter runs a single-threaded event loop (`mainloop()`). Blocking network calls executed on the main thread cause UI freezes. By running lookups inside `threading.Thread(target=..., daemon=True).start()`, network execution occurs asynchronously, scheduling UI updates back to the main thread via `widget.after()`.

### Q6: How are environment configuration variables loaded in this project?
- **Short answer:** Environment variables are loaded dynamically from `.env` files using custom file parsing in `config/settings.py` with fallback defaults.
- **Technical explanation:** `config/settings.py` reads `.env` key-value pairs into `os.environ`. If `.env` is absent, settings default safely (e.g. `GEO_PROVIDER_NAME = "ipapi.co"`), allowing free tier operation without requiring mandatory configuration files.

---

## SECTION C: COMPUTER NETWORKING & DNS

### Q7: How does `core/dns_resolver.py` resolve domain names?
- **Short answer:** It uses Python's standard `socket.getaddrinfo()` function to query system recursive DNS resolvers.
- **Technical explanation:** `socket.getaddrinfo(domain, None)` requests both `AF_INET` (IPv4) and `AF_INET6` (IPv6) socket structures. High-precision timing is recorded using `time.perf_counter()`. Resolved addresses are filtered and deduplicated into `ipv4_addresses` and `ipv6_addresses`.

### Q8: What is the project's Deterministic IP Selection Rule?
- **Short answer:** When DNS returns multiple IP addresses for a domain, the system selects the **first valid IPv4 address** for geolocation; if no IPv4 address exists, it selects the **first valid IPv6 address**.
- **Technical explanation:** Web domains hosted on Content Delivery Networks (CDNs) often return multiple IP addresses. Selecting the primary target deterministically ensures consistent geolocation querying while preserving all returned IPs in `resolved_addresses` for analysis.

### Q9: Why might resolving the same domain twice yield different IP addresses?
- **Short answer:** Because major websites utilize Content Delivery Networks (CDNs), Anycast routing, and DNS load balancers to route traffic to the nearest or least loaded server.
- **Technical explanation:** CDNs configure low Time-To-Live (TTL) values on DNS records and respond with different edge server IPs based on geographical DNS origin and server load.

---

## SECTION D: IP GEOLOCATION

### Q10: Can IP geolocation determine the exact physical location of a person or building?
- **Short answer:** No.
- **Technical explanation:** IP geolocation estimates the geographic association of an IP address based on database records maintained by Regional Internet Registries (RIRs) and ISPs. It maps addresses to countries, regions, cities, and corporate network registry coordinates—it does NOT perform GPS device tracking.

### Q11: How does `core/geo_service.py` communicate with the geolocation provider?
- **Short answer:** It sends secure HTTPS GET requests to `ipapi.co/json/` using Python's standard `urllib.request` module with explicit timeout limits.
- **Technical explanation:** The client sets a 5.0-second socket timeout and custom `User-Agent` headers. It parses JSON responses into an internal `GeoResult` dataclass via `core/normalizer.py` and handles HTTP status codes such as 429 (Rate Limit Exceeded) gracefully.

---

## SECTION E: DATABASE ARCHITECTURE

### Q12: Which database engine is used, and why?
- **Short answer:** SQLite (`data/ip_tracker.db`), using Python's built-in `sqlite3` module.
- **Technical explanation:** SQLite provides a zero-configuration, lightweight, single-file relational database that requires no external server setup. It is ideal for local desktop application history logging.

### Q13: How does the application prevent SQL injection vulnerabilities?
- **Short answer:** All database operations execute using parameterized SQL query placeholders (`?`).
- **Technical explanation:** SQL strings use positional `?` parameters (e.g. `INSERT INTO lookup_history VALUES (?, ?, ...)`), allowing the SQLite driver to automatically sanitize and escape user input values.

### Q14: How does `database/db.py` prevent file locking errors on Windows?
- **Short answer:** Every database connection wrapper uses an explicit `try ... finally: conn.close()` block.
- **Technical explanation:** Python's `with sqlite3.connect(...) as conn:` manages transactions (`commit`/`rollback`) but does NOT automatically close the connection handle. On Windows, unclosed handles cause `PermissionError: [WinError 32]` during file cleanup; explicit `finally` blocks guarantee handle release.

---

## SECTION F: GUI DESIGN & USER EXPERIENCE

### Q15: What design visual theme was chosen for the interface?
- **Short answer:** A "Modern Network Intelligence Console" dark slate theme (`IP PULSE`).
- **Technical explanation:** Built using dark slate background (`#0F172A`), card surface frames (`#1E293B`), sky blue accents (`#0EA5E9`), emerald status badges (`#10B981`), and high-contrast typography (`#F8FAFC`).

### Q16: How does the GUI handle component errors without crashing?
- **Short answer:** Errors are caught inside service layers and rendered as polished error cards or status badges rather than showing unhandled raw Python tracebacks.
- **Technical explanation:** The UI checks `LookupResult.overall_status`. Failed stages (e.g. `DNS_FAILED` or `GEO_FAILED`) display informative inline status banners and preserve partial data (such as DNS timing) cleanly.

---

## SECTION G: MAP VISUALIZATION

### Q17: How is the interactive map implemented in `gui/map_view.py`?
- **Short answer:** It uses `tkintermapview` to render interactive OpenStreetMap tiles directly inside a native Tkinter frame.
- **Technical explanation:** `TkinterMapView` centers on `(latitude, longitude)`, sets an initial zoom level of 10, and places an OpenStreetMap marker displaying target IP and location labels.

### Q18: What happens if geographic coordinates are missing or invalid?
- **Short answer:** The coordinate validator (`validate_coordinates()`) flags out-of-range values, and the MapView displays a friendly fallback message panel.
- **Technical explanation:** `validate_coordinates()` checks bounds (-90 to +90 for latitude, -180 to +180 for longitude). If coordinates are missing or invalid, MapView displays `MAP UNAVAILABLE - Coordinates were not provided` without crashing.

---

## SECTION H: 50-WEBSITE FIELD TESTING

### Q19: Why test exactly 50 websites in Phase 9?
- **Short answer:** To establish a controlled, reproducible empirical sample for evaluating software stability, response latencies, and global infrastructure distributions.
- **Technical explanation:** A 50-website dataset provides a manageable, purposive sample across 11 diverse website categories (Search, Social, E-commerce, Edu, News, etc.) without overloading API rate limits or network resources.

### Q20: Why execute field-test lookups sequentially rather than in parallel?
- **Short answer:** To respect external API rate limits, prevent network congestion, and ensure accurate, reproducible timing measurements.
- **Technical explanation:** Sequential execution with 0.5s inter-request delay pacing avoids HTTP 429 rate limits from public geolocation endpoints and prevents local CPU/socket queuing skew.

---

## SECTION I: DATA ANALYSIS & STATISTICS

### Q21: What descriptive statistics were computed in Phase 10?
- **Short answer:** Sample count, mean, standard deviation, minimum, 25th percentile (P25), median, 75th percentile (P75), maximum, and Interquartile Range (IQR).
- **Technical explanation:** Computed across `dns_response_time_ms`, `api_response_time_ms`, and `total_response_time_ms` using `pandas` and `numpy` in `analysis/analyzer.py`.

### Q22: Why is the median preferred over the mean for network response times?
- **Short answer:** Because network latency measurements exhibit strong right-skewness due to occasional transient latency spikes.
- **Technical explanation:** Mean is heavily sensitive to high extreme values (outliers). In our 50-site empirical data, total latency had a median of **108.64 ms** versus a mean of **358.00 ms** (max 2915.82 ms). Median provides a far more accurate representation of typical performance.

---

## SECTION J: RESEARCH LIMITATIONS & DIFFICULT QUESTIONS

### Q23: Why do two completely different websites show the exact same IP geolocation city?
- **Short answer:** They are hosted on shared cloud infrastructure or the same Content Delivery Network (CDN).
- **Technical explanation:** Modern cloud providers (e.g. Cloudflare, AWS, Fastly) host millions of customer domains on shared Anycast IP ranges. Geolocation databases resolve the IP to the CDN's registered network edge hub rather than the customer's business address.

### Q24: Why separate the application lookup history (`ip_tracker.db`) from the research dataset (`field_test_results.csv`)?
- **Short answer:** Because operational user history and controlled scientific field research datasets serve fundamentally different purposes and must remain uncorrupted.
- **Technical explanation:** User history logs ad-hoc daily queries. Research datasets require immutable, standardized schemas with test IDs (1–50) for statistical auditability.

### Q25: How many automated unit tests exist in the project, and did they pass?
- **Short answer:** Exactly 54 automated unit and integration tests across 9 test modules, with a **100% pass rate**.
- **Technical explanation:** Executed via `python -m unittest discover -s tests`. Covers input validation, socket DNS resolution, API parsing, normalizer dataclasses, lookup orchestration, SQLite database CRUD, coordinate bounds validation, field test loader, and data analysis statistics.
