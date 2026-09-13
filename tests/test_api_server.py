"""
Automated Integration Tests for IP PULSE REST API Server.

Validates:
- Static file serving (HTML, CSS, JS)
- CORS headers on all endpoints
- /api/status endpoint
- /api/analyze endpoint (input validation, error handling, structured payload)
- /api/history endpoint
- /api/field-study endpoint
- /api/analytics endpoint
- /api/export/csv endpoint
- OPTIONS preflight request handling
"""
import json
import threading
import time
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from api.server import create_server


class TestAPIServer(unittest.TestCase):
    """Integration test suite for IP PULSE ThreadingHTTPServer."""

    @classmethod
    def setUpClass(cls):
        """Start test server on localhost on a dedicated test port."""
        cls.port = 8765
        cls.server = create_server(host="127.0.0.1", port=cls.port)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.3)  # Brief pause for server initialization

    @classmethod
    def tearDownClass(cls):
        """Shutdown test server."""
        cls.server.shutdown()
        cls.server.server_close()

    def _url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def test_01_static_index_html(self):
        """Verify root GET serves the Stitch web interface."""
        req = Request(self._url("/"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            content_type = resp.headers.get("Content-Type", "")
            self.assertIn("text/html", content_type)
            body = resp.read().decode("utf-8")
            self.assertIn("IP PULSE", body)
            self.assertIn("Analyze a Website or IP", body)

    def test_02_static_css_assets(self):
        """Verify static CSS delivery with proper MIME type."""
        req = Request(self._url("/assets/style.css"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/css", resp.headers.get("Content-Type", ""))

    def test_03_cors_preflight(self):
        """Verify OPTIONS request returns CORS headers with 204 status."""
        req = Request(self._url("/api/analyze"), method="OPTIONS")
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 204)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")
            self.assertIn("POST", resp.headers.get("Access-Control-Allow-Methods", ""))

    def test_04_api_status(self):
        """Verify /api/status returns operational status."""
        req = Request(self._url("/api/status"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "operational")
            self.assertEqual(data.get("version"), "2.0.0")
            self.assertTrue(data.get("capabilities", {}).get("dns_resolution"))

    def test_05_api_analyze_empty_payload(self):
        """Verify /api/analyze rejects empty target with 400 Bad Request."""
        payload = json.dumps({"target": ""}).encode("utf-8")
        req = Request(self._url("/api/analyze"), data=payload, headers={"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req)
        self.assertEqual(ctx.exception.code, 400)
        data = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertFalse(data.get("success"))

    def test_06_api_analyze_ip(self):
        """Verify /api/analyze with IP address returns structured multi-layered intelligence."""
        payload = json.dumps({"target": "1.1.1.1"}).encode("utf-8")
        req = Request(self._url("/api/analyze"), data=payload, headers={"Content-Type": "application/json"})
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("base", data)
            self.assertIn("security", data)
            self.assertIn("ip_intel", data)
            self.assertIn("risk", data)
            self.assertIn("personality", data)
            self.assertIn("explanation", data)

            # Check base fields
            base = data["base"]
            self.assertEqual(base["selected_ip"], "1.1.1.1")
            self.assertIn(base["overall_status"], ["SUCCESS", "GEO_FAILED"])

            # Check risk engine
            risk = data["risk"]
            self.assertIn("trust_score", risk)
            self.assertIn("risk_score", risk)
            self.assertIn("risk_category", risk)

    def test_07_api_history(self):
        """Verify /api/history returns SQLite records list."""
        req = Request(self._url("/api/history"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIsInstance(data.get("records"), list)

    def test_08_api_field_study(self):
        """Verify /api/field-study returns manual-first protocol status."""
        req = Request(self._url("/api/field-study"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("target"), 50)
            self.assertIn("available_count", data)
            self.assertIn("remaining", data)
            self.assertIn("records", data)

    def test_09_api_analytics(self):
        """Verify /api/analytics returns statistical calculations."""
        req = Request(self._url("/api/analytics"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            if not data.get("insufficient_data"):
                self.assertIn("total_observations", data)
                self.assertIn("trust_brackets", data)
                self.assertEqual(len(data["trust_brackets"]), 5)

    def test_10_api_export_csv(self):
        """Verify CSV export for history and field study."""
        req = Request(self._url("/api/export/csv?type=history"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/csv", resp.headers.get("Content-Type", ""))
            csv_content = resp.read().decode("utf-8")
            self.assertIn("Domain", csv_content)

        req_fs = Request(self._url("/api/export/csv?type=field-study"))
        with urlopen(req_fs) as resp_fs:
            self.assertEqual(resp_fs.status, 200)
            self.assertIn("text/csv", resp_fs.headers.get("Content-Type", ""))
            csv_fs = resp_fs.read().decode("utf-8")
            self.assertIn("Domain", csv_fs)

    def test_11_api_export_json(self):
        """Verify JSON export endpoint returns structured dataset."""
        req = Request(self._url("/api/export/json"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("application/json", resp.headers.get("Content-Type", ""))
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("target_observations"), 50)
            self.assertIn("observations", data)
            self.assertIn("analytics", data)
            self.assertIn("validation_summary", data)

    def test_12_api_export_report(self):
        """Verify Markdown research report export endpoint."""
        req = Request(self._url("/api/export/report"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/markdown", resp.headers.get("Content-Type", ""))
            report_text = resp.read().decode("utf-8")
            self.assertIn("1. Executive Summary", report_text)
            self.assertIn("12. Dataset Status & Integrity Attestation", report_text)

    def test_13_api_export_pdf(self):
        """Verify PDF export endpoint returns valid binary PDF."""
        req = Request(self._url("/api/export/pdf"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("application/pdf", resp.headers.get("Content-Type", ""))
            pdf_bytes = resp.read()
            self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
            self.assertGreater(len(pdf_bytes), 1000)

    def test_14_api_export_validate(self):
        """Verify data validation endpoint returns audit summary."""
        req = Request(self._url("/api/export/validate"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("is_valid", data)
            self.assertIn("issues_count", data)
            self.assertIn("warnings", data)

    def test_15_api_explain_status(self):
        """Verify Explainable AI status endpoint returns operational metadata."""
        req = Request(self._url("/api/explain/status"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("status", data)
            self.assertIn("provider", data)
            self.assertIn("model", data)

    def test_16_api_explain_post_valid_payload(self):
        """Verify POST /api/explain returns structured evidence explanation."""
        payload = {
            "target": "example.com",
            "intelligence": {
                "base": {"selected_ip": "93.184.216.34", "country": "United States", "asn": "AS15133"},
                "security": {"is_https": True, "tls_valid": True},
                "ip_intel": {"infrastructure_type": "CDN / Edge Hub"},
                "risk": {"trust_score": 90, "risk_score": 10, "positive_factors": ["HTTPS active"]},
            },
        }
        body = json.dumps(payload).encode("utf-8")
        req = Request(self._url("/api/explain"), data=body, headers={"Content-Type": "application/json"})
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "success")
            self.assertIn("summary", data)
            self.assertIn("trust_explanation", data)
            self.assertIn("risk_explanation", data)
            self.assertIn("recommendation", data)
            self.assertIn("limitations", data)

    def test_17_api_explain_empty_payload(self):
        """Verify POST /api/explain rejects empty target with 400 error."""
        body = json.dumps({}).encode("utf-8")
        req = Request(self._url("/api/explain"), data=body, headers={"Content-Type": "application/json"})
        try:
            urlopen(req)
            self.fail("Expected HTTP 400 error for empty target")
        except HTTPError as e:
            self.assertEqual(e.code, 400)

    def test_18_api_compare_candidates(self):
        """Verify GET /api/compare/candidates returns available candidate observations."""
        req = Request(self._url("/api/compare/candidates"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("count", data)
            self.assertIn("candidates", data)
            self.assertIsInstance(data["candidates"], list)

    def test_19_api_compare_valid_payload(self):
        """Verify POST /api/compare performs multi-target comparison across 2 observations."""
        payload = {
            "observations": [
                {
                    "domain": "alpha.test.com",
                    "resolved_ip": "1.1.1.1",
                    "asn": "AS13335",
                    "organization": "Cloudflare",
                    "country": "United States",
                    "infrastructure_type": "Cloud / Hosting",
                    "https_status": "Enabled",
                    "website_trust_score": 90.0,
                    "ip_risk_score": 10.0,
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                },
                {
                    "domain": "beta.test.com",
                    "resolved_ip": "8.8.8.8",
                    "asn": "AS15169",
                    "organization": "Google",
                    "country": "United States",
                    "infrastructure_type": "Cloud / Hosting",
                    "https_status": "Enabled",
                    "website_trust_score": 85.0,
                    "ip_risk_score": 15.0,
                    "latitude": 37.4220,
                    "longitude": -122.0841,
                },
            ]
        }
        body = json.dumps(payload).encode("utf-8")
        req = Request(self._url("/api/compare"), data=body, headers={"Content-Type": "application/json"})
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("count"), 2)
            self.assertIn("statistics", data)
            self.assertIn("differences", data)
            self.assertIn("map_points", data)
            self.assertEqual(len(data["map_points"]), 2)

    def test_20_api_compare_insufficient_payload(self):
        """Verify POST /api/compare rejects fewer than 2 observations with 400."""
        payload = {"observations": [{"domain": "single.com"}]}
        body = json.dumps(payload).encode("utf-8")
        req = Request(self._url("/api/compare"), data=body, headers={"Content-Type": "application/json"})
        try:
            urlopen(req)
            self.fail("Expected HTTP 400 error for insufficient observations")
        except HTTPError as e:
            self.assertEqual(e.code, 400)

    def test_21_api_compare_explain(self):
        """Verify POST /api/compare/explain produces comparative synthesis."""
        payload = {
            "comparison": {
                "observations": [
                    {"domain": "one.com", "resolved_ip": "1.1.1.1", "asn": "AS1", "country": "US", "website_trust_score": 90, "ip_risk_score": 10},
                    {"domain": "two.com", "resolved_ip": "2.2.2.2", "asn": "AS2", "country": "DE", "website_trust_score": 40, "ip_risk_score": 70},
                ],
                "statistics": {
                    "common_asn": "No common value detected.",
                    "common_country": "No common value detected.",
                    "https_adoption": {"formatted": "1 of 2 (50.0%) enforced"},
                    "anonymizer_detections": {"total_anonymizers": 0},
                },
                "differences": ["Geographic divergence observed."],
            }
        }
        body = json.dumps(payload).encode("utf-8")
        req = Request(self._url("/api/compare/explain"), data=body, headers={"Content-Type": "application/json"})
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "success")
            self.assertIn("summary", data)
            self.assertIn("infrastructure_comparison", data)
            self.assertIn("security_comparison", data)

    def test_22_api_compare_export_csv_and_json(self):
        """Verify POST /api/compare/export delivers CSV and JSON export streams."""
        payload = {
            "observations": [
                {"domain": "siteA.com", "resolved_ip": "1.1.1.1", "country": "US", "website_trust_score": 88},
                {"domain": "siteB.com", "resolved_ip": "2.2.2.2", "country": "CA", "website_trust_score": 92},
            ],
            "format": "csv",
        }
        body = json.dumps(payload).encode("utf-8")
        req = Request(self._url("/api/compare/export"), data=body, headers={"Content-Type": "application/json"})
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/csv", resp.headers.get("Content-Type", ""))
            csv_text = resp.read().decode("utf-8")
            self.assertIn("siteA.com", csv_text)

        payload["format"] = "json"
        body_json = json.dumps(payload).encode("utf-8")
        req_json = Request(self._url("/api/compare/export"), data=body_json, headers={"Content-Type": "application/json"})
        with urlopen(req_json) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("application/json", resp.headers.get("Content-Type", ""))
            json_text = resp.read().decode("utf-8")
            self.assertIn("siteB.com", json_text)

    def test_23_api_analytics_filtering_query_params(self):
        """Verify GET /api/analytics handles query parameter filters."""
        req = Request(self._url("/api/analytics?country=United%20States&range=recent_10"))
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("is_filtered", data)
            self.assertIn("unfiltered_total_count", data)
            self.assertIn("filtered_count", data)
            self.assertIn("available_filter_options", data)
            self.assertIn("map_points", data)
            self.assertIn("mapped_points_count", data)
            self.assertIn("missing_coordinates_count", data)

    def test_24_api_analytics_post_and_capabilities(self):
        """Verify POST /api/analytics with body filters and status capability."""
        # 1. POST /api/analytics
        payload = {"filters": {"infrastructure": "Cloud", "https_status": "Enabled"}}
        body = json.dumps(payload).encode("utf-8")
        req = Request(self._url("/api/analytics"), data=body, headers={"Content-Type": "application/json"})
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("is_filtered", data)
            self.assertIn("map_points", data)

        # 2. Status capability
        req_status = Request(self._url("/api/status"))
        with urlopen(req_status) as resp_status:
            self.assertEqual(resp_status.status, 200)
            status_data = json.loads(resp_status.read().decode("utf-8"))
            caps = status_data.get("capabilities", {})
            self.assertTrue(caps.get("visualization_dashboard"))


if __name__ == "__main__":
    unittest.main()




