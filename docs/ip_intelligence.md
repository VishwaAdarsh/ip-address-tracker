# IP Intelligence & Infrastructure Analysis Documentation (Phase 16)

## Overview
IP Intelligence & Infrastructure Analysis is an extension module for the **IP PULSE** platform that analyzes network provenance, provider categories, infrastructure types, and anonymization signals for resolved IP addresses.

> **Important Security & Disclaimer Notice:**  
> *"IP infrastructure classification and anonymization indicators are based on available intelligence signals and should not be interpreted as definitive proof of malicious activity."*

---

## 1. Data Model & Architecture (`IPIntelligenceResult`)

Defined in `core/ip_intel.py`, `IPIntelligenceResult` structures network metadata with explicit `"Unknown"` defaults:

```python
@dataclass
class IPIntelligenceResult:
    ip_address: str
    ip_version: str            # "IPv4", "IPv6", "Unknown"
    asn: str                   # e.g. "AS15169" or "Unknown"
    asn_name: str              # e.g. "Google LLC" or "Unknown"
    organization: str          # e.g. "Google LLC" or "Unknown"
    isp: str                   # e.g. "Google LLC" or "Unknown"
    network_type: str          # "Cloud", "Datacenter", "Hosting", "Enterprise", "Residential", "Mobile", "Education", "Government", "Unknown"
    infrastructure_type: str   # "CDN / Edge Hub", "Cloud Hosting", "Commercial ISP", "Enterprise Network", "Unknown"
    vpn_status: str            # "Detected", "Not Detected", "Unknown"
    proxy_status: str          # "Detected", "Not Detected", "Unknown"
    tor_status: str            # "Detected", "Not Detected", "Unknown"
    datacenter_status: str     # "Detected", "Not Detected", "Unknown"
    country: str               # Country name or "Unknown"
    network_country: str       # ISO country code or "Unknown"
    checked_at: str            # ISO 8601 UTC timestamp
    errors: List[str]          # Non-fatal error notices
    warnings: List[str]        # Audit warning notices
```

---

## 2. Provider Abstraction Layer

All IP Intelligence services are isolated behind a clean provider interface (`IPIntelligenceProvider`):

```python
class IPIntelligenceProvider:
    def analyze_ip(self, ip_address: str, asn: str, org: str, isp: str, raw_signals: dict) -> IPIntelligenceResult:
        raise NotImplementedError()
```

- **`StandardIPIntelligenceProvider`:** The primary implementation. Integrates local ASN & network classification heuristics with raw signals returned by underlying geolocation endpoints (`ipapi.co` / `ip-api.com`).
- **Extensibility:** New external intelligence or reputation providers (e.g. MaxMind, IPinfo, GreyNoise) can be plugged in seamlessly by subclassing `IPIntelligenceProvider` without modifying UI or service orchestration code.

---

## 3. Anonymization & Infrastructure Signals

1. **VPN Detection (`vpn_status`)**:
   - Statuses: `"Detected"`, `"Not Detected"`, `"Unknown"`.
   - **Crucial Rule:** A datacenter or cloud IP is **never** automatically assumed to be a VPN. VPN status requires an explicit verified signal or recognized commercial VPN provider ASN. Unverified signals return `"Unknown"`.

2. **Proxy Detection (`proxy_status`)**:
   - Statuses: `"Detected"`, `"Not Detected"`, `"Unknown"`.

3. **Tor Exit Node Detection (`tor_status`)**:
   - Statuses: `"Detected"`, `"Not Detected"`, `"Unknown"`.

4. **Datacenter Detection (`datacenter_status`)**:
   - Statuses: `"Detected"`, `"Not Detected"`, `"Unknown"`.

5. **Network Type Classification (`network_type`)**:
   - Categories: `"Cloud"`, `"Datacenter"`, `"Hosting"`, `"Enterprise"`, `"Residential"`, `"Mobile"`, `"Education"`, `"Government"`, `"Unknown"`.

6. **Infrastructure Type Classification (`infrastructure_type`)**:
   - Categories: `"CDN / Edge Hub"`, `"Cloud Hosting"`, `"Commercial ISP"`, `"Enterprise Network"`, `"Unknown"`.

---

## 4. Error Handling & API Quota Resilience

- **Quota / Rate Limit (HTTP 429) & Timeouts:** If an external provider is rate-limited, times out, or fails, the service catches the exception, appends an error message to `errors`, and safely populates unverified indicator fields with `"Unknown"`.
- **Zero Application Crashes:** Network failures never throw unhandled exceptions or freeze the PySide6 main thread.

---

## 5. Files Created & Modified in Phase 16

| File | Action | Purpose |
| :--- | :--- | :--- |
| `core/ip_intel.py` | Modified / Upgraded | Added `IPIntelligenceResult`, `IPIntelligenceProvider`, `StandardIPIntelligenceProvider`, and `analyze_ip_infrastructure()`. |
| `tests/test_ip_intel.py` | Upgraded | Added 7 automated unit tests covering IPv4/IPv6, cloud/ISP classification, Tor/VPN/proxy signals, quota 429 handling, and mock provider failures. |
| `docs/ip_intelligence.md` | Created | Technical documentation, provider abstraction design, and disclaimer notices for Phase 16. |
