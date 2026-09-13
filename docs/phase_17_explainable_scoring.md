# IP PULSE — Phase 17: Explainable Website Trust & IP Risk Engine
## Academic Methodology & Technical Architecture Specification

**Project:** IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform  
**Component:** Explainable Website Trust & IP Risk Engine  
**Module:** `core/risk_engine.py`  
**API Endpoints:** `/api/analyze`, `/api/status`  
**Frontend Components:** `#score-explanation-modal`, Score Cards with "Why this score?" dialog  

---

## 1. Executive Summary & Academic Objective

In traditional network monitoring and threat intelligence dashboards, security scores are frequently opaque "black box" numbers. Users and analysts are presented with an arbitrary 0–100 score without insight into which network observables triggered deductions or rewards. In academic research and regulated cybersecurity environments, opaque metrics fail the requirements of:
1. **Auditability:** Auditors must verify exactly which signals contributed to a judgment.
2. **Determinism:** Identical technical observations must produce identical mathematical results.
3. **Fairness & Neutrality:** The absence of information must never be conflated with guilt or malicious intent.
4. **Separation of Concerns:** Application transport encryption (Website Trust) operates at a distinct OSI layer from network routing infrastructure (IP Risk).

Phase 17 implements the **Authoritative Explainable Website Trust & IP Risk Engine** for IP PULSE. Built directly into the Python backend (`core/risk_engine.py`), it decouples Website Trust from IP Risk, attributes fine-grained point deltas to verified technical signals, computes independent evidence confidence metrics, and renders full explainability to the user via an interactive glassmorphic modal dialog.

---

## 2. Decoupled Dual-Engine Architecture

A central innovation in Phase 17 is the complete decoupling of **Website Trust Score** and **IP Risk Score**.

```
                           +------------------------+
                           | Target Input (Host/IP) |
                           +-----------+------------+
                                       |
                 +---------------------+---------------------+
                 |                                           |
                 v                                           v
    +-------------------------+                 +-------------------------+
    | Website Security Engine |                 | IP Intelligence Engine  |
    | (HTTPS, TLS, Headers)   |                 | (Tor, Proxy, VPN, ASN)  |
    +------------+------------+                 +------------+------------+
                 |                                           |
                 v                                           v
    +-------------------------+                 +-------------------------+
    |  Website Trust Engine   |                 |      IP Risk Engine     |
    |  Base Score: 50         |                 |      Base Score: 5      |
    |  Range: 0–100           |                 |      Range: 0–100       |
    +------------+------------+                 +------------+------------+
                 |                                           |
                 +---------------------+---------------------+
                                       |
                                       v
                        +------------------------------+
                        |  Authoritative RiskScore     |
                        |  - Structured Trust Result   |
                        |  - Structured IP Risk Result |
                        |  - Analytical Disclaimers    |
                        +--------------+---------------+
                                       |
                        +--------------+---------------+
                        |                              |
                        v                              v
               +-----------------+            +------------------+
               | JSON REST API   |            | Frontend UI      |
               | /api/analyze    |            | Explainability   |
               +-----------------+            | Modal Dialog     |
                                              +------------------+
```

### Why `Trust != 100 - Risk`?
In naive systems, `Risk = 100 - Trust`. This formulation is technically flawed:
- **Case 1 (Phishing on Cloudflare):** A phishing domain may enforce valid TLS 1.3 encryption, provide a healthy DigiCert certificate, and return Strict-Transport-Security (HSTS). Its **Website Trust Score** is high (e.g., 90/100) because transport encryption is intact. However, its hosting may reside on an anonymous bulletproof provider or compromised VPS.
- **Case 2 (Benign Internal University Server):** A local university research server might serve plaintext HTTP (`http://lab.cs.univ.edu`) due to legacy equipment. Its **Website Trust Score** is low (e.g., 25/100) due to unencrypted transport. However, its IP resides on an authoritative national research and education network (NREN / Commercial ISP) with zero Tor, VPN, or proxy indicators. Its **IP Risk Score** is baseline low (5/100).

Decoupling these engines ensures each dimension accurately reflects its respective technical layer without cross-contamination.

---

## 3. Authoritative Scoring Methodology

### 3.1 Website Trust Score (0–100)
- **Primary Domain:** Transport Layer Security, X.509 Cryptography, HTTP Protocol Security Headers.
- **Base Neutral Score:** `50` (Neutral baseline before security probes).
- **Mathematical Formula:**
  $$\text{Trust Score} = \text{clamp}\left(50 + \sum \text{Points}_{\text{positive}} - \sum |\text{Points}_{\text{negative}}|, 0, 100\right)$$

#### Evaluated Signals & Point Weights
| # | Technical Signal | Observed Condition | Point Delta | Classification Status | Justification / Analytical Reason |
|---|------------------|-------------------|:-----------:|:---------------------:|-----------------------------------|
| 1 | **HTTPS Protocol** | Enabled (TLS negotiated) | `+20` | `Enabled` | In-transit traffic is encrypted, safeguarding against wiretapping and MitM eavesdropping. |
| | | Disabled (Plaintext HTTP) | `-25` | `Disabled` | Traffic is unencrypted and vulnerable to cleartext interception and manipulation. |
| | | Unreachable / Timeout | `0` | `Unknown` | Probe timed out or was restricted by firewall (neutral). |
| 2 | **Certificate Presence** | X.509 Certificate Presented | `+15` | `Present` | Cryptographic public key certificate presented during TLS handshake. |
| | | No Certificate Presented | `-20` | `Missing` | Server endpoint failed to supply a public key certificate. |
| | | Handshake Skipped | `0` | `Unknown` | Endpoint unreachable or non-TLS. |
| 3 | **Certificate Trust Chain** | Valid Root CA Chain | `+15` | `Valid` | Certificate successfully validated against the operating system trust store. |
| | | Invalid / Self-Signed / Expired | `-25` | `Invalid / Untrusted` | Certificate failed cryptographic path validation (self-signed, untrusted CA, or name mismatch). |
| | | No Certificate Presented | `0` | `No Certificate` | Trust validation skipped because no certificate was returned. |
| | | Indeterminate | `0` | `Unknown` | Chain validation status could not be resolved. |
| 4 | **Certificate Lifespan** | Healthy ($\ge 30$ days remaining) | `+5` | `Healthy` | Certificate validity window is actively maintained. |
| | | Expiring Soon ($0 \le \text{days} < 30$) | `0` | `Expiring Soon` | Valid certificate approaching expiry window; renewal recommended. |
| | | Expired ($\text{days} < 0$) | `-15` | `Expired` | Certificate has lapsed beyond validity end-date. |
| | | Date Unavailable | `0` | `Unknown` | Validity dates could not be parsed. |
| 5 | **HTTPS Redirection** | HTTP upgrades to HTTPS | `+10` | `Enforced` | Plain HTTP requests automatically upgrade to encrypted HTTPS endpoints. |
| | | HTTP does not redirect | `-10` | `Not Enforced` | Unencrypted HTTP remains accessible without automatic upgrade; downgrade risks present. |
| | | Not Inspected | `0` | `Unknown` | Redirection audit was not performed. |
| 6 | **HSTS Policy** | `Strict-Transport-Security` | `+10` | `Enforced` | Mandates browser-enforced TLS, eliminating SSL-stripping attack vectors. |
| | | Not Detected | `0` | `Not Detected` | Header absent (neutral: many legitimate sites do not mandate HSTS). |
| | | Not Inspected | `0` | `Unknown` | Security headers were not inspected. |
| 7 | **Defensive Headers** | CSP or X-Frame-Options | `+5` | `Active` | Client-side framing defenses mitigate clickjacking and injection risks. |
| | | Not Detected | `0` | `Not Detected` | Framing headers absent (neutral). |
| | | Not Inspected | `0` | `Unknown` | Frame headers were not inspected. |
| 8 | **Redirect Chain Depth** | Excessive (> 3 hops) | `-10` | `Excessive` | Redirection chain exceeds 3 hops; possible misconfiguration or evasion loop. |
| | | Normal ($\le 3$ hops) | `0` | `Normal` | Standard redirection hops observed. |
| | | Hop Count Unavailable | `0` | `Unknown` | Hop count unavailable. |

---

### 3.2 IP Risk Score (0–100)
- **Primary Domain:** Network Routing Infrastructure, Autonomous System Classification, Anonymizer Detection.
- **Base Ambient Risk:** `5` (Normal, benign internet infrastructure carries a small baseline ambient exposure).
- **Mathematical Formula:**
  $$\text{IP Risk Score} = \text{clamp}\left(5 + \sum \text{Points}_{\text{risk}} - \sum |\text{Points}_{\text{mitigation}}|, 0, 100\right)$$

#### Evaluated Signals & Point Weights
| # | Technical Signal | Observed Condition | Point Delta | Status | Analytical Explanation |
|---|------------------|-------------------|:-----------:|:------:|------------------------|
| 1 | **Tor Exit Node** | Active Tor Relay Exit | `+65` | `Detected` | IP is an active public Tor exit node; frequently leveraged for anonymity or automated attacks. |
| | | Not Tor Exit | `0` | `Not Detected` | No Tor exit signatures detected (neutral). |
| | | Status Unknown | `0` | `Unknown` | Tor exit verification was not performed. |
| 2 | **Proxy Gateway** | Public/Commercial Proxy | `+25` | `Detected` | IP operates as a public or commercial proxy intermediary. |
| | | Not a Proxy | `0` | `Not Detected` | No proxy indicators detected (neutral). |
| | | Status Unknown | `0` | `Unknown` | Proxy status was not verified. |
| 3 | **Commercial VPN** | VPN Service Exit | `+20` | `Detected` | IP is associated with commercial VPN exit infrastructure. |
| | | Not a VPN | `0` | `Not Detected` | No VPN indicators detected (neutral). |
| | | Status Unknown | `0` | `Unknown` | VPN status was not verified. |
| 4 | **Datacenter Hosting** | Commercial Cloud / Facility | `+10` | `Detected` | Host resides in an enterprise cloud facility rather than consumer residential ISP. (Not inherently malicious). |
| | | Consumer / Residential ISP | `0` | `Not Detected` | Standard subscriber or institutional access network. |
| | | Status Unknown | `0` | `Unknown` | Datacenter classification was not determined. |
| 5 | **Edge Hub Context** | Verified CDN Edge Hub | `-5` | `Active CDN` | Major CDN edge presence (e.g. Cloudflare, Akamai) dampens raw origin exposure risks. |
| | | Enterprise / ISP / Cloud | `0` | Neutral | Standard network context (neutral). |
| | | Status Unknown | `0` | `Unknown` | Network context unclassified. |

---

## 4. Analytical Classifications & Boundaries

To prevent overclaiming and reckless assertions (e.g. claiming a site is "100% Guaranteed Safe" or "Confirmed Criminal Hacker"), the engine applies non-overclaiming analytical tiers:

### 4.1 Website Trust Classification Tiers
| Score Range | Analytical Classification | Meaning & Recommended Action |
|:-----------:|:-------------------------:|------------------------------|
| **80 – 100** | `LIKELY SAFE` | Comprehensive cryptographic security and transport encryption verified. |
| **60 – 79** | `GENERALLY SAFE` | Standard TLS transport active; minor optional headers or expiry warnings noted. |
| **40 – 59** | `REVIEW RECOMMENDED` | Mixed security posture or unverified configurations; manual inspection advised. |
| **20 – 39** | `SUSPICIOUS` | Significant security deficiencies (e.g., untrusted certificate, no redirection). |
| **0 – 19** | `HIGH RISK` | Critical failures observed (plaintext HTTP, missing or invalid certificates). |
| *No data* | `UNKNOWN` | Zero signals available for evaluation. |

### 4.2 IP Risk Classification Tiers
| Score Range | Analytical Classification | Meaning & Recommended Action |
|:-----------:|:-------------------------:|------------------------------|
| **0 – 19** | `LOW RISK` | Standard ISP or CDN infrastructure with zero anonymization indicators. |
| **20 – 39** | `MODERATE` | Minor risk indicators observed (e.g., commercial VPN or datacenter IP). |
| **40 – 59** | `ELEVATED` | Multiple proxy or anonymizing intermediaries detected. |
| **60 – 79** | `HIGH RISK` | High-anonymity routing verified (e.g., active Tor exit node). |
| **80 – 100** | `CRITICAL` | Severe compound exposure (Tor exit + proxy + hosting indicators). |
| *No data* | `UNKNOWN` | Zero signals available for evaluation. |

---

## 5. Evidence Coverage & Independent Confidence Rating

Confidence in IP PULSE is **strictly independent of the score value**. A site can have a very low score (e.g. 10/100) with **HIGH confidence** if all 8 security probes succeeded and proved the site is insecure. Conversely, a site can have a neutral score (50/100) with **UNKNOWN confidence** if network timeouts prevented any signals from being observed.

### 5.1 Evidence Coverage Ratio
Evidence coverage is formatted as a human-readable fraction:
$$\text{Coverage} = \frac{\text{Available Verified Signals}}{\text{Total Inspectable Signals}}$$
- Website Trust inspects up to **8 signals** (`X/8`).
- IP Risk inspects up to **5 signals** (`Y/5`).

### 5.2 Confidence Tiers
$$\text{Ratio} = \frac{\text{Available Count}}{\text{Total Count}} - \text{Penalty}$$
*(A 0.15 penalty applies to IP Risk confidence if geolocation resolution failed).*

| Ratio Range | Confidence Tier | Description |
|:-----------:|:---------------:|-------------|
| $\ge 80\%$ | `HIGH` | Comprehensive evidence available; high evaluation certainty. |
| $50\% – 79\%$ | `MEDIUM` | Moderate evidence coverage; sufficient for preliminary assessment. |
| $20\% – 49\%$ | `LOW` | Limited signals available; assessment should be treated with caution. |
| $< 20\%$ | `UNKNOWN` | Insufficient evidence to formulate a reliable assessment. |

---

## 6. Neutral Handling of Missing/Unknown Data

A core scientific requirement of the engine:
> **Unknown $\ne$ Safe. Unknown $\ne$ Dangerous.**

When a probe fails (e.g., DNS timeout, socket connection reset, rate limit):
1. **0 Points Added or Subtracted:** Unknown signals never adjust the score.
2. **Explicit Listing:** Unknown signals are collected into `unknown_signals` and shown to the user in the explanation breakdown.
3. **Coverage Impact:** Unknown signals reduce the Evidence Coverage ratio and lower the Confidence Tier, truthfully informing the user that the assessment is incomplete.

---

## 7. Frontend Explainability Dialog ("Why this score?")

The user interface exposes this data via an accessible, glassmorphic modal dialog (`#score-explanation-modal`).

### 7.1 Interactive Features
- **Direct Card Integration:** Both Website Trust and IP Risk cards feature a distinct `"Why this score?"` button with evidence coverage pills (e.g. `Coverage: 8/8 • HIGH`).
- **Tab Switching:** An internal tab switcher allows instant toggling between "Website Trust Score Breakdown" and "IP Risk Score Breakdown".
- **Visual Signal Badges:**
  - Positive points: Green pill badge (`+20 pts`, `+15 pts`, `+10 pts`).
  - Deductions / Risk points: Crimson pill badge (`-25 pts`, `+65 Risk`, `-15 pts`).
  - Neutral / Unknown: Dark grey pill badge (`0 pts`, `Neutral`, `Unverified`).
- **Contextual Reasoning:** Each signal displays the technical rationale explaining *why* the points were awarded or deducted.
- **Ethical Disclaimers:** Every dialog displays the analytical disclaimer prominently at the footer.

---

## 8. Mandatory Analytical & Ethical Disclaimers

To protect the integrity of the project and comply with cybersecurity analytical standards, the following disclaimers are programmatically attached to all evaluation outputs and displayed in the UI:

> **Unified Disclaimer:**  
> *"IP PULSE scores are heuristic analytical assessments based on available technical signals. They do not guarantee that a website is legitimate, safe, fraudulent, or malicious. IP Risk reflects observed network indicators and should not be interpreted as proof of malicious activity."*

> **Website Trust Disclaimer:**  
> *"IP PULSE Website Trust Scores are heuristic analytical assessments derived strictly from observed technical indicators (e.g. TLS certificates, protocol enforcement, and headers). They do not constitute definitive proof of website legitimacy, business integrity, or safety from fraud."*

> **IP Risk Disclaimer:**  
> *"IP PULSE IP Risk Scores reflect observed network infrastructure indicators (e.g. Tor, VPN, proxy, or datacenter hosting) and must not be interpreted as definitive proof of malicious activity or threat actor origin."*

---

## 9. Comprehensive Verification & Validation

The Phase 17 implementation was validated against a 30-test automated suite (`tests/test_explainable_scoring.py`, `tests/test_risk_engine.py`, `tests/test_api_server.py`) and passed across all 104 project-wide unit tests:

| Test Identifier | Scenario Validated | Result |
|-----------------|--------------------|:------:|
| `test_01_all_positive_signals` | Full security stack on CDN edge node | **PASSED** |
| `test_02_mixed_positive_and_negative_signals` | Expired cert + HTTPS on cloud hosting | **PASSED** |
| `test_03_no_available_signals_empty_or_none` | None/empty inputs return neutral defaults | **PASSED** |
| `test_04_unknown_signals_neutral_zero_points` | Missing fields yield 0 pt deltas | **PASSED** |
| `test_05_https_enabled_vs_disabled` | HTTPS enabled (+20) vs disabled (-25) | **PASSED** |
| `test_06_invalid_certificate_vs_valid_certificate` | Valid (+15) vs untrusted root CA (-25) | **PASSED** |
| `test_07_vpn_detected` | VPN exit detection (+20 risk) | **PASSED** |
| `test_08_proxy_detected` | Proxy gateway detection (+25 risk) | **PASSED** |
| `test_09_tor_detected` | Tor exit node detection (+65 risk) | **PASSED** |
| `test_10_datacenter_infrastructure` | Cloud datacenter hosting (+10 risk, low tier) | **PASSED** |
| `test_11_normal_infrastructure_baseline_risk_not_zero` | Residential ISP baseline (5 risk) | **PASSED** |
| `test_12_multiple_risk_signals_combined` | Tor + Proxy + Datacenter compound risk | **PASSED** |
| `test_13_determinism` | 50 consecutive iterations yield identical scores | **PASSED** |
| `test_14_score_never_below_zero` | Negative points clamp strictly at 0 | **PASSED** |
| `test_15_score_never_exceeds_100` | Positive points clamp strictly at 100 | **PASSED** |
| `test_16_classification_thresholds_mapping` | Accurate tier boundary classification | **PASSED** |
| `test_17_confidence_calculation_independence_from_score` | Independence of confidence from score | **PASSED** |
| `test_18_evidence_coverage_calculation` | Evidence coverage format `X/Y` | **PASSED** |

---

## 10. Viva Defense & Academic Q&A Preparation

### Q1: Why did you create two separate scores instead of one unified "Security Score"?
> **Candidate Answer:** Transport encryption and network routing operate on completely different layers. A fraudulent phishing website can easily install a free, valid Let's Encrypt SSL certificate and proxy through Cloudflare. If we merged both scores into one, the valid SSL certificate would mask the malicious hosting, or legitimate university servers without HTTPS would be wrongly accused of being cyberattack hosts. Decoupling Website Trust (application layer) from IP Risk (infrastructure layer) provides rigorous, uncorrupted intelligence.

### Q2: Why is the baseline IP Risk Score 5 instead of 0?
> **Candidate Answer:** In internet security research, no connected host has zero exposure. Every host connected to the public IPv4/IPv6 internet is subject to ambient port scans, routing path fluctuations, and external probe traffic. Starting at a baseline of 5 acknowledges ambient internet reality rather than making a false mathematical claim of absolute invulnerability.

### Q3: How does your engine handle missing or timeout data?
> **Candidate Answer:** We strictly enforce the principle that *Unknown is neither Safe nor Dangerous*. When a signal cannot be gathered, it receives exactly 0 points. It does not penalize the website, nor does it grant unearned credit. Instead, the signal is explicitly recorded in `unknown_signals`, reducing the Evidence Coverage ratio (e.g., from 8/8 down to 5/8) and lowering the Confidence rating (e.g., from HIGH to MEDIUM).

### Q4: If a host is identified as a Datacenter IP, does IP PULSE classify it as malicious?
> **Candidate Answer:** Absolutely not. Datacenter hosting simply indicates that the IP belongs to a commercial facility (such as AWS, Google Cloud, or DigitalOcean) rather than a residential consumer subscriber. It receives a minor analytical attribution (+10 points), keeping it firmly within the `LOW RISK` tier (0–19). Datacenter hosting is standard for modern web applications.

### Q5: What prevents your scoring engine from giving non-deterministic or drifting results?
> **Candidate Answer:** The engine is purely deterministic and stateless. Given the exact same set of observed technical features (X.509 certificate validity, redirect state, security headers, Tor/VPN flags), it applies deterministic linear point summations bounded by hard clamps `max(0, min(100, score))`. We verified this with automated tests executing 50 consecutive runs with zero drift.

### Q6: What is the purpose of the Evidence Coverage metric?
> **Candidate Answer:** Evidence Coverage answers the question: *"Out of all the technical signals this system knows how to measure, how many were we actually able to verify?"* Displaying `8/8` or `5/8` gives users immediate transparency regarding the completeness of the scan, ensuring they know whether the score is based on comprehensive evidence or limited data.
