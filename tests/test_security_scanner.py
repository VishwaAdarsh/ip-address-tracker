"""
Automated Unit Tests for Website Security Intelligence (Phase 15).
"""
import unittest

from core.security_scanner import (
    WebsiteSecurityResult,
    analyze_website_security,
    normalize_domain_for_security,
    probe_tls_certificate,
    scan_website_security,
)


class TestWebsiteSecurityIntelligence(unittest.TestCase):
    """Test suite for Phase 15 Website Security Intelligence Service."""

    def test_domain_normalization(self):
        """Test domain normalization with various target URL/domain formats."""
        self.assertEqual(normalize_domain_for_security("example.com"), "example.com")
        self.assertEqual(normalize_domain_for_security("www.example.com"), "www.example.com")
        self.assertEqual(normalize_domain_for_security("https://example.com"), "example.com")
        self.assertEqual(normalize_domain_for_security("http://example.com:8080/path?query=1#frag"), "example.com")
        self.assertEqual(normalize_domain_for_security("https://user:pass@example.com/path"), "example.com")
        self.assertEqual(normalize_domain_for_security(""), "")

    def test_valid_https_website_security_analysis(self):
        """Test Website Security Analysis on a known HTTPS site (google.com)."""
        res = analyze_website_security("google.com", timeout=5.0)
        self.assertEqual(res.domain, "google.com")
        self.assertTrue(res.https_enabled)
        self.assertTrue(res.tls_available)
        self.assertTrue(res.certificate_present)
        self.assertTrue(res.certificate_valid)
        self.assertEqual(res.certificate_status, "Valid")
        self.assertNotEqual(res.certificate_issuer, "Unknown")
        self.assertIsNotNone(res.certificate_days_remaining)
        self.assertGreater(res.certificate_days_remaining, 0)
        self.assertIsNotNone(res.checked_at)

    def test_http_to_https_redirect(self):
        """Test HTTP to HTTPS redirect tracking on a domain enforcing HTTPS redirect."""
        res = analyze_website_security("http://github.com", timeout=5.0)
        self.assertEqual(res.domain, "github.com")
        self.assertTrue(res.http_to_https_redirect)
        self.assertTrue(res.https_enabled)

    def test_nonexistent_domain_security_analysis(self):
        """Test scan on invalid or nonexistent domain without application crash."""
        res = analyze_website_security("invalid-domain-xyz-123456789.org", timeout=1.0)
        self.assertEqual(res.domain, "invalid-domain-xyz-123456789.org")
        # Explicit Unknown / None states for missing information
        self.assertIsNone(res.certificate_valid)
        self.assertEqual(res.certificate_status, "Unknown")
        self.assertEqual(res.certificate_issuer, "Unknown")
        self.assertIsNone(res.certificate_days_remaining)
        self.assertGreater(len(result_warnings := res.warnings), 0)

    def test_empty_target_input(self):
        """Test empty target normalization and error recording."""
        res = analyze_website_security("")
        self.assertEqual(res.domain, "")
        self.assertIn("Target domain input is empty or invalid", res.errors)

    def test_tls_certificate_probe(self):
        """Test probe_tls_certificate helper."""
        valid, cert, tls_ver, errs, warns = probe_tls_certificate("google.com", timeout=5.0)
        self.assertTrue(valid)
        self.assertIsNotNone(cert)
        self.assertIn("TLS", tls_ver)

    def test_unknown_states_never_falsely_penalized(self):
        """Test that missing certificate data sets certificate_valid=None, NOT False."""
        res = WebsiteSecurityResult(domain="test.local")
        self.assertIsNone(res.certificate_valid)
        self.assertIsNone(res.http_to_https_redirect)
        self.assertEqual(res.certificate_status, "Unknown")

    def test_backward_compatible_security_info(self):
        """Test scan_website_security backward compatibility bridge."""
        sec_info = scan_website_security("google.com", timeout=5.0)
        self.assertEqual(sec_info.target, "google.com")
        self.assertTrue(sec_info.https_enabled)
        self.assertTrue(sec_info.ssl_valid)


if __name__ == "__main__":
    unittest.main()
