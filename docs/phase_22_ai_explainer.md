# Phase 22: Explainable AI Intelligence Layer

## 1. Executive Summary

Phase 22 introduces an **optional, evidence-grounded AI explanation layer** for IP PULSE ("IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform"). Operating strictly as an interpretive and explainability engine, this layer translates deterministic technical telemetry into structured, professional, human-understandable insights.

### Core Architectural Guarantees
- **Strict Evidence Grounding:** The AI engine synthesizes **only** verified technical evidence (transport encryption, TLS validity, ASN routing, infrastructure classification, and heuristics). It is strictly prohibited from fabricating DNS records, certificates, threat reputation, blacklist status, or company profiles.
- **Zero Factual Authority / Score Preservation:** The AI layer never determines, overrides, or alters:
  - Website Trust Score ($0\text{--}100$)
  - IP Risk Score ($0\text{--}100$)
  - Geolocation coordinates
  - ASN / ISP registrations
  - VPN / Proxy / Tor / Datacenter detections
- **Prohibition of Definitive Security Claims:** The system strictly rejects and sanitizes absolute claims (e.g. *"100% safe"*, *"definitely fake"*, *"completely secure"*), employing calibrated language such as *"appears lower risk based on available signals"*, *"generally safe indicators"*, or *"review recommended"*.
- **Explicit Handling of Unknowns:** Any unobserved or unmeasured dimension (e.g. unknown ASN, absent HSTS header, unresolvable location) is categorized as `UNKNOWN` or *"Information unavailable"*.
- **Manual-First Interactive Trigger:** Explanations are generated exclusively on-demand when the user clicks **"Explain with AI"**. Batch scanning and Field Study operations are never executed automatically.
- **Offline / Zero-Cost Resilience:** Includes an offline, deterministic **Rule-Based Factual Engine** active by default when no external API key is set, ensuring the application always operates with zero external dependencies and zero cost.

---

## 2. Architecture & Data Flow

```
+----------------------------------------------------------------------------------------------------+
|                                    STITCH WEB FRONTEND (SPA)                                       |
|                                       Tab 4: AI Explanation                                        |
+----------------------------------------------------------------------------------------------------+
                                                  |
                     [Manual Click: "Explain with AI" (with debouncing)]
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                      API LAYER (api/server.py)                                     |
|                      GET /api/explain/status  |  POST /api/explain                                 |
+----------------------------------------------------------------------------------------------------+
                                                  |
                             [Data-Minimized Intelligence Payload]
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                EXPLAINER ENGINE (core/ai_explainer.py)                             |
|                                                                                                    |
|    +------------------------------------------------------------------------------------------+    |
|    | 1. In-Memory Evidence Hash Cache (Key: Target + Scores + Signals -> AIExplanationResult) |    |
|    +------------------------------------------------------------------------------------------+    |
|                                                  | (Cache Miss)                                    |
|                                                  v                                                 |
|    +------------------------------------------------------------------------------------------+    |
|    | 2. Provider Abstraction (AIExplanationProvider ABC)                                      |    |
|    |    - RuleBasedAIProvider (Deterministic factual engine, zero-cost, offline)              |    |
|    |    - GeminiAIProvider (Google Gemini API via google-genai / REST with structured JSON)  |    |
|    +------------------------------------------------------------------------------------------+    |
|                                                  |                                                 |
|                                                  v                                                 |
|    +------------------------------------------------------------------------------------------+    |
|    | 3. Response Validation & Claim Sanitization (Replaces absolute claims; verifies schema)  |    |
|    +------------------------------------------------------------------------------------------+    |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                    [Validated Structured JSON]
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                 STITCH UI STRUCTURED RENDERING                                     |
|  - Executive Summary                                                                               |
|  - Trust Score Analysis & IP Risk Score Analysis                                                   |
|  - Signal Tri-Grid: Strongest Positive | Key Risk Factors | Unknown / Unavailable                  |
|  - Assessment & Recommendations • Analytical Limitations Disclaimer                                |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Provider Configuration & Environment Variables

All settings are configured via environment variables or a local `.env` file (loaded via `config/settings.py`):

| Variable | Type | Default | Description |
|---|---|---|---|
| `AI_ENABLED` | `bool` | `true` | Master toggle. Set to `false` to completely disable the AI explanation layer. |
| `AI_PROVIDER` | `str` | `"rule_based"` | Provider to use: `"rule_based"` (default offline factual engine) or `"gemini"`. |
| `AI_API_KEY` | `str` | `""` | API key for external provider. Automatically checks `GEMINI_API_KEY` as fallback. |
| `AI_MODEL` | `str` | `"gemini-2.5-flash"` | Model identifier used when calling Gemini. |
| `AI_TIMEOUT` | `float` | `10.0` | Network timeout in seconds for external AI calls. |

### Security & Key Hygiene
- API keys are read exclusively server-side.
- Keys are **never** rendered into HTML, sent to the browser in API responses, or exposed to client JavaScript.
- If an external provider is selected without an API key, the system returns `status="provider_unavailable"` without crashing.

---

## 4. Privacy & Data Minimization

The `build_explanation_payload()` function filters the target intelligence to include strictly the minimum technical attributes necessary:
- **Included:** Target domain/IP, resolved IP, IP version, country, region, city, coordinates, ASN, organization, ISP, infrastructure type, network type, transport security flags (HTTPS, TLS validity, cipher, HSTS, CSP, redirects), Trust Score, IP Risk Score, confidence rating, and positive/negative signal lists.
- **Excluded:** Internal filesystem paths, SQLite connection strings, database credentials, server environment variables, history records of other targets, and client device identifiers.

---

## 5. API Endpoint Specifications

### 5.1 `GET /api/explain/status`
Returns metadata and operational status of the AI layer.

**Example Response:**
```json
{
  "status": "operational",
  "enabled": true,
  "provider": "rule_based",
  "model": "deterministic-factual-v1",
  "description": "Evidence-grounded explainability engine for Website Trust and IP Risk."
}
```

### 5.2 `POST /api/explain`
Generates an evidence-grounded explanation for a specified target or pre-scanned intelligence object.

**Request Payload:**
```json
{
  "target": "example.com",
  "intelligence": { ... },
  "provider": "rule_based",
  "bypass_cache": false
}
```
*Note: If `intelligence` is passed, the engine uses it directly, avoiding redundant network rescanning.*

**Example Response:**
```json
{
  "status": "success",
  "provider": "rule_based",
  "model": "deterministic-factual-v1",
  "summary": "Target 'example.com' resolves to 93.184.216.34 (EDGECAST, AS15133) geolocated in Los Angeles, United States. The host operates under a 'CDN / Edge Hub' profile enforcing encrypted HTTPS. Deterministic evaluation registers a Website Trust Score of 92/100 and an IP Risk Score of 12/100, placing it in the 'Low Risk' bracket.",
  "trust_explanation": "The Website Trust Score of 92/100 is driven by empirical transport signals: A valid TLS certificate is present, issued by 'DigiCert Global Root G2'; Certificate has 180 days remaining before expiration; HTTP Strict Transport Security (HSTS) is enabled, protecting against downgrade attacks.",
  "risk_explanation": "The IP Risk Score of 12/100 reflects infrastructure and network provenance: Hosting infrastructure is located in a datacenter / cloud facility (CDN / Edge Hub).",
  "positive_signals": [
    "HTTPS transport enforced",
    "Valid TLS certificate with >30 days validity",
    "HTTP Strict Transport Security (HSTS) active"
  ],
  "negative_signals": [
    "Infrastructure hosted in Datacenter / Cloud environment"
  ],
  "unknown_signals": [
    "Content Security Policy (CSP) Header"
  ],
  "recommendation": "The target appears lower risk based on available technical signals. Network profile aligns with established hosting norms. Standard precautions apply.",
  "limitations": "AI explanations are analytical syntheses of empirical point-in-time telemetry. They do not constitute certified cybersecurity audits, legal attestations, or guarantees of future behavior. Deterministic classifications and underlying technical evidence remain authoritative.",
  "cached": false,
  "error_message": null,
  "created_at": "2026-09-14T00:22:00+00:00"
}
```

---

## 6. Error & State Handling

The UI and backend cleanly transition through 4 operational states:
1. **Idle State (`#ai-explanation-idle`):** Displayed initially when a scan completes. Informs user that explanation is available on-demand.
2. **Generating State (`#ai-explanation-loading`):** Displays animated spinner and pulse skeleton while processing. Button is disabled to prevent duplicate calls.
3. **Success State (`#ai-explanation-result`):** Renders executive summary, dual score cards, positive/risk/unknown tri-grid, recommendation, and limitations disclaimer.
4. **Error / Unavailable State (`#ai-explanation-error`):** If a network timeout, quota exceeded (429), or missing API key occurs, an alert banner displays the informative message while explicitly reassuring the user that deterministic analysis remains 100% operational.

---

## 7. How to Disable AI

To completely disable the AI explanation layer:
1. Set `AI_ENABLED=false` in `.env` or the operating system environment:
   ```powershell
   $env:AI_ENABLED="false"
   ```
2. In this state, `POST /api/explain` returns `status="provider_unavailable"`, and the UI displays:
   *"AI explanation layer is currently disabled in configuration (AI_ENABLED=false). Deterministic analysis remains fully available."*
3. All underlying DNS, Geolocation, Security Scanner, Risk Engine, Field Study, and Export features continue operating without interruption.
