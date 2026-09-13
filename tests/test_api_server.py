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


if __name__ == "__main__":
    unittest.main()

