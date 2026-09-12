# Field-Test Methodology & Manual-First Research Design

## 1. Study Overview
This field study evaluates DNS resolution behaviors, public IP address locations, network infrastructure providers, and component execution performance across a controlled dataset of **50 public websites**.

**Project:** College Semester Field Project — IP Address Tracker & Geolocation Tool  
**Methodology:** **Manual-First Field Testing**  
**Sample Size:** Exactly 50 public website observations  
**Primary Source of Truth:** SQLite Lookup History (`data/ip_tracker.db`)  
**Derived Research Dataset:** `data/field_test/field_test_results.csv`  

---

## 2. Manual-First Methodology

The field project follows a **manual-first data collection methodology**:

```text
Normal Application Usage (User enters domains/IPs on Dashboard)
        ↓
Lookups processed by core service engine (DNS + Geolocation)
        ↓
Successful lookup observations stored in SQLite History (data/ip_tracker.db)
        ↓
Field Project Module reads existing History records
        ↓
Valid observations are deduplicated deterministically by domain
        ↓
Count evaluated: Available = N / 50 | Remaining = max(50 - N, 0)
        ↓
Case 1 (N < 50): User may optionally click [ COMPLETE REMAINING N AUTOMATICALLY ]
Case 2 (N == 50): Status = TARGET REACHED ✓ (No auto completion needed)
Case 3 (N > 50): Status = TARGET REACHED ✓ (50 selected deterministically)
```

### Key Methodology Principles
1. **History as Source of Truth:** Normal user lookups executed during regular application usage form the primary empirical observation pool.
2. **Zero Automatic Execution on Screen Load:** Opening the Field Project tab never launches automatic testing.
3. **Controlled Automatic Completion:** If fewer than 50 valid observations exist in History, the user may optionally click `[ COMPLETE REMAINING N AUTOMATICALLY ]`. This executes *only* the exact remaining number of website lookups required to reach 50, using standard `perform_lookup(domain, save_to_db=True)` so lookups are saved through the normal History mechanism.
4. **Overrun Prevention:** Automatic completion never runs all 50 websites if only N are required.
5. **History Integrity:** Raw SQLite History is never deleted, truncated, or modified when generating the field project dataset.

---

## 3. Sampling & Deduplication Rules

- **Sampling Method:** Purposive / Convenience Sampling across 11 diverse website categories (Search, Technology, Social Media, E-commerce, Reference, Education, News, Government, Finance, Entertainment, Cloud Services).
- **Deduplication Rule:** Multiple lookups of the same domain in History are deduplicated deterministically by domain name (preserving the earliest/latest unique observation per domain).
- **Sample Stability:** The 50 website domains are derived from user lookups and complemented by `data/field_test/websites.csv` when automatic completion is requested. Failed lookups are preserved as valid empirical observations rather than omitted.

---

## 4. Measured Variables & Metrics

| Category | Field Name | Description / Format |
|---|---|---|
| Metadata | `test_id` | Unique ID (1 to 50) |
| Metadata | `domain` | Tested website domain |
| Metadata | `category` | Website domain category |
| Metadata | `timestamp` | ISO UTC execution timestamp |
| Technical | `input_type` | DOMAIN / IPV4 / IPV6 |
| Technical | `dns_status` | SUCCESS / DNS_FAILED |
| Technical | `ipv4_addresses` | All resolved IPv4 addresses (semicolon-separated) |
| Technical | `ipv6_addresses` | All resolved IPv6 addresses (semicolon-separated) |
| Technical | `selected_ip` | IP address selected for geolocation |
| Technical | `ip_version` | IPv4 / IPv6 / N/A |
| Location | `country` / `country_code` | Geolocation country name & ISO 2-letter code |
| Location | `region` / `city` | Region/State and City name ("N/A" if unreturned) |
| Location | `latitude` / `longitude` | Geographic coordinates (float or empty if N/A) |
| Location | `timezone` | Timezone identifier (e.g. Asia/Kolkata) |
| Network | `organization` / `isp` | Network owner & Internet Service Provider |
| Network | `asn` | Autonomous System Number (e.g. AS15169) |
| Performance | `dns_response_time_ms` | High-precision DNS resolution duration (ms) |
| Performance | `api_response_time_ms` | High-precision Geolocation API duration (ms) |
| Performance | `total_response_time_ms` | End-to-end pipeline execution time (ms) |
| Status | `geolocation_status` | SUCCESS / API_TIMEOUT / API_RATE_LIMIT / etc. |
| Status | `overall_status` | SUCCESS / DNS_FAILED / GEO_FAILED / INVALID_INPUT |
| Status | `error_message` | Technical exception or error summary if failed |

---

## 5. Technical Limitations & Ethical Considerations

1. **Approximate Geolocation:** IP geolocation maps IP addresses to network registry allocations; it does not indicate exact physical server addresses or user physical locations.
2. **Time-Dependent DNS:** DNS resolution results vary over time and across geographic lookup origins due to Content Delivery Networks (CDNs), Anycast routing, and dynamic load balancing.
3. **Data Integrity & Non-Fabrication:** Missing provider attributes default to `"N/A"` or null. Values are never fabricated.
4. **Controlled Pacing:** Sequential execution enforces request pacing (0.5s inter-request delay) to respect external API rate limits.
