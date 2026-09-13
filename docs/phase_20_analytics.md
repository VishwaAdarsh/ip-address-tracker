# Phase 20: Advanced Field Study Analytics & Comparison

## 1. Executive Summary

Phase 20 elevates the IP PULSE platform from an endpoint scanner into an empirical research analytics system. It computes transparent, deterministic, and statistically rigorous insights across the standardized **50-website field study dataset** stored in `data/ip_tracker.db`.

### Core Architectural Principles
- **Strict Empirical Derivation:** All 7 analytical dimensions are calculated purely from actual observations stored in the SQLite `field_study_observations` table. Zero simulated threat feeds, synthetic scores, or artificial telemetry are used.
- **Zero Fabrication & Bias Avoidance:** Missing, unresolvable, or unmeasured attributes are classified as `Unknown` and explicitly segregated from positive and negative findings.
- **Graceful State Resilience:** Gracefully handles empty ($N=0$), partial ($1 \le N < 50$), and target ($N=50$) sample sizes without divide-by-zero errors or misleading $0.0\%$ indicators.
- **Obsidian Dark Stitch Aesthetic:** Integrates cleanly into `#view-analytics` using Tailwind CSS, glassmorphism cards, dual histograms, and comparative ranking tables.

---

## 2. Statistical Methodology & Calculations

### 2.1 Univariate Central Tendency & Dispersion
For any continuous numeric distribution $X = \{x_1, x_2, \dots, x_n\}$ (such as Website Trust Score or IP Risk Score):

$$\mu = \frac{1}{n} \sum_{i=1}^{n} x_i$$

$$\sigma = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (x_i - \mu)^2}$$

- When $n = 0$: $\mu = \text{None}$, $\sigma = \text{None}$, $\min = \text{None}$, $\max = \text{None}$.
- Missing or null scores are omitted from score calculation rather than defaulting to 0, preventing downward score skewing.

### 2.2 Standardized Histogram Binning
Continuous 0–100 scores are partitioned into 5 standardized intervals:
1. **Critical Risk / Very Low Trust:** $0 \le x \le 20$
2. **High Risk / Low Trust:** $21 \le x \le 40$
3. **Medium Risk / Moderate Trust:** $41 \le x \le 60$
4. **Low Risk / Good Trust:** $61 \le x \le 80$
5. **Minimal Risk / High Trust:** $81 \le x \le 100$

Relative frequency is computed as:
$$P_k = \frac{\text{Count}_k}{n_{\text{valid}}} \times 100\%$$

---

## 3. Seven Analytical Dimensions

```
+-----------------------------------------------------------------------------------+
|                            IP PULSE ANALYTICS ENGINE                              |
|                      (services/analytics_service.py)                              |
+-----------------------------------------------------------------------------------+
        |
        +---> [1] Field Study Overview & 50-Site Target Quota
        |         - N sample size, remaining to 50, completion %, mean trust, mean risk
        |
        +---> [2] Trust & Risk Score Analysis (Dual Histograms)
        |         - 5-bracket histogram, min/mean/max/std dev, classification pills
        |
        +---> [3] Security & Transport Encryption
        |         - HTTPS adoption rate (Enabled, Disabled, Unknown)
        |         - TLS certificate validation (Valid, Invalid/Expired, Unknown)
        |
        +---> [4] Infrastructure & Network Analysis
        |         - Dual-stack IPv4 vs IPv6 ratios & query latencies (DNS & API)
        |         - Cloud/Datacenter vs Traditional network hosting density
        |         - Anonymizer detection counts (VPN, Proxy, Tor)
        |
        +---> [5] Country & BGP ASN Distribution
        |         - Geographic routing frequency table
        |         - Dominant Autonomous Systems frequency table
        |
        +---> [6] Deterministic Research Insights Layer
        |         - Non-speculative, verifiable empirical findings with metrics
        |
        +---> [7] Comparative Cohort Rankings
                  - Top 5 highest & lowest Website Trust scores
                  - Top 5 highest & lowest IP Risk scores
                  - Comparative group averages (HTTPS vs Non-HTTPS, Cloud vs Traditional)
```

### Section 1: Field Study Overview
- **Sample Count:** Total observations $N$ vs Target (50).
- **Quota Progress:** Dynamic bar indicating completion towards the 50-site goal ($0\% \to 100\%$).
- **HTTPS Adoption:** Percentage of cohort actively serving encrypted transport.
- **Central Posture:** Cohort mean Website Trust and IP Risk ratings.

### Section 2: Trust & Risk Score Analysis
- **Website Trust Score Histogram:** 5-bracket visual distribution representing cryptographic and operational integrity.
- **IP Risk Score Histogram:** 5-bracket distribution depicting network exposure and hosting volatility.
- **Classification Summaries:** Categorical breakdown pills (e.g., Very High Trust, Moderate Trust, High Risk).

### Section 3: Security & Transport Encryption
- **HTTPS Status Breakdown:** Quantified counts and percentages for `Enabled`, `Disabled`, and `Unknown`.
- **TLS Certificate Chain Verification:** Quantified counts and percentages for `Valid`, `Invalid / Expired`, and `Unknown`.
- **Proportional Stacked Visualizers:** Dynamic dual-color progress bars representing adoption coverage.

### Section 4: Infrastructure & Network Analysis
- **IP Protocols:** Ratio of IPv4 vs IPv6 endpoints.
- **Latency Telemetry:** Measured round-trip DNS resolution and API query times in milliseconds.
- **Cloud/Datacenter Density:** Hosting categorization comparing Hyperscalers/CDNs (Cloudflare, AWS, Google, Akamai) against traditional Enterprise/Residential ISPs.
- **Anonymizer Probing:** Quantified detection counters for VPN exit nodes, HTTP/SOCKS proxies, and Tor onion routers.

### Section 5: Country & Autonomous System (BGP) Distribution
- **Top Geographic Nodes:** Frequency table of hosting nations across the cohort.
- **Top Autonomous Systems:** BGP routing authority attribution (ASN number + Organization name).

### Section 6: Research Insights Layer
Factual, deterministic deductions generated without hallucination or extrapolation:
1. **Sample Quota State:** Exact collected count vs 50 target.
2. **Transport Layer Adoption:** Empirically verified HTTPS coverage rate.
3. **Infrastructure Concentration:** Cloud/Datacenter infrastructure percentage.
4. **Scoring Central Tendencies:** Actual empirical mean trust and risk scores.
5. **Anonymization Telemetry:** Observed presence or total absence of anonymization egress nodes.
6. **BGP Dominance:** Primary Autonomous System routing the observed cohort.

### Section 7: Comparative Cohort Rankings
- **Highest Website Trust Table:** Domain, country, and trust rating.
- **Highest IP Risk Table:** Domain, infrastructure type, and risk rating.
- **Group Comparison Averages:** Comparative mean trust of HTTPS-enabled vs non-HTTPS endpoints, and comparative risk of Cloud vs Non-Cloud hosting.

---

## 4. API Specification

### Endpoint: `GET /api/analytics`
- **Method:** `GET`
- **Content-Type:** `application/json`
- **Authentication:** None (Localhost Platform)

#### Response Schema
```json
{
  "success": true,
  "insufficient_data": false,
  "overview": {
    "total_observations": 50,
    "valid_observations": 50,
    "invalid_observations": 0,
    "sample_target": 50,
    "remaining_to_target": 0,
    "target_reached": true,
    "collection_progress_pct": 100.0,
    "study_status": "TARGET_REACHED",
    "https_adoption_pct": 96.0,
    "mean_trust_score": 88.4,
    "mean_risk_score": 24.2
  },
  "trust_analysis": {
    "min": 45.0,
    "mean": 88.4,
    "max": 98.0,
    "std_dev": 12.1,
    "count": 50,
    "histogram": [
      {"bracket": "0–20", "count": 0, "pct": 0.0},
      {"bracket": "21–40", "count": 0, "pct": 0.0},
      {"bracket": "41–60", "count": 3, "pct": 6.0},
      {"bracket": "61–80", "count": 8, "pct": 16.0},
      {"bracket": "81–100", "count": 39, "pct": 78.0}
    ],
    "classifications": [
      {"classification": "High Trust", "count": 39, "pct": 78.0}
    ]
  },
  "risk_analysis": {
    "min": 10.0,
    "mean": 24.2,
    "max": 75.0,
    "std_dev": 14.3,
    "count": 50,
    "histogram": [
      {"bracket": "0–20", "count": 30, "pct": 60.0},
      {"bracket": "21–40", "count": 15, "pct": 30.0},
      {"bracket": "41–60", "count": 4, "pct": 8.0},
      {"bracket": "61–80", "count": 1, "pct": 2.0},
      {"bracket": "81–100", "count": 0, "pct": 0.0}
    ],
    "classifications": [
      {"classification": "Low Risk", "count": 45, "pct": 90.0}
    ]
  },
  "security_analysis": {
    "https_status": {"enabled": 48, "disabled": 2, "unknown": 0, "adoption_pct": 96.0},
    "tls_status": {"valid": 48, "invalid_or_expired": 2, "unknown": 0, "valid_pct": 96.0}
  },
  "network_analysis": {
    "ip_versions": {"ipv4": 46, "ipv6": 4, "unknown": 0, "ipv4_pct": 92.0, "ipv6_pct": 8.0},
    "infrastructure": {"cloud_datacenter": 41, "traditional_other": 9, "unknown": 0, "cloud_pct": 82.0},
    "threat_indicators": {"vpn": 0, "proxy": 0, "tor": 0, "clean": 50, "any_threat_flag": 0},
    "query_latency": {"mean_dns_ms": 14.2, "mean_api_ms": 48.5}
  },
  "geographic_and_asn_distribution": {
    "top_countries": [{"country": "United States", "count": 34, "pct": 68.0}],
    "top_asns": [{"asn": "AS13335", "org": "Cloudflare, Inc.", "count": 21, "pct": 42.0}]
  },
  "research_insights": [
    {
      "id": "insight-quota",
      "category": "reputation",
      "title": "Study Quota Completed",
      "finding": "Study target completed: exactly 50 standardized website observations have been collected and verified.",
      "metric": "50 / 50 (100.0%)",
      "type": "success"
    }
  ],
  "comparison_analytics": {
    "highest_trust_sites": [...],
    "highest_risk_sites": [...]
  }
}
```

---

## 5. Verification & Testing

The Phase 20 analytics calculation engine is verified by a dedicated test suite (`tests/test_analytics_service.py`) alongside the full regression test suite:
- **Empty Dataset ($N=0$):** Verified `insufficient_data == True`, graceful `None` percentages, and zero divide protection.
- **Partial Dataset ($N<50$):** Verified progress percentage and remaining count calculations.
- **Target Dataset ($N=50$):** Verified target reached status and 100% completion state.
- **Unknown Value Segregation:** Verified that `Unknown` security, missing geolocation, or unmeasured attributes are never conflated with positive/negative values.
- **Score Aggregations:** Verified min, mean, max, standard deviation, and 5-bracket histogram binning for Trust and Risk.
- **Security & Network Posture:** Verified IPv4/IPv6 ratio, cloud hosting density, and threat detection tallying.
- **Comparisons & Rankings:** Verified descending order for top sites and ascending order for lowest sites.
- **Deterministic Insights:** Verified factual statement generation against empirical metrics.

**Full Project Test Suite Result:**
`140 passed in 16.61s` (100% pass rate).
