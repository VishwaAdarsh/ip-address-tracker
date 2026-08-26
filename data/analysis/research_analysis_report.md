# Field-Test Data Analysis & Findings Report

## 1. Executive Summary
- **Total Websites Analyzed:** 50
- **Overall Success Rate:** 98.0% (49/50 lookups)
- **Unique Geolocation Countries:** 8 (Top country: United States with 20 observations)
- **IP Protocol Ratio:** IPv4: 49 | IPv6: 0
- **Median Execution Time:** DNS: 21.16 ms | Geolocation API: 277.29 ms | Total Pipeline: 302.2 ms

---

## 2. Descriptive Performance Analysis

| Metric | Sample Count | Mean (ms) | Std Dev (ms) | Min (ms) | P25 (ms) | Median (ms) | P75 (ms) | Max (ms) | IQR (ms) |
|---|---|---|---|---|---|---|---|---|---|
| **DNS Resolution** | 50 | 132.43 | 294.0 | 0.52 | 18.34 | 21.16 | 25.52 | 1143.83 | 7.18 |
| **Geolocation API** | 50 | 299.25 | 155.33 | 0.0 | 269.99 | 277.29 | 289.32 | 1273.38 | 19.32 |
| **Total Pipeline** | 50 | 431.68 | 309.4 | 249.23 | 292.54 | 302.2 | 320.24 | 1413.75 | 27.7 |

*Note: Median is reported as the primary location metric due to right-skewed timing distributions caused by occasional network latencies.*

---

## 3. Geographic & Network Findings
- **Geographic Representation:** Across 50 public websites, 8 distinct countries were identified. The United States was the most frequently geolocated country (20 sites).
- **Network Providers & Infrastructure:** Major cloud and CDN infrastructure providers (e.g. Cloudflare, Fastly, Amazon CloudFront, Google LLC) represent a significant proportion of resolved target IPs.

---

## 4. Missing-Data & Quality Observations
Missing attributes (e.g., unreturned city or region names from IP registry databases) were recorded explicitly as `"N/A"` without data fabrication:
- **City:** 49 present (1 missing / 2.0%)
- **Region:** 49 present (1 missing / 2.0%)
- **Country:** 49 present (1 missing / 2.0%)
- **Latitude:** 49 present (1 missing / 2.0%)
- **Longitude:** 49 present (1 missing / 2.0%)
- **Timezone:** 49 present (1 missing / 2.0%)
- **Organization:** 46 present (4 missing / 8.0%)
- **Isp:** 49 present (1 missing / 2.0%)
- **Asn:** 49 present (1 missing / 2.0%)
- **Selected_ip:** 49 present (1 missing / 2.0%)

---

## 5. Sample Limitations
1. **Purposive Sample:** The sample consists of 50 purposively selected public domains across 11 categories; findings cannot be generalized to the entire global Internet.
2. **Approximate Geolocation:** IP geolocation reflects network registry associations rather than exact physical server locations.
