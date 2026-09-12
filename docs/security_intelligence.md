# Website Security Intelligence Documentation (Phase 15)

## Overview
Website Security Intelligence is a reusable service module for the **IP PULSE** platform that analyzes observable security signals of a domain/website and returns structured data without altering or breaking existing DNS, geolocation, database history, or map components.

> **Important Security Disclaimer:**  
> *"Website Security Intelligence provides observable security-related signals. It does not prove that a website is legitimate, safe, malicious, or fraudulent."*

---

## 1. Core Architecture & Data Model

The primary data structure is `WebsiteSecurityResult` defined in `core/security_scanner.py`:

```python
@dataclass
class WebsiteSecurityResult:
    domain: str
    https_enabled: Optional[bool]              # True / False / None (Unknown)
    http_to_https_redirect: Optional[bool]     # True / False / None (Unknown)
    tls_available: Optional[bool]              # True / False / None (Unknown)
    certificate_present: Optional[bool]        # True / False / None (Unknown)
    certificate_valid: Optional[bool]          # True / False / None (Unknown)
    certificate_status: str                    # "Valid", "Expired", "Not Yet Valid", "Unknown"
    certificate_issuer: str                    # Dynamic issuer name or "Unknown"
    certificate_subject: str                   # Dynamic subject name or "Unknown"
    certificate_not_before: str                # ISO 8601 string or "Unknown"
    certificate_not_after: str                 # ISO 8601 string or "Unknown"
    certificate_days_remaining: Optional[int]  # Integer days or None (Unknown)
    checked_at: str                            # ISO 8601 UTC timestamp
    errors: List[str]                          # List of non-fatal error notices
    warnings: List[str]                        # List of audit warning notices
```

---

## 2. Security Signals Implementation Details

### 2.1 Domain Normalization Utility
Function: `normalize_domain_for_security(input_target: str) -> str`
- Safely strips `http://`, `https://`, basic auth credentials (`user:pass@`), ports (`:8080`), paths (`/path`), query parameters (`?query=test`), and URL fragments (`#hash`).
- Returns clean, lowercased hostname without storing sensitive tokens or query parameters.

### 2.2 HTTPS & TLS Certificate Probing
Function: `probe_tls_certificate(hostname: str, timeout: float = 3.0)`
- Establishes a TLS socket connection via Python's built-in `ssl` module (`ssl.create_default_context()`).
- Inspects peer certificate (`getpeercert()`) to extract:
  - `certificate_issuer` & `certificate_subject` (Common Name or Organization Name)
  - `certificate_not_before` & `certificate_not_after` (ISO timestamps)
  - `certificate_days_remaining` (Calculated using `datetime.timezone.utc`)
- If certificate verification fails (e.g. self-signed or expired), executes unverified fallback socket inspection (`ssl._create_unverified_context()`) to parse certificate fields for audit without crashing.

### 2.3 HTTP → HTTPS Redirect Tracking
Handler: `ControlledRedirectHandler(max_redirects: int = 5)`
- Sends non-intrusive `HTTP` request (`http://domain`) with custom `User-Agent`.
- Follows HTTP redirects up to a maximum limit of **5 hops** to prevent unbounded redirect loops.
- Evaluates `http_to_https_redirect = True` if any URL in the redirect chain or final destination starts with `https://`.

---

## 3. Explicit Unknown / Unavailable Handling Rules

To prevent false security penalties:
- **Missing Information Rule:** Unavailable or timed-out checks explicitly return `None` (Unknown) for booleans and `"Unknown"` for string/status fields, rather than returning `False`.
- For example:
  - If TLS handshake times out: `certificate_valid = None` and `certificate_status = "Unknown"` (NOT `False`).
  - If redirect tracking fails: `http_to_https_redirect = None` (NOT `False`).

---

## 4. Network Safety & Operational Bounds

- **Non-Intrusive Probing:** Probes are strictly limited to standard SSL/TLS handshake metadata and HTTP header inspection.
- **Strict Bounds:** Socket timeouts are set to `3.0s` and HTTP redirects are capped at `5` hops.
- **Zero Port Scanning:** No vulnerability scanning, brute-forcing, directory enumeration, or intrusive network actions are performed.

---

## 5. Files Created & Modified in Phase 15

| File | Action | Purpose |
| :--- | :--- | :--- |
| `core/security_scanner.py` | Modified / Upgraded | Added `WebsiteSecurityResult`, `normalize_domain_for_security()`, `analyze_website_security()`, and explicit Unknown state logic. |
| `tests/test_security_scanner.py` | Upgraded | Added 8 automated unit tests covering domain normalization, HTTPS probing, TLS cert parsing, redirect tracking, and fallback states. |
| `docs/security_intelligence.md` | Created | Phase 15 technical documentation and security limitation disclaimers. |
