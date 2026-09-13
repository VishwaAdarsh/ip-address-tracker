# IP PULSE — Comprehensive Viva Examination Question Bank & Technical Answers

This document provides a comprehensive, technically accurate viva examination guide for **IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform**, structured across 7 core academic categories with concise, spoken-friendly answers tailored for B.Sc. IT degree defense.

---

## 1. BASIC NETWORKING CONCEPTS

### Q1: What is an IP address, and how does it differ from a MAC address?
* **Spoken Answer:** An IP address is a logical network address used to route packets across interconnected networks (Layer 3), whereas a MAC address is a physical hardware identifier assigned to a network interface card (Layer 2).
* **Technical Detail:** IPv4 uses 32 bits and IPv6 uses 128 bits. An IP address changes when a device moves to another network, while a MAC address is permanently burned into the hardware.

### Q2: What is the difference between IPv4 and IPv6?
* **Spoken Answer:** IPv4 uses 32-bit addresses providing approximately 4.3 billion unique addresses, whereas IPv6 uses 128 bits providing virtually inexhaustible addressing space ($3.4 \times 10^{38}$ addresses).
* **Technical Detail:** IPv4 is written in decimal dotted-quad notation (e.g., `192.168.1.1`), while IPv6 uses hexadecimal groups separated by colons (e.g., `2001:4860:4860::8888`). IPv6 eliminates the necessity of NAT and integrates native IPSec encryption.

### Q3: What is the Domain Name System (DNS)?
* **Spoken Answer:** DNS is a distributed, hierarchical naming system that translates human-friendly domain names (like `google.com`) into computer-routable IP addresses (like `142.250.182.238`).
* **Technical Detail:** It operates on UDP/TCP port 53. The client's resolver queries root nameservers, Top-Level Domain (TLD) nameservers, and authoritative nameservers to resolve A (IPv4) or AAAA (IPv6) records.

### Q4: What is IP Geolocation?
* **Spoken Answer:** IP geolocation is the mapping of a public IP address to geographic metadata, such as country, region, city, latitude, longitude, and timezone.
* **Technical Detail:** Geolocation maps to administrative network registry allocations (RIR netblocks like ARIN or APNIC) and ISP infrastructure, not physical GPS device tracking.

### Q5: What is an Autonomous System (ASN)?
* **Spoken Answer:** An Autonomous System (AS) is a collection of connected IP routing prefixes controlled by one or more network operators that presents a single, clearly defined routing policy to the Internet.
* **Technical Detail:** ASNs are globally unique numbers (e.g., AS15169 for Google, AS13335 for Cloudflare) used by the Border Gateway Protocol (BGP) to make inter-domain routing decisions.

### Q6: What is an Internet Service Provider (ISP)?
* **Spoken Answer:** An ISP is an organization that provides connectivity and network transit allowing individuals and businesses to access the Internet.
* **Technical Detail:** ISPs manage telecommunication infrastructure, lease IP address blocks from RIRs, and peer with other networks at Internet Exchange Points (IXPs).

---

## 2. PROJECT OVERVIEW & APPLICATION ARCHITECTURE

### Q7: Why did you build IP PULSE? What problem does it solve?
* **Spoken Answer:** We built IP PULSE to eliminate the fragmentation and opacity of traditional network diagnostic tools. It unifies DNS resolution, geolocation, website security inspection, infrastructure classification, and explainable risk scoring into a single, cohesive web platform.
* **Technical Detail:** Standard CLI tools (`nslookup`, `curl`, `whois`) provide isolated data without correlation or persistent history. IP PULSE correlates transport-layer and network-layer signals into mathematically bounded, transparent Trust and Risk scores.

### Q8: Why did you choose Python for the backend?
* **Spoken Answer:** Python offers robust standard library networking modules (`socket`, `ssl`, `http.server`, `urllib`), native SQLite database integration, and high-performance data analysis packages (`pandas`, `reportlab`) ideal for research automation.
* **Technical Detail:** Python allows a lightweight architecture: standard library `ThreadingHTTPServer` delivers concurrent multithreaded REST APIs without the heavy dependency footprint of external web frameworks.

### Q9: Why did you build a web frontend instead of a desktop GUI?
* **Spoken Answer:** A modern web interface built on the Stitch Obsidian Dark design system provides accessible, cross-platform usage, responsive mobile/tablet layouts, and dynamic interactive Leaflet mapping without requiring client-side desktop GUI installations like PySide6.
* **Technical Detail:** The frontend uses pure vanilla JavaScript and Tailwind CSS utility classes, communicating with the Python backend via asynchronous REST JSON endpoints.

### Q10: How does the system resolve a domain name?
* **Spoken Answer:** When a user enters a domain, the validator strips protocols and paths, and `core/dns_resolver.py` invokes `socket.getaddrinfo()` to retrieve both IPv4 (A) and IPv6 (AAAA) records.
* **Technical Detail:** It implements a deterministic IP selection rule: prioritizing the first valid IPv4 address for downstream geolocation while preserving all discovered IPv6 addresses in the telemetry record.

### Q11: How is IP geolocation obtained in the platform?
* **Spoken Answer:** The backend queries authoritative public geolocation REST APIs (`ipapi.co`) over HTTPS with strict 5.0-second timeouts, parsing JSON responses into normalized data models.
* **Technical Detail:** If network errors or provider rate limits occur, the system fails gracefully to neutral `UNKNOWN` states without application crashes.

### Q12: What is infrastructure classification?
* **Spoken Answer:** It is the categorization of the host network into distinct operational types: `datacenter` (hosting facilities and cloud hubs), `cdn` (edge distribution networks), `residential` (consumer broadband), or `business` (corporate networks).
* **Technical Detail:** Classification is determined by correlating Autonomous System Numbers (ASNs) and organization names against known cloud provider IP netblock registries.

### Q13: What is VPN detection?
* **Spoken Answer:** VPN detection identifies whether an IP address belongs to a commercial Virtual Private Network service that encapsulates and tunnels client traffic.
* **Technical Detail:** Evaluated by cross-referencing IP netblocks against known commercial VPN exit nodes (e.g., NordVPN, ExpressVPN).

### Q14: What is Proxy detection?
* **Spoken Answer:** Proxy detection identifies intermediate forwarding servers (HTTP, HTTPS, or SOCKS proxies) that relay requests on behalf of clients.
* **Technical Detail:** Detected via open proxy registries and signature checks on forwarding headers (`X-Forwarded-For`, `Via`).

### Q15: What is Tor (The Onion Router)?
* **Spoken Answer:** Tor is an open-source decentralized overlay network designed for anonymous communication, routing encrypted traffic through a multi-hop circuit of volunteer-operated relays.
* **Technical Detail:** IP PULSE checks public Tor exit node directories. An IP confirmed as a Tor exit node indicates active anonymized routing.

---

## 3. WEBSITE SECURITY INTELLIGENCE

### Q16: What is HTTPS, and how does it work?
* **Spoken Answer:** HTTPS (Hypertext Transfer Protocol Secure) is the encrypted extension of HTTP. It encrypts communication between the browser and server using Transport Layer Security (TLS).
* **Technical Detail:** HTTPS operates on port 443. It establishes encryption via asymmetric cryptography (TLS handshake) for authentication and key exchange, followed by symmetric encryption (e.g., AES-GCM) for rapid data transfer.

### Q17: What is TLS, and what does a TLS certificate provide?
* **Spoken Answer:** TLS (Transport Layer Security) is the cryptographic protocol that secures internet communications. A TLS certificate provides cryptographic authentication of server identity and enables encrypted sessions.
* **Technical Detail:** Issued by trusted Certificate Authorities (CAs) conforming to X.509 standards. It validates domain ownership, provides the public encryption key, and specifies validity dates.

### Q18: What security checks does IP PULSE perform on a website?
* **Spoken Answer:** It verifies HTTPS enforcement, TLS certificate validity, certificate issuer, remaining days until expiration, negotiated cipher suite, and defensive HTTP security headers.
* **Technical Detail:** `core/security_scanner.py` passive-checks response headers for HSTS (`Strict-Transport-Security`), CSP (`Content-Security-Policy`), and Clickjacking prevention (`X-Frame-Options`).

### Q19: Does HTTPS guarantee that a website is genuine or safe?
* **Spoken Answer:** No! HTTPS only guarantees that the connection between client and server is encrypted and has not been tampered with in transit. It does NOT guarantee that the website owner is legitimate or that the site is free of phishing or malware.
* **Technical Detail:** Attackers frequently obtain free, automated TLS certificates (e.g., via Let's Encrypt) for fraudulent or deceptive phishing domains.

### Q20: Does an elevated IP Risk Score prove that an IP is actively malicious?
* **Spoken Answer:** No. The IP Risk Score is a heuristic indicator based on observable technical telemetry. An elevated score indicates elevated risk characteristics (such as hosting anonymity relays or missing encryption), not legal or forensic proof of malicious behavior.
* **Technical Detail:** IP PULSE attaches a mandatory analytical disclaimer to all risk assessments to prevent automated enforcement without human verification.

---

## 4. SCORING & RISK METHODOLOGY

### Q21: How is the Website Trust Score calculated?
* **Spoken Answer:** Trust Score is a deterministic value from 0 to 100 calculated by rewarding positive security hygiene factors, such as valid TLS certificates, HTTPS enforcement, modern TLS versions, and security headers.
* **Technical Detail:** Base score starts at neutral 50. Positive signals add points (e.g., $+20$ for valid TLS $>30$ days, $+15$ for HTTPS redirect, $+10$ for HSTS/CSP), capped strictly at 100.

### Q22: How is the IP Risk Score calculated?
* **Spoken Answer:** Risk Score is mathematically complementary to Trust Score ($\text{Trust} + \text{Risk} = 100$), bounded between 0 and 100, driven by negative risk indicators.
* **Technical Detail:** Risk factors deduct trust / add risk: untrusted or expired TLS ($+30$ Risk), plaintext HTTP ($+25$ Risk), Tor exit nodes ($+35$ Risk), open proxies ($+25$ Risk), and commercial VPNs ($+15$ Risk).

### Q23: What happens when telemetry information is unavailable or times out?
* **Spoken Answer:** Missing information is assigned an explicit neutral status of `UNKNOWN` or `Not Evaluated`. It is never penalized or assumed to be malicious.
* **Technical Detail:** This enforces the **Data Neutrality Principle**. A DNS timeout or unreturned geolocation attribute maintains a baseline neutral score and simply reduces observational confidence.

### Q24: Why is Evidence Confidence separate from the Risk Score?
* **Spoken Answer:** Because a score derived from 5 observed signals is much more reliable than a score derived from only 1 signal. Keeping confidence separate informs the analyst about observational completeness.
* **Technical Detail:** Confidence represents the ratio of observed signals to total evaluated dimensions. A host could have an 85 Trust Score with High Confidence (all data present) or Low Confidence (minimal data available).

---

## 5. 50-SITE FIELD STUDY & RESEARCH ANALYTICS

### Q25: What is the 50-Site Field Study protocol?
* **Spoken Answer:** It is a standardized empirical research protocol designed to benchmark public internet telemetry across 50 representative global websites spanning 11 diverse industry sectors.
* **Technical Detail:** Enforces strict validation rules: syntactically valid domains, verified IPv4/IPv6 addresses, valid latitude/longitude bounds, ISO 8601 UTC timestamps, and unique `(test_id, domain)` tuples.

### Q26: How were observations collected? Were they automated or manual?
* **Spoken Answer:** The platform follows a manual-first collection methodology where observations are triggered deliberately, with an optional background completion tool to fill remaining observations up to 50.
* **Technical Detail:** This prevents aggressive scraping, respects third-party provider rate limits, and ensures verifiable data provenance for research reproducibility.

### Q27: What fields are recorded in each field study observation?
* **Spoken Answer:** Exactly 26 structured attributes across 6 categories: Identity (domain, IP, version), Geolocation (country, region, city, coordinates), Network (ASN, ISP, infrastructure), Security (HTTPS, TLS, VPN, Proxy, Tor), Scoring (Trust, Risk, Confidence), and Metadata (timestamp, status).

### Q28: What do the actual empirical results show so far?
* **Spoken Answer:** Currently, 7 real observations are recorded in the database: 100% cloud/hosting infrastructure concentration, 85.7% IPv4 to 14.3% IPv6 allocation, a mean Trust Score of 85.0/100, and mean Risk Score of 15.0/100 across the US, Canada, Australia, and India.
* **Technical Detail:** Top Autonomous Systems in the dataset are AS13335 (Cloudflare) at 42.9% and AS15169 (Google) at 14.3%, highlighting modern infrastructure centralization.

### Q29: How does the Research Dashboard filter telemetry?
* **Spoken Answer:** It provides real-time multi-dimensional filtering across 7 dimensions: Country, Infrastructure Type, Trust Classification, Risk Classification, HTTPS Status, IP Version, and Observation Range.
* **Technical Detail:** All statistical aggregations (mean, median, standard deviation, min, max, histograms) and the interactive Leaflet map recompute dynamically over the filtered subset without modifying source records.

---

## 6. EXPLAINABLE AI INTELLIGENCE LAYER

### Q30: What is the purpose of AI in IP PULSE?
* **Spoken Answer:** AI acts as an explainability and reporting layer. It translates complex technical signals into plain-English analytical summaries for analysts and executive stakeholders.
* **Technical Detail:** The AI synthesizes positive factors, negative factors, and unknown factors into narrative explanations of why a particular score was assigned.

### Q31: Does AI calculate or alter the Trust Score or Risk Score?
* **Spoken Answer:** Absolutely NOT! Trust and Risk scores are strictly computed by our deterministic mathematical scoring engine in `core/risk_engine.py`. AI has zero influence over numerical scores.
* **Technical Detail:** This architectural separation guarantees that scores remain objective, reproducible, and verifiable, preventing AI hallucination from corrupting quantitative data.

### Q32: What happens if the AI service or internet connection is offline?
* **Spoken Answer:** The system features a deterministic rule-based fallback engine that synthesizes structured natural-language explanations locally without external API calls.
* **Technical Detail:** If Google Gemini API is unavailable or unconfigured, `core/ai_explainer.py` immediately activates its internal rule-based template generator, ensuring zero feature disruption.

### Q33: How do you prevent the AI from making false or absolute security claims?
* **Spoken Answer:** All generated explanation text passes through a regex-based sanitization filter (`sanitize_security_claims`) that intercepts and replaces absolute claims like "100% safe" or "definitely malicious" with objective, probabilistic language.

---

## 7. SYSTEM ARCHITECTURE, WORKFLOW & PERSISTENCE

### Q34: What is the Intelligence Provenance Chain?
* **Spoken Answer:** It is a 6-node audit trail that records each sequential stage of intelligence gathering: Target Resolution $\to$ DNS Mapping $\to$ Geolocation $\to$ Autonomous System $\to$ Security & TLS $\to$ Risk & Trust Synthesis.
* **Technical Detail:** It provides full transparency into how the final assessment was reached, validating the chain of custody for every telemetry signal.

### Q35: What is the IP Personality engine?
* **Spoken Answer:** It is a classification engine that assigns one of 8 deterministic behavioral archetypes (such as `CLOUD_SENTINEL`, `RESIDENTIAL_PEER`, `PRIVACY_SHIELD`, or `EDGE_ROUTER`) based on network infrastructure and anonymity indicators.
* **Technical Detail:** Provides analysts with an immediate mental model of how the host operates in the global network topology.

### Q36: How does the Investigation Workspace work?
* **Spoken Answer:** It allows side-by-side comparison of 2 to 5 targets selected from History or Field Study, automatically highlighting extreme scores and calculating an infrastructure commonality matrix.
* **Technical Detail:** Operates strictly read-only. It identifies shared ASNs, common countries, hosting providers, and infrastructure types across the candidate cohort.

### Q37: How is data persisted in the SQLite database?
* **Spoken Answer:** Lookups and field observations are stored in `data/ip_tracker.db` using parameterized SQL queries with WAL (Write-Ahead Logging) mode and foreign keys enabled.
* **Technical Detail:** The database maintains two isolated tables: `lookup_history` (general user queries) and `field_study_observations` (formal 50-site research dataset). History operations never corrupt or overwrite field study data.

### Q38: What security hardening measures are built into the API server?
* **Spoken Answer:** The API server enforces standard security response headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy`), limits request payloads to 10MB, and prevents path traversal attacks when serving static files.
* **Technical Detail:** Zero external dependencies are exposed on the server boundary; standard library `ThreadingHTTPServer` executes isolated threads for each client connection.

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

### Q19: What is the Manual-First Field Test Methodology?
- **Short answer:** Normal user lookups executed on the Dashboard are automatically collected in the SQLite History database. The Field Project reads these records first, and only allows optional automatic completion if fewer than 50 valid observations exist.
- **Technical explanation:** `services/field_test_service.py` evaluates `available_count` from `ip_tracker.db` by filtering and deduplicating unique domain lookups. If `N < 50`, `[ COMPLETE REMAINING (50 - N) AUTOMATICALLY ]` allows completing only the required remaining sites using standard `perform_lookup(domain, save_to_db=True)`.

### Q20: Why execute automatic completion sequentially rather than in parallel?
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

### Q24: How does the Field Project dataset relate to SQLite Lookup History?
- **Short answer:** The field project dataset (`data/field_test/field_test_results.csv`) is derived directly from unique domain observations in SQLite History (`data/ip_tracker.db`).
- **Technical explanation:** Normal lookups are stored in SQLite History. The field project service filters valid domain lookups, deduplicates by domain name, selects up to 50 records, and exports them to CSV without modifying or deleting the raw database.

### Q25: How many automated unit tests exist in the project, and did they pass?
- **Short answer:** Exactly 60 automated unit and integration tests across 9 test modules, with a **100% pass rate**.
- **Technical explanation:** Executed via `python -m unittest discover -s tests`. Covers input validation, socket DNS resolution, API parsing, normalizer dataclasses, lookup orchestration, SQLite database CRUD, manual-first field testing, 10 workflow scenarios, coordinate bounds validation, and data analysis statistics.
