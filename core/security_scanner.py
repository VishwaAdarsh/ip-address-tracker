"""
Website Security Intelligence Scanner Module for IP PULSE Platform.

Provides:
- HTTPS availability probing
- SSL/TLS certificate verification, issuer extraction, subject extraction, and expiry calculation
- TLS protocol version and cipher suite inspection
- HTTP redirect chain tracking and final URL resolution
- HTTP security header detection (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
"""
from dataclasses import dataclass, field
import datetime
import socket
import ssl
from typing import Dict, Optional, Tuple
import urllib.parse
import urllib.request


@dataclass
class SecurityInfo:
    """Dataclass holding Website Security Intelligence audit data."""

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
    security_headers: Dict[str, bool] = field(
        default_factory=lambda: {
            "hsts": False,
            "csp": False,
            "x_frame_options": False,
            "x_content_type_options": False,
        }
    )
    error_message: Optional[str] = None


def probe_ssl_certificate(hostname: str, port: int = 443, timeout: float = 3.0) -> Tuple[bool, dict, str, str]:
    """
    Establish SSL/TLS socket connection to retrieve certificate details.

    Returns:
    - Tuple: (ssl_valid: bool, cert_dict: dict, tls_version: str, cipher_name: str)
    """
    context = ssl.create_default_context()
    
    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                tls_ver = ssock.version() or "TLS"
                cipher = ssock.cipher()
                cipher_name = cipher[0] if cipher else "N/A"
                return True, cert or {}, tls_ver, cipher_name
    except Exception as e:
        # Fallback probe without hostname verification to inspect self-signed/expired cert details
        try:
            unverified_ctx = ssl._create_unverified_context()
            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                with unverified_ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert(binary_form=False)
                    tls_ver = ssock.version() or "TLS"
                    cipher = ssock.cipher()
                    cipher_name = cipher[0] if cipher else "N/A"
                    return False, cert or {}, tls_ver, cipher_name
        except Exception:
            return False, {}, "N/A", "N/A"


def _extract_cert_name(cert_field) -> str:
    """Extract Common Name (CN) or Organization Name (O) from certificate subject/issuer tuple."""
    if not cert_field:
        return "N/A"
    
    cn = "N/A"
    org = "N/A"
    
    for rdn in cert_field:
        for key, val in rdn:
            if key == "commonName":
                cn = val
            elif key == "organizationName":
                org = val
                
    return cn if cn != "N/A" else org


def _calculate_cert_expiry_days(not_after_str: str) -> int:
    """Calculate remaining days until certificate expiry date string."""
    if not not_after_str:
        return 0
    try:
        # Format: 'May 26 23:59:59 2026 GMT'
        expiry_dt = datetime.datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y GMT").replace(tzinfo=datetime.timezone.utc)
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        days_left = (expiry_dt - now_dt).days
        return max(days_left, 0)
    except Exception:
        return 0


class RedirectTrackerHandler(urllib.request.HTTPRedirectHandler):
    """Custom HTTP redirect handler to count redirect hops."""

    def __init__(self):
        super().__init__()
        self.redirect_count = 0
        self.history = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirect_count += 1
        self.history.append(newurl)
        if self.redirect_count > 10:
            raise urllib.error.HTTPError(req.full_url, code, "Too many redirects", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def scan_website_security(target: str, timeout: float = 4.0) -> SecurityInfo:
    """
    Perform a complete website security intelligence scan on target domain or URL.

    Args:
    - target: Domain name (e.g. 'google.com') or IP address
    - timeout: Socket and HTTP request timeout in seconds

    Returns:
    - SecurityInfo dataclass instance
    """
    clean_host = target.strip().lower()
    if clean_host.startswith("http://"):
        clean_host = clean_host[7:]
    elif clean_host.startswith("https://"):
        clean_host = clean_host[8:]
    clean_host = clean_host.split("/")[0].split(":")[0]

    info = SecurityInfo(target=clean_host)

    if not clean_host:
        info.error_message = "Empty target input"
        return info

    # 1. Probe SSL/TLS Certificate
    ssl_valid, cert_dict, tls_ver, cipher_name = probe_ssl_certificate(clean_host, timeout=timeout)
    info.ssl_valid = ssl_valid
    info.https_enabled = ssl_valid or bool(cert_dict)
    info.tls_version = tls_ver
    info.cipher_suite = cipher_name

    if cert_dict:
        info.ssl_issuer = _extract_cert_name(cert_dict.get("issuer"))
        info.ssl_subject = _extract_cert_name(cert_dict.get("subject"))
        info.ssl_expiry_days = _calculate_cert_expiry_days(cert_dict.get("notAfter", ""))

    # 2. Probe HTTP Redirects & Security Headers
    probe_url = f"https://{clean_host}" if info.https_enabled else f"http://{clean_host}"
    
    redirect_handler = RedirectTrackerHandler()
    opener = urllib.request.build_opener(redirect_handler)
    
    req = urllib.request.Request(
        probe_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) IP-PULSE-SecurityScanner/2.0"},
        method="HEAD",
    )

    try:
        with opener.open(req, timeout=timeout) as response:
            info.final_url = response.geturl()
            info.redirect_count = redirect_handler.redirect_count
            
            # Inspect response security headers
            resp_headers = {k.lower(): v for k, v in response.headers.items()}
            info.security_headers["hsts"] = "strict-transport-security" in resp_headers
            info.security_headers["csp"] = "content-security-policy" in resp_headers
            info.security_headers["x_frame_options"] = "x-frame-options" in resp_headers
            info.security_headers["x_content_type_options"] = "x-content-type-options" in resp_headers
            
            if not info.https_enabled and response.geturl().startswith("https://"):
                info.https_enabled = True

    except Exception as e:
        if not info.final_url or info.final_url == "N/A":
            info.final_url = probe_url
        if not info.error_message and not info.https_enabled:
            info.error_message = f"HTTP probe notice: {str(e)[:60]}"

    return info
