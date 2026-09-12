"""
Automated Unit Tests for core/security_scanner.py
"""
import unittest

from core.security_scanner import (
    SecurityInfo,
    _calculate_cert_expiry_days,
    _extract_cert_name,
    probe_ssl_certificate,
    scan_website_security,
)


class TestSecurityScanner(unittest.TestCase):
    """Test suite for Security Scanner module."""

    def test_cert_helpers(self):
        """Test cert name extractor and expiry calculation helpers."""
        sample_issuer = ((("commonName", "DigiCert Global Root CA"),),)
        name = _extract_cert_name(sample_issuer)
        self.assertEqual(name, "DigiCert Global Root CA")

        self.assertEqual(_extract_cert_name([]), "N/A")
        self.assertEqual(_calculate_cert_expiry_days(""), 0)

    def test_invalid_target_security_scan(self):
        """Test scan on empty or invalid hostname."""
        res = scan_website_security("")
        self.assertEqual(res.target, "")
        self.assertIsNotNone(res.error_message)

    def test_live_domain_security_scan(self):
        """Test live domain security scan on google.com."""
        res = scan_website_security("google.com", timeout=5.0)
        self.assertEqual(res.target, "google.com")
        self.assertTrue(res.https_enabled)
        self.assertTrue(res.ssl_valid)
        self.assertNotEqual(res.ssl_issuer, "N/A")
        self.assertIn("google", res.final_url.lower())

    def test_probe_ssl_certificate_fallback(self):
        """Test SSL probe error handling on invalid host."""
        is_valid, cert, tls_ver, cipher = probe_ssl_certificate("invalid-domain-xyz-123456789.org", timeout=1.0)
        self.assertFalse(is_valid)
        self.assertEqual(cert, {})
        self.assertEqual(tls_ver, "N/A")


if __name__ == "__main__":
    unittest.main()
