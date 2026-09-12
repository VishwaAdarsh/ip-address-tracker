"""
Unit tests for core/validator.py input validation module.
"""
import unittest
from core.validator import (
    InputType,
    ValidationResult,
    is_valid_domain,
    is_valid_ipv4,
    is_valid_ipv6,
    normalize_input,
    validate_input,
)


class TestInputNormalization(unittest.TestCase):
    """Test normalization of raw input strings."""

    def test_whitespace_trimming(self):
        self.assertEqual(normalize_input("  google.com  "), "google.com")
        self.assertEqual(normalize_input("\t8.8.8.8\n"), "8.8.8.8")

    def test_scheme_stripping(self):
        self.assertEqual(normalize_input("https://google.com"), "google.com")
        self.assertEqual(normalize_input("http://example.org/"), "example.org")

    def test_lowercase_conversion(self):
        self.assertEqual(normalize_input("GOOGLE.COM"), "google.com")
        self.assertEqual(normalize_input("2001:DB8::1"), "2001:db8::1")

    def test_empty_normalization(self):
        self.assertEqual(normalize_input(""), "")
        self.assertEqual(normalize_input("   "), "")


class TestDomainValidation(unittest.TestCase):
    """Test domain name validation logic."""

    def test_valid_domains(self):
        valid_domains = [
            "google.com",
            "example.org",
            "subdomain.example.com",
            "my-domain.co.uk",
            "a.b.c.d.com",
        ]
        for domain in valid_domains:
            with self.subTest(domain=domain):
                res = validate_input(domain)
                self.assertTrue(res.is_valid, f"Expected {domain} to be valid")
                self.assertEqual(res.input_type, InputType.DOMAIN)
                self.assertIsNone(res.error_message)

    def test_invalid_domains(self):
        invalid_domains = [
            "hello@123",
            "-badlabel.com",
            "badlabel-.com",
            "invalid_domain!",
            "google..com",
            "singlelabel",
        ]
        for domain in invalid_domains:
            with self.subTest(domain=domain):
                res = validate_input(domain)
                self.assertFalse(res.is_valid, f"Expected {domain} to be invalid")
                self.assertEqual(res.input_type, InputType.UNKNOWN)
                self.assertIsNotNone(res.error_message)


class TestIPv4Validation(unittest.TestCase):
    """Test IPv4 address validation logic."""

    def test_valid_ipv4(self):
        valid_ips = ["8.8.8.8", "1.1.1.1", "127.0.0.1", "192.168.1.1"]
        for ip in valid_ips:
            with self.subTest(ip=ip):
                res = validate_input(ip)
                self.assertTrue(res.is_valid, f"Expected {ip} to be valid IPv4")
                self.assertEqual(res.input_type, InputType.IPV4)
                self.assertIsNone(res.error_message)

    def test_invalid_ipv4(self):
        invalid_ips = ["256.0.0.1", "8.8.8", "1.1.1.1.1", "1.2.3.999"]
        for ip in invalid_ips:
            with self.subTest(ip=ip):
                res = validate_input(ip)
                self.assertFalse(res.is_valid, f"Expected {ip} to be invalid IPv4")
                self.assertNotEqual(res.input_type, InputType.IPV4)
                self.assertIsNotNone(res.error_message)


class TestIPv6Validation(unittest.TestCase):
    """Test IPv6 address validation logic."""

    def test_valid_ipv6(self):
        valid_ips = [
            "2001:4860:4860::8888",
            "::1",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "fe80::1ff:fe23:4567:890a",
        ]
        for ip in valid_ips:
            with self.subTest(ip=ip):
                res = validate_input(ip)
                self.assertTrue(res.is_valid, f"Expected {ip} to be valid IPv6")
                self.assertEqual(res.input_type, InputType.IPV6)
                self.assertIsNone(res.error_message)

    def test_invalid_ipv6(self):
        invalid_ips = ["2001:::1", "xyz::1", "1:2:3:4:5:6:7:8:9"]
        for ip in invalid_ips:
            with self.subTest(ip=ip):
                res = validate_input(ip)
                self.assertFalse(res.is_valid, f"Expected {ip} to be invalid IPv6")
                self.assertNotEqual(res.input_type, InputType.IPV6)
                self.assertIsNotNone(res.error_message)


class TestEdgeCasesAndValidationResult(unittest.TestCase):
    """Test edge cases, empty input, and ValidationResult structure."""

    def test_empty_and_none_input(self):
        res_empty = validate_input("")
        self.assertFalse(res_empty.is_valid)
        self.assertEqual(res_empty.input_type, InputType.UNKNOWN)

        res_space = validate_input("   ")
        self.assertFalse(res_space.is_valid)

        res_none = validate_input(None)
        self.assertFalse(res_none.is_valid)

    def test_result_structure(self):
        raw = "  HTTPS://GOOGLE.COM  "
        res = validate_input(raw)
        self.assertEqual(res.original_input, raw)
        self.assertEqual(res.normalized_input, "google.com")
        self.assertEqual(res.input_type, InputType.DOMAIN)
        self.assertTrue(res.is_valid)
        self.assertIsNone(res.error_message)


if __name__ == "__main__":
    unittest.main()
