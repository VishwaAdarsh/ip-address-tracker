"""
Website Security Intelligence Scanner Module for IP PULSE Platform (Phase 15).

Provides:
- Safe domain normalization utility (extracts hostname without credentials, port, path, query, fragment)
- Structured WebsiteSecurityResult data model with explicit Unknown/None handling
- HTTPS status probe
- HTTP -> HTTPS redirect chain tracking with redirect limits
- SSL/TLS certificate inspection (presence, validity, status, issuer, subject, validity period, expiry days)
- Graceful exception handling ensuring zero application crashes on network/TLS/cert failures
"""
from dataclasses import dataclass, field
import datetime
import socket
import ssl
from typing import List, Optional, Tuple
import urllib.parse
import urllib.request


def normalize_domain_for_security(input_target: str) -> str:
    """
    Safely extract clean hostname from target domain, URL, or IP input.

    Handles:
    - example.com
    - www.example.com
    - https://example.com
    - http://example.com:8080/path
    - https://user:pass@example.com/path?query=1#frag

    Returns:
    - Clean hostname string without scheme, credentials, port, path, query, or fragment.
    """
    if not input_target:
        return ""

    raw = input_target.strip().lower()

    # Prepend scheme if missing for urlparse parsing
    if not (raw.startswith("http://") or raw.startswith("https://")):
        raw = "http://" + raw

    try:
        parsed = urllib.parse.urlparse(raw)
        hostname = parsed.hostname or parsed.path.split("/")[0]
        # Remove trailing dots
        return hostname.rstrip(".").lower()
    except Exception:
        # Fallback simple string splitting
        clean = input_target.strip().lower()
        if clean.startswith("http://"):
            clean = clean[7:]
        elif clean.startswith("https://"):
            clean = clean[8:]
        return clean.split("/")[0].split(":")[0].split("?")[0].split("#")[0].rstrip(".")


@dataclass
class WebsiteSecurityResult:
    """
    Structured data model for Website Security Intelligence (Phase 15).
    
    Uses explicit None/Unknown states to ensure missing info is never falsely penalized as a security failure.
    """

    domain: str = ""
    https_enabled: Optional[bool] = None               # True / False / None for Unknown
    http_to_https_redirect: Optional[bool] = None      # True / False / None for Unknown
    tls_available: Optional[bool] = None               # True / False / None for Unknown
    certificate_present: Optional[bool] = None         # True / False / None for Unknown
    certificate_valid: Optional[bool] = None           # True / False / None for Unknown
    certificate_status: str = "Unknown"                # "Valid", "Expired", "Not Yet Valid", "Unknown"
    certificate_issuer: str = "Unknown"                # Dynamic string or "Unknown"
    certificate_subject: str = "Unknown"               # Dynamic string or "Unknown"
    certificate_not_before: str = "Unknown"            # ISO string or "Unknown"
    certificate_not_after: str = "Unknown"             # ISO string or "Unknown"
    certificate_days_remaining: Optional[int] = None   # int remaining days or None for Unknown
    checked_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SecurityInfo:
    """Backward-compatible SecurityInfo dataclass bridge."""

    target: str = ""
    https_enabled: bool = False
    ssl_valid: bool = False
    ssl_issuer: str = "N/A"
    ssl_subject: str = "N/A"
    ssl_expiry_days: int = 0
    tls_version: str = "N/A"
    cipher_suite: str = "N/A"
    redirect_count: int = 0
    final_url: str = "N/A"
    security_headers: dict = field(
        default_factory=lambda: {
            "hsts": False,
            "csp": False,
            "x_frame_options": False,
            "x_content_type_options": False,
        }
    )
    error_message: Optional[str] = None


def _format_cert_date(date_str: str) -> str:
    """Format certificate date string into ISO format."""
    if not date_str:
        return "Unknown"
    try:
        dt = datetime.datetime.strptime(date_str, "%b %d %H:%M:%S %Y GMT").replace(tzinfo=datetime.timezone.utc)
        return dt.isoformat()
    except Exception:
        return date_str


def _extract_cert_field_name(cert_field) -> str:
    """Extract Common Name (CN) or Organization Name (O) from certificate subject/issuer tuple."""
    if not cert_field:
        return "Unknown"

    cn = "Unknown"
    org = "Unknown"

    for rdn in cert_field:
        for key, val in rdn:
            if key == "commonName":
                cn = val
            elif key == "organizationName":
                org = val

    return cn if cn != "Unknown" else org


def probe_tls_certificate(hostname: str, port: int = 443, timeout: float = 3.0) -> Tuple[Optional[bool], dict, str, List[str], List[str]]:
    """
    Probe TLS socket to inspect certificate.

    Returns:
    - Tuple: (certificate_valid: Optional[bool], cert_dict: dict, tls_version: str, errors: list, warnings: list)
    """
    errors: List[str] = []
    warnings: List[str] = []
    context = ssl.create_default_context()

    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                tls_ver = ssock.version() or "TLS"
                return True, cert or {}, tls_ver, errors, warnings
    except ssl.SSLCertVerificationError as e:
        warnings.append(f"SSL certificate verification notice: {str(e)}")
        # Inspect cert without verification to parse details
        try:
            unverified_ctx = ssl._create_unverified_context()
            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                with unverified_ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert(binary_form=False)
                    tls_ver = ssock.version() or "TLS"
                    return False, cert or {}, tls_ver, errors, warnings
        except Exception as ex:
            errors.append(f"Unverified SSL socket inspection failed: {str(ex)}")
            return False, {}, "Unknown", errors, warnings
    except Exception as e:
        warnings.append(f"TLS socket handshake skipped: {str(e)}")
        return None, {}, "Unknown", errors, warnings


class ControlledRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Custom HTTP redirect handler with strict max redirect limit."""

    def __init__(self, max_redirects: int = 5):
        super().__init__()
        self.max_redirects = max_redirects
        self.redirect_count = 0
        self.redirect_chain: List[str] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirect_count += 1
        self.redirect_chain.append(newurl)
        if self.redirect_count > self.max_redirects:
            raise urllib.error.HTTPError(req.full_url, code, "Exceeded maximum allowed redirects", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def analyze_website_security(target: str, timeout: float = 3.0) -> WebsiteSecurityResult:
    """
    Perform a complete, non-intrusive Website Security Intelligence scan on target domain or URL.

    Args:
    - target: Domain name or URL string
    - timeout: Connection and request timeout in seconds

    Returns:
    - WebsiteSecurityResult dataclass instance
    """
    domain = normalize_domain_for_security(target)
    result = WebsiteSecurityResult(domain=domain)

    if not domain:
        result.errors.append("Target domain input is empty or invalid")
        return result

    # 1. Probe TLS & Certificate
    cert_valid, cert_dict, tls_ver, tls_errs, tls_warns = probe_tls_certificate(domain, timeout=timeout)
    result.errors.extend(tls_errs)
    result.warnings.extend(tls_warns)

    if cert_dict or cert_valid:
        result.https_enabled = True
        result.tls_available = True
        result.certificate_present = True
        if cert_dict:
            result.certificate_issuer = _extract_cert_field_name(cert_dict.get("issuer"))
            result.certificate_subject = _extract_cert_field_name(cert_dict.get("subject"))
            
            not_before = cert_dict.get("notBefore", "")
            not_after = cert_dict.get("notAfter", "")
            result.certificate_not_before = _format_cert_date(not_before)
            result.certificate_not_after = _format_cert_date(not_after)

            # Check validity dates
            if not_after:
                try:
                    expiry_dt = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y GMT").replace(tzinfo=datetime.timezone.utc)
                    start_dt = datetime.datetime.strptime(not_before, "%b %d %H:%M:%S %Y GMT").replace(tzinfo=datetime.timezone.utc) if not_before else None
                    now_dt = datetime.datetime.now(datetime.timezone.utc)

                    days_rem = (expiry_dt - now_dt).days
                    result.certificate_days_remaining = days_rem

                    if now_dt > expiry_dt:
                        result.certificate_status = "Expired"
                        result.certificate_valid = False
                    elif start_dt and now_dt < start_dt:
                        result.certificate_status = "Not Yet Valid"
                        result.certificate_valid = False
                    else:
                        result.certificate_status = "Valid" if cert_valid else "Unverified"
                        result.certificate_valid = cert_valid
                except Exception as e:
                    result.warnings.append(f"Certificate date parsing notice: {str(e)}")
                    result.certificate_status = "Unknown"
                    result.certificate_valid = cert_valid
        else:
            result.certificate_valid = cert_valid
            result.certificate_status = "Valid" if cert_valid else "Unknown"
    else:
        result.tls_available = False if cert_valid is False else None
        result.certificate_present = False if cert_valid is False else None
        result.certificate_valid = None  # Explicitly Unknown
        result.certificate_status = "Unknown"

    # 2. Probe HTTP to HTTPS Redirect
    redirect_handler = ControlledRedirectHandler(max_redirects=5)
    opener = urllib.request.build_opener(redirect_handler)
    http_url = f"http://{domain}"

    req = urllib.request.Request(
        http_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) IP-PULSE-SecurityScanner/2.0"},
    )

    try:
        with opener.open(req, timeout=timeout) as response:
            final_url = response.geturl()
            has_https_in_chain = any(u.startswith("https://") for u in redirect_handler.redirect_chain) or final_url.startswith("https://")
            
            if has_https_in_chain:
                result.http_to_https_redirect = True
                result.https_enabled = True
            else:
                result.http_to_https_redirect = False
                result.https_enabled = result.https_enabled if result.https_enabled is not None else False
    except urllib.error.HTTPError as e:
        if e.code in [301, 302, 307, 308]:
            location = e.headers.get("Location", "")
            has_https_in_chain = any(u.startswith("https://") for u in redirect_handler.redirect_chain) or location.startswith("https://")
            if has_https_in_chain:
                result.http_to_https_redirect = True
                result.https_enabled = True
            else:
                result.http_to_https_redirect = False
        else:
            result.warnings.append(f"HTTP probe returned status code {e.code}")
            result.http_to_https_redirect = None  # Unknown
    except Exception as e:
        result.warnings.append(f"HTTP redirect probe skipped: {str(e)}")
        result.http_to_https_redirect = None  # Explicitly Unknown

    if result.https_enabled is None and result.tls_available is True:
        result.https_enabled = True

    return result


def scan_website_security(target: str, timeout: float = 4.0) -> SecurityInfo:
    """Backward-compatible scan_website_security bridging to SecurityInfo."""
    sec_res = analyze_website_security(target, timeout=timeout)

    return SecurityInfo(
        target=sec_res.domain,
        https_enabled=bool(sec_res.https_enabled),
        ssl_valid=bool(sec_res.certificate_valid),
        ssl_issuer=sec_res.certificate_issuer,
        ssl_subject=sec_res.certificate_subject,
        ssl_expiry_days=sec_res.certificate_days_remaining or 0,
        tls_version="TLS" if sec_res.tls_available else "N/A",
        cipher_suite="N/A",
        redirect_count=1 if sec_res.http_to_https_redirect else 0,
        final_url=f"https://{sec_res.domain}" if sec_res.https_enabled else f"http://{sec_res.domain}",
        error_message="; ".join(sec_res.errors) if sec_res.errors else None,
    )
