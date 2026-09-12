# Field-Test Data Analysis & Findings Report

## 1. Executive Summary
- **Total Websites Analyzed:** 50
- **Overall Success Rate:** 98.0% (49/50 lookups)
- **Unique Geolocation Countries:** 10 (Top country: United States with 20 observations)
- **IP Protocol Ratio:** IPv4: 49 | IPv6: 0
- **Median Execution Time:** DNS: 24.44 ms | Geolocation API: 285.52 ms | Total Pipeline: 316.25 ms

---

## 2. Descriptive Performance Analysis

| Metric | Sample Count | Mean (ms) | Std Dev (ms) | Min (ms) | P25 (ms) | Median (ms) | P75 (ms) | Max (ms) | IQR (ms) |
|---|---|---|---|---|---|---|---|---|---|
| **DNS Resolution** | 50 | 82.72 | 185.71 | 14.08 | 22.16 | 24.44 | 35.33 | 914.11 | 13.17 |
| **Geolocation API** | 50 | 310.21 | 117.69 | 0.0 | 268.86 | 285.52 | 306.86 | 976.59 | 38.0 |
| **Total Pipeline** | 50 | 392.93 | 211.84 | 19.62 | 295.37 | 316.25 | 394.66 | 1180.58 | 99.3 |

*Note: Median is reported as the primary location metric due to right-skewed timing distributions caused by occasional network latencies.*

---

## 3. Geographic & Network Findings
- **Geographic Representation:** Across 50 public websites, 10 distinct countries were identified. The United States was the most frequently geolocated country (20 sites).
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
- **Organization:** 45 present (5 missing / 10.0%)
- **Isp:** 49 present (1 missing / 2.0%)
- **Asn:** 49 present (1 missing / 2.0%)
- **Selected_ip:** 49 present (1 missing / 2.0%)

---

## 5. Sample Limitations
1. **Purposive Sample:** The sample consists of 50 purposively selected public domains across 11 categories; findings cannot be generalized to the entire global Internet.
2. **Approximate Geolocation:** IP geolocation reflects network registry associations rather than exact physical server locations.
