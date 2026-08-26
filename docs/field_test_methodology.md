# Field-Test Methodology & Research Design

## 1. Study Overview
This field study evaluates DNS resolution behaviors, public IP address locations, network infrastructure providers, and component execution performance across a controlled dataset of **50 public websites**.

**Project:** College Semester Field Project — IP Address Tracker & Geolocation Tool  
**Sample Size:** Exactly 50 public domain names  
**Data Storage:** `data/field_test/field_test_results.csv`  

---

## 2. Sampling Design
- **Sampling Method:** Purposive / Convenience Sampling (non-random selection of established public websites across diverse categories).
- **Categories Included:** Search, Technology, Social Media, E-commerce, Reference, Education, News, Government, Finance, Entertainment, Cloud Services.
- **Sample Stability:** The 50 website domains are fixed prior to the formal experiment (`data/field_test/websites.csv`). Failed DNS or geolocation lookups are preserved as valid empirical observations rather than dynamically replaced.
- **Generalizability Notice:** The sample is designed to demonstrate multi-category infrastructure patterns; it is not a statistically representative random sample of the global Internet.

---

## 3. Experimental Procedure & Pipeline
Each website domain is processed sequentially according to the following automated workflow:

```text
Domain Input (websites.csv)
        ↓
Input Validation (core/validator.py)
        ↓
DNS Resolution (core/dns_resolver.py)
        ↓
Deterministic IP Selection Rule
        ↓
IP Geolocation Service (core/geo_service.py)
        ↓
Response Normalization (core/normalizer.py)
        ↓
Research Dataset Output (data/field_test/field_test_results.csv)
```

### Deterministic IP Selection Rule
Modern web domains frequently resolve to multiple IPv4 and IPv6 addresses (CDNs, Anycast, load balancing). To ensure reproducible geolocation querying:
1. The **first valid IPv4 address** returned by DNS is selected for geolocation.
2. If no IPv4 address exists, the **first valid IPv6 address** is selected.
3. **Complete DNS Preservation:** All returned IPv4 and IPv6 addresses are preserved in the research dataset (delimited by semicolons `;`).

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
4. **Rate Limit Compliance:** Sequential execution enforces request pacing (0.5s inter-request delay) to respect external API rate limits.
