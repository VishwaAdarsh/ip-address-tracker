"""
Multi-Threaded REST API & Static Web Server for IP PULSE Platform.

Serves:
- Stitch Web Frontend SPA from frontend/ directory
- /api/status: System health, components & version info
- /api/analyze: Unified IP Intelligence, Geolocation & Website Risk analysis
- /api/history: SQLite Lookup History query, single deletion, and clear operations
- /api/field-study: Manual-first 50-site research telemetry & optional auto-completion
- /api/analytics: Real-time statistical distributions & metrics calculated from database
- /api/export/csv: CSV data export endpoint

Architecture:
- Built with Python standard library http.server.ThreadingHTTPServer for high concurrency,
  zero external dependency overhead, and guaranteed cross-platform portability.
- Fully supports CORS for decoupled local development.
"""
import csv
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import logging
import mimetypes
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from config.settings import BASE_DIR
from database.db import clear_history, delete_lookup, get_lookup_history
from database.models import LookupRecord
from core.intel_chain import generate_ip_personality_profile
from core.ip_intel import analyze_ip_intelligence
from services.field_test_service import (
    FIELD_TEST_HEADERS,
    add_field_observation,
    export_field_dataset_from_history,
    get_field_project_status,
    run_automatic_completion,
)
from services.risk_analysis_service import perform_full_intelligence_scan
from services.export_service import (
    export_field_study_csv,
    export_field_study_json,
    generate_research_report_markdown,
    generate_research_report_pdf,
    save_export_artifact,
    validate_field_study_dataset,
)

logger = logging.getLogger(__name__)

FRONTEND_DIR = BASE_DIR / "frontend"


class IPPulseRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler dispatching REST API routes and serving static web assets."""

    server_version = "IPPulseHTTP/2.0"

    def _set_cors_headers(self) -> None:
        """Inject CORS headers allowing secure browser API access."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight requests."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self._set_cors_headers()
        self.end_headers()

    def _send_json(self, data: Any, status: int = 200) -> None:
        """Send JSON response with proper headers and UTF-8 encoding."""
        encoded = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error_json(self, message: str, status: int = 400, details: Optional[Any] = None) -> None:
        """Send structured error response."""
        payload = {"success": False, "error": message}
        if details:
            payload["details"] = details
        self._send_json(payload, status=status)

    def do_GET(self) -> None:
        """Route GET requests to API endpoints or static file server."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path.rstrip("/")
        query_params = parse_qs(parsed_url.query)

        # 1. API Routing
        if path == "/api/status":
            self._handle_api_status()
        elif path == "/api/history":
            self._handle_api_history(query_params)
        elif path == "/api/field-study":
            self._handle_api_field_study()
        elif path == "/api/analytics":
            self._handle_api_analytics()
        elif path == "/api/export/csv":
            self._handle_api_export_csv(query_params)
        elif path == "/api/export/json":
            self._handle_api_export_json()
        elif path in ("/api/export/report", "/api/export/markdown"):
            self._handle_api_export_report()
        elif path == "/api/export/pdf":
            self._handle_api_export_pdf()
        elif path == "/api/export/validate":
            self._handle_api_export_validate()
        elif path.startswith("/api/"):
            self._send_error_json(f"Endpoint not found: {path}", status=404)
        else:
            # 2. Static File Serving
            self._serve_static_file(parsed_url.path)

    def do_POST(self) -> None:
        """Route POST requests to API endpoints."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path.rstrip("/")

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            self._send_error_json("Invalid JSON body", status=400)
            return

        if path == "/api/analyze":
            self._handle_api_analyze(payload)
        elif path == "/api/field-study/add":
            self._handle_api_field_study_add(payload)
        elif path == "/api/field-study/complete-remaining":
            self._handle_api_field_study_complete()
        else:
            self._send_error_json(f"Unknown POST endpoint: {path}", status=404)

    def do_DELETE(self) -> None:
        """Route DELETE requests for history management."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path.rstrip("/")

        if path == "/api/history":
            # Clear all history
            cleared = clear_history()
            self._send_json({"success": cleared, "message": "History cleared successfully." if cleared else "Failed to clear history."})
        elif path.startswith("/api/history/"):
            # Delete single record by ID
            try:
                rec_id = int(path.split("/")[-1])
                deleted = delete_lookup(rec_id)
                if deleted:
                    self._send_json({"success": True, "message": f"Record {rec_id} deleted."})
                else:
                    self._send_error_json(f"Record {rec_id} not found or could not be deleted.", status=404)
            except ValueError:
                self._send_error_json("Invalid record ID", status=400)
        else:
            self._send_error_json(f"Unknown DELETE endpoint: {path}", status=404)

    # -------------------------------------------------------------------------
    # API Route Implementations
    # -------------------------------------------------------------------------

    def _handle_api_status(self) -> None:
        """Return operational telemetry and system status."""
        self._send_json({
            "status": "operational",
            "version": "2.0.0",
            "service": "IP PULSE Multi-Layered Intelligence Console",
            "capabilities": {
                "dns_resolution": True,
                "geolocation": True,
                "security_scanner": True,
                "ip_intel": True,
                "risk_engine": True,
                "ai_explainer": True,
                "field_study": True,
            },
        })

    def _handle_api_analyze(self, payload: Dict[str, Any]) -> None:
        """Execute complete multi-layered IP Intelligence and Security scan."""
        target = str(payload.get("target", "")).strip()
        if not target:
            self._send_error_json("Target domain or IP address is required.", status=400)
            return

        try:
            result = perform_full_intelligence_scan(target, save_to_db=True)
            base = result.base_lookup
            sec = result.security
            intel = result.ip_intel
            risk = result.risk
            chain = result.chain
            ip_val = base.selected_ip or target

            response_data = {
                "success": True,
                "target": target,
                "base": {
                    "input": base.input,
                    "normalized_input": base.normalized_input,
                    "input_type": base.input_type,
                    "selected_ip": base.selected_ip,
                    "ip_version": base.ip_version,
                    "ipv4_addresses": base.ipv4_addresses,
                    "ipv6_addresses": base.ipv6_addresses,
                    "country": base.country,
                    "country_code": base.country_code,
                    "region": base.region,
                    "city": base.city,
                    "latitude": base.latitude,
                    "longitude": base.longitude,
                    "timezone": base.timezone,
                    "organization": base.organization,
                    "isp": base.isp,
                    "asn": base.asn,
                    "dns_response_time_ms": base.dns_response_time_ms,
                    "api_response_time_ms": base.api_response_time_ms,
                    "total_response_time_ms": base.total_response_time_ms,
                    "dns_status": base.dns_status,
                    "geolocation_status": base.geolocation_status,
                    "overall_status": base.overall_status.value if hasattr(base.overall_status, "value") else str(base.overall_status),
                    "error_message": base.error_message,
                    "timestamp": base.timestamp,
                },
                "security": {
                    "target_domain": getattr(sec, "target", getattr(sec, "domain", target)),
                    "is_https": getattr(sec, "https_enabled", False),
                    "tls_valid": getattr(sec, "ssl_valid", getattr(sec, "certificate_valid", False)),
                    "tls_version": getattr(sec, "tls_version", "N/A"),
                    "cipher_name": getattr(sec, "cipher_suite", "N/A"),
                    "expires_in_days": getattr(sec, "ssl_expiry_days", getattr(sec, "certificate_days_remaining", 0)),
                    "issuer_org": getattr(sec, "ssl_issuer", getattr(sec, "certificate_issuer", "Unknown")),
                    "subject_alt_names": [],
                    "hsts_header": sec.security_headers.get("hsts", False) if hasattr(sec, "security_headers") and isinstance(sec.security_headers, dict) else False,
                    "csp_header": sec.security_headers.get("csp", False) if hasattr(sec, "security_headers") and isinstance(sec.security_headers, dict) else False,
                    "x_frame_options": sec.security_headers.get("x_frame_options", False) if hasattr(sec, "security_headers") and isinstance(sec.security_headers, dict) else False,
                    "redirect_count": getattr(sec, "redirect_count", 0),
                    "final_url": getattr(sec, "final_url", "N/A"),
                    "response_status_code": 200,
                },
                "ip_intel": {
                    "ip_address": getattr(intel, "ip_address", ip_val),
                    "asn": getattr(intel, "asn", "Unknown"),
                    "organization": getattr(intel, "organization", "Unknown"),
                    "isp": getattr(intel, "isp", "Unknown"),
                    "infrastructure_type": getattr(intel, "infrastructure_type", "Unknown"),
                    "vpn_status": getattr(intel, "vpn_status", "DETECTED" if getattr(intel, "is_vpn", False) else "NOT_DETECTED"),
                    "proxy_status": getattr(intel, "proxy_status", "DETECTED" if getattr(intel, "is_proxy", False) else "NOT_DETECTED"),
                    "tor_status": getattr(intel, "tor_status", "DETECTED" if getattr(intel, "is_tor", False) else "NOT_DETECTED"),
                    "datacenter_status": getattr(intel, "datacenter_status", "DETECTED" if getattr(intel, "is_datacenter", False) else "NOT_DETECTED"),
                },
                "risk": {
                    "trust_score": risk.trust_score,
                    "risk_score": risk.risk_score,
                    "risk_category": getattr(risk, "risk_category", getattr(risk, "risk_level", "Low")),
                    "risk_level": getattr(risk, "risk_level", "Low"),
                    "confidence_rating": getattr(risk, "confidence_rating", f"{int(getattr(risk, 'confidence_score', 1.0) * 100)}%"),
                    "confidence_score": getattr(risk, "confidence_score", 1.0),
                    "risk_factors": risk.risk_factors,
                    "positive_factors": risk.positive_factors,
                    "trust": risk.trust.to_dict() if getattr(risk, "trust", None) else None,
                    "ip_risk": risk.ip_risk.to_dict() if getattr(risk, "ip_risk", None) else None,
                    "disclaimer": getattr(risk, "disclaimer", "IP PULSE analytical assessment based on available technical signals."),
                },
                "personality": getattr(chain, "ip_personality", getattr(chain, "personality_summary", "IP personality statement")),
                "ip_personality": chain.personality.to_dict() if getattr(chain, "personality", None) else {
                    "labels": ["INFRASTRUCTURE UNCLASSIFIED"],
                    "summary": getattr(chain, "ip_personality", "IP personality statement"),
                    "confidence": "UNKNOWN",
                    "disclaimer": getattr(chain, "disclaimer", ""),
                },
                "intelligence_chain": chain.to_dict() if hasattr(chain, "to_dict") else {
                    "domain": getattr(chain, "domain_or_input", target),
                    "ip": getattr(chain, "resolved_ip", ip_val),
                    "asn": getattr(chain, "asn", "Unknown"),
                    "organization": getattr(chain, "organization", "Unknown"),
                    "infrastructure": getattr(chain, "infrastructure_type", "Unknown"),
                    "location": f"{getattr(chain, 'city', '')}, {getattr(chain, 'country', '')}".strip(", ") or "Unknown Location",
                    "nodes": getattr(chain, "nodes", []),
                },
                "explanation": result.explanation,
                "provenance": [
                    {"stage": "DNS Resolution", "source": "Core Resolver", "status": base.dns_status, "details": f"Resolved {base.selected_ip}"},
                    {"stage": "Geolocation", "source": "Multi-Provider Geo", "status": base.geolocation_status, "details": f"{base.city}, {base.country}"},
                    {"stage": "Security Probe", "source": "Website Scanner", "status": "AUDITED", "details": f"HTTPS: {getattr(sec, 'https_enabled', False)}"},
                    {"stage": "IP Intelligence", "source": "Infrastructure Engine", "status": "CLASSIFIED", "details": f"Class: {getattr(intel, 'infrastructure_type', 'Unknown')}"},
                ],
            }
            self._send_json(response_data)
        except Exception as e:
            logger.exception(f"Error analyzing target {target}: {e}")
            self._send_error_json(f"Analysis engine error: {str(e)}", status=500)

    def _handle_api_history(self, query_params: Dict[str, List[str]]) -> None:
        """Retrieve stored lookup records from SQLite database."""
        limit_param = query_params.get("limit", [None])[0]
        offset_param = query_params.get("offset", ["0"])[0]

        limit = int(limit_param) if limit_param and limit_param.isdigit() else None
        offset = int(offset_param) if offset_param and offset_param.isdigit() else 0

        try:
            records: List[LookupRecord] = get_lookup_history(limit=limit, offset=offset)
            serialized = []
            for r in records:
                # Format friendly date
                ts_str = r.timestamp or ""
                serialized.append({
                    "id": r.id,
                    "timestamp": ts_str,
                    "input_value": r.input_value,
                    "input_type": r.input_type,
                    "domain": r.domain,
                    "ip_address": r.ip_address,
                    "ip_version": r.ip_version,
                    "country": r.country,
                    "country_code": r.country_code,
                    "region": r.region,
                    "city": r.city,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "timezone": r.timezone,
                    "organization": r.organization,
                    "isp": r.isp,
                    "asn": r.asn,
                    "dns_response_time_ms": r.dns_response_time_ms,
                    "api_response_time_ms": r.api_response_time_ms,
                    "status": r.status,
                    "error_message": r.error_message,
                })
            self._send_json({
                "success": True,
                "total_count": len(serialized),
                "records": serialized,
            })
        except Exception as e:
            logger.exception(f"Error fetching history: {e}")
            self._send_error_json(f"Database error: {str(e)}", status=500)

    def _handle_api_field_study(self) -> None:
        """Evaluate manual-first 50-website field study status."""
        try:
            status = get_field_project_status(target_count=50)
            avail = status["available_count"]
            target = status["target"]
            rem = status["remaining"]
            pct = status["progress_percentage"]

            self._send_json({
                "success": True,
                "available_count": avail,
                "target": target,
                "remaining": rem,
                "progress_percentage": pct,
                "protocol": "Manual-First Protocol Active",
                "status": status["status"],
                "summary": status["summary"],
                "records": status["records"],
            })
        except Exception as e:
            logger.exception(f"Error retrieving field study status: {e}")
            self._send_error_json(f"Field study error: {str(e)}", status=500)

    def _handle_api_field_study_add(self, payload: Dict[str, Any]) -> None:
        """Add an intentionally curated website observation to the 50-site field study."""
        target = str(payload.get("target") or payload.get("domain") or "").strip()
        category = payload.get("category")
        if not target:
            self._send_error_json("Target domain is required.", status=400)
            return

        try:
            success, msg, obs = add_field_observation(target=target, category=category)
            if not success:
                if "already recorded" in msg.lower():
                    self._send_json({
                        "success": False,
                        "duplicate": True,
                        "message": msg,
                        "observation": obs.to_dict() if obs else None,
                    }, status=409)
                else:
                    self._send_json({
                        "success": False,
                        "error": msg,
                        "message": msg,
                    }, status=400)
                return

            st = get_field_project_status(target_count=50)
            self._send_json({
                "success": True,
                "message": msg,
                "observation": obs.to_dict() if obs else None,
                "available_count": st["available_count"],
                "target": st["target"],
                "remaining": st["remaining"],
                "progress_percentage": st["progress_percentage"],
                "status": st["status"],
                "summary": st["summary"],
            })
        except Exception as e:
            logger.exception(f"Error adding observation to field study: {e}")
            self._send_error_json(f"Error adding observation: {str(e)}", status=500)

    def _handle_api_field_study_complete(self) -> None:
        """Asynchronously execute automated completion for remaining observations."""
        try:
            def bg_runner():
                try:
                    run_automatic_completion(target_count=50)
                except Exception as ex:
                    logger.error(f"Background field completion failed: {ex}")

            thread = threading.Thread(target=bg_runner, daemon=True)
            thread.start()

            self._send_json({
                "success": True,
                "message": "Field study completion started in background.",
            })
        except Exception as e:
            self._send_error_json(f"Could not initiate completion: {str(e)}", status=500)

    def _handle_api_analytics(self) -> None:
        """Compute statistical distributions and metrics directly from real database observations."""
        try:
            from services.analytics_service import compute_field_study_analytics
            analytics_data = compute_field_study_analytics()

            # Merge top-level aliases for backward compatibility with existing tests/clients
            ov = analytics_data.get("overview", {})
            na = analytics_data.get("network_analysis", {})
            ta = analytics_data.get("trust_analysis", {})

            response_payload = {
                **analytics_data,
                "total_observations": ov.get("total_observations", 0),
                "mean_dns_time_ms": na.get("mean_dns_latency_ms", 0.0),
                "mean_api_time_ms": na.get("mean_api_latency_ms", 0.0),
                "ipv4_count": na.get("ipv4_count", 0),
                "ipv6_count": na.get("ipv6_count", 0),
                "top_countries": na.get("top_countries", []),
                "top_organizations": na.get("top_organizations", []),
                "trust_brackets": ta.get("distribution", []),
            }

            self._send_json(response_payload)
        except Exception as e:
            logger.exception(f"Error compiling analytics: {e}")
            self._send_error_json(f"Analytics engine error: {str(e)}", status=500)

    def _handle_api_export_csv(self, query_params: Dict[str, List[str]]) -> None:
        """Export history or field study dataset as CSV."""
        export_type = query_params.get("type", ["history"])[0]

        if export_type == "field-study":
            csv_str = export_field_study_csv()
            save_export_artifact("IP_PULSE_Field_Study.csv", csv_str)
            filename = "IP_PULSE_Field_Study.csv"
            csv_data = csv_str.encode("utf-8")
        else:
            output = io.StringIO()
            records = get_lookup_history()
            writer = csv.writer(output)
            writer.writerow(["ID", "Timestamp", "Input", "Domain", "IP Address", "Version", "Country", "City", "Lat", "Lon", "Org", "ISP", "ASN", "DNS (ms)", "API (ms)", "Status"])
            for r in records:
                writer.writerow([r.id, r.timestamp, r.input_value, r.domain, r.ip_address, r.ip_version, r.country, r.city, r.latitude, r.longitude, r.organization, r.isp, r.asn, r.dns_response_time_ms, r.api_response_time_ms, r.status])
            filename = "ip_pulse_history.csv"
            csv_data = output.getvalue().encode("utf-8")

        self.send_response(200)
        self._set_cors_headers()
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(csv_data)))
        self.end_headers()
        self.wfile.write(csv_data)

    def _handle_api_export_json(self) -> None:
        """Export structured research dataset as JSON."""
        try:
            payload = export_field_study_json(target_count=50)
            json_str = json.dumps(payload, indent=2)
            save_export_artifact("IP_PULSE_Field_Study.json", json_str)
            raw_bytes = json_str.encode("utf-8")

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="IP_PULSE_Field_Study.json"')
            self.send_header("Content-Length", str(len(raw_bytes)))
            self.end_headers()
            self.wfile.write(raw_bytes)
        except Exception as e:
            logger.exception(f"Error exporting JSON dataset: {e}")
            self._send_error_json(f"JSON export error: {str(e)}", status=500)

    def _handle_api_export_report(self) -> None:
        """Export comprehensive academic research report as Markdown."""
        try:
            report_str = generate_research_report_markdown(target_count=50)
            save_export_artifact("IP_PULSE_Research_Report.md", report_str)
            raw_bytes = report_str.encode("utf-8")

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="IP_PULSE_Research_Report.md"')
            self.send_header("Content-Length", str(len(raw_bytes)))
            self.end_headers()
            self.wfile.write(raw_bytes)
        except Exception as e:
            logger.exception(f"Error generating Markdown report: {e}")
            self._send_error_json(f"Markdown report error: {str(e)}", status=500)

    def _handle_api_export_pdf(self) -> None:
        """Export publication-grade research report as PDF."""
        try:
            pdf_bytes = generate_research_report_pdf(target_count=50)
            save_export_artifact("IP_PULSE_Research_Report.pdf", pdf_bytes)

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", 'attachment; filename="IP_PULSE_Research_Report.pdf"')
            self.send_header("Content-Length", str(len(pdf_bytes)))
            self.end_headers()
            self.wfile.write(pdf_bytes)
        except Exception as e:
            logger.exception(f"Error generating PDF report: {e}")
            self._send_error_json(f"PDF export error: {str(e)}", status=500)

    def _handle_api_export_validate(self) -> None:
        """Run and return dataset quality audit results."""
        try:
            audit_result = validate_field_study_dataset()
            self._send_json(audit_result)
        except Exception as e:
            logger.exception(f"Error validating field study dataset: {e}")
            self._send_error_json(f"Dataset validation error: {str(e)}", status=500)

    # -------------------------------------------------------------------------
    # Static File Delivery
    # -------------------------------------------------------------------------

    def _serve_static_file(self, raw_path: str) -> None:
        """Serve files from frontend/ directory with path traversal protection."""
        clean_path = raw_path.split("?")[0].lstrip("/")
        if not clean_path or clean_path == "":
            clean_path = "index.html"

        target_file = (FRONTEND_DIR / clean_path).resolve()

        # Prevent directory traversal attacks
        try:
            target_file.relative_to(FRONTEND_DIR.resolve())
        except ValueError:
            self._send_error_json("Access denied", status=403)
            return

        if not target_file.exists() or not target_file.is_file():
            # If requesting an SPA route, fallback to index.html
            fallback = FRONTEND_DIR / "index.html"
            if fallback.exists():
                target_file = fallback
            else:
                self._send_error_json("Resource not found", status=404)
                return

        mime_type, _ = mimetypes.guess_type(str(target_file))
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            content = target_file.read_bytes()
            self.send_response(HTTPStatus.OK)
            self._set_cors_headers()
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if mime_type.startswith("text/") or mime_type in ["application/javascript", "application/json"] else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            logger.error(f"Error serving file {target_file}: {e}")
            self._send_error_json("Error reading file", status=500)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress noisy request logging unless debugging."""
        logger.debug("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """Create and return configured ThreadingHTTPServer instance."""
    server_address = (host, port)
    return ThreadingHTTPServer(server_address, IPPulseRequestHandler)


def run_api_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start blocking HTTP server on specified host and port."""
    server = create_server(host, port)
    logger.info(f"IP PULSE HTTP & REST API server running at http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down IP PULSE API server...")
    finally:
        server.server_close()
