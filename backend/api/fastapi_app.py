"""
FastAPI Application for IP PULSE Platform.
Provides ASGI production entrypoint for Uvicorn deployment on Render and cloud platforms.
Maintains 100% route, schema, and behavior parity with IPPulseRequestHandler.
"""
import csv
import datetime
import io
import json
import logging
import mimetypes
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config.settings import (
    AI_ENABLED,
    AI_MODEL,
    AI_PROVIDER,
    BASE_DIR,
)
from backend.intelligence.ai_explainer import explain_intelligence
from backend.database.db import clear_history, delete_lookup, get_lookup_history, init_db
from backend.models.models import FieldObservation, LookupRecord
from backend.services.field_test_service import (
    add_field_observation,
    get_field_project_status,
    run_automatic_completion,
)
from backend.services.risk_analysis_service import perform_full_intelligence_scan
from backend.services.comparison_service import (
    execute_comparison,
    generate_comparison_ai_explanation,
    get_comparison_candidates,
)
from backend.reports.export_service import (
    export_field_study_csv,
    export_field_study_json,
    generate_research_report_markdown,
    generate_research_report_pdf,
    save_export_artifact,
    validate_field_study_dataset,
)

logger = logging.getLogger(__name__)
FRONTEND_DIR = BASE_DIR / "frontend"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject standard security hardening HTTP headers."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


def create_fastapi_app() -> FastAPI:
    """Create and configure the FastAPI application with full route coverage."""
    # Ensure database schema is initialized on startup
    init_db()

    app = FastAPI(
        title="IP PULSE - IP Intelligence, Geolocation & Website Risk Analysis Platform",
        description="Unified multi-layered cyber telemetry, IP geolocation, website security intelligence, and empirical research platform.",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 1. Security & CORS Middlewares
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=86400,
    )

    # -------------------------------------------------------------------------
    # REST API Routes
    # -------------------------------------------------------------------------

    @app.get("/api/status")
    def get_api_status() -> Dict[str, Any]:
        """Return operational telemetry and system status."""
        return {
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
                "explainable_ai_layer": True,
                "comparison_workspace": True,
                "visualization_dashboard": True,
            },
        }

    @app.get("/api/history")
    def get_history(
        limit: Optional[int] = Query(None, description="Max records to return"),
        offset: int = Query(0, description="Record offset"),
    ) -> Dict[str, Any]:
        """Retrieve stored lookup records from SQLite database."""
        records: List[LookupRecord] = get_lookup_history(limit=limit, offset=offset)
        serialized = []
        for r in records:
            serialized.append({
                "id": r.id,
                "timestamp": r.timestamp or "",
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
        return {"success": True, "count": len(serialized), "records": serialized}

    @app.delete("/api/history")
    def delete_all_history() -> Dict[str, Any]:
        """Clear all historical lookup records."""
        cleared = clear_history()
        return {
            "success": cleared,
            "message": "History cleared successfully." if cleared else "Failed to clear history.",
        }

    @app.delete("/api/history/{rec_id}")
    def delete_single_history(rec_id: int) -> Dict[str, Any]:
        """Delete single lookup record by ID."""
        deleted = delete_lookup(rec_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Record {rec_id} not found or could not be deleted.")
        return {"success": True, "message": f"Record {rec_id} deleted."}

    @app.get("/api/field-study")
    def get_field_study() -> Dict[str, Any]:
        """Return 50-site field study status, metrics, and recorded observations."""
        status = get_field_project_status(target_count=50)
        return {
            "success": True,
            "status": status["status"],
            "target": status["target"],
            "available_count": status["available_count"],
            "remaining": status["remaining"],
            "progress_percentage": status["progress_percentage"],
            "summary": status["summary"],
            "records": status["records"],
        }

    @app.post("/api/field-study/add")
    def add_field_study_observation(payload: Dict[str, Any] = Body(...)) -> Response:
        """Add an intentionally curated website observation to the 50-site field study."""
        target = str(payload.get("target") or payload.get("domain") or "").strip()
        category = payload.get("category")
        searched_by = str(payload.get("searched_by") or payload.get("investigator") or "Anonymous").strip() or "Anonymous"
        if not target:
            raise HTTPException(status_code=400, detail="Target domain is required.")

        success, msg, obs = add_field_observation(
            target=target,
            category=category,
            searched_by=searched_by,
            update_if_exists=True,
        )
        if not success:
            if "already recorded" in msg.lower():
                return JSONResponse(
                    status_code=409,
                    content={
                        "success": False,
                        "duplicate": True,
                        "message": msg,
                        "observation": obs.to_dict() if obs else None,
                    },
                )
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": msg, "message": msg},
            )

        st = get_field_project_status(target_count=50)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": msg,
                "observation": obs.to_dict() if obs else None,
                "available_count": st["available_count"],
                "target": st["target"],
                "remaining": st["remaining"],
                "progress_percentage": st["progress_percentage"],
                "status": st["status"],
                "summary": st["summary"],
            },
        )

    @app.post("/api/field-study/complete-remaining")
    def complete_field_study_remaining() -> Dict[str, Any]:
        """Asynchronously execute automated completion for remaining observations."""
        def bg_runner():
            try:
                run_automatic_completion(target_count=50)
            except Exception as ex:
                logger.error(f"Background field completion failed: {ex}")

        thread = threading.Thread(target=bg_runner, daemon=True)
        thread.start()
        return {"success": True, "message": "Field study completion started in background."}

    def _compile_analytics_response(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from backend.analytics.analytics_service import compute_field_study_analytics
        analytics_data = compute_field_study_analytics(filters=filters if filters else None)
        ov = analytics_data.get("overview", {})
        na = analytics_data.get("network_analysis", {})
        ta = analytics_data.get("trust_analysis", {})
        return {
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

    @app.get("/api/analytics")
    def get_analytics(request: Request) -> Dict[str, Any]:
        """Compute statistical distributions directly from real observations with optional query filters."""
        query_params = dict(request.query_params)
        filters = {k: v for k, v in query_params.items() if v}
        return _compile_analytics_response(filters=filters if filters else None)

    @app.post("/api/analytics")
    def post_analytics(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
        """Compute statistical distributions directly from real observations with JSON filter payload."""
        return _compile_analytics_response(filters=payload if payload else None)

    @app.get("/api/export/csv")
    def get_export_csv(type: str = Query("history")) -> Response:
        """Export history or field study dataset as CSV."""
        if type == "field-study":
            csv_str = export_field_study_csv()
            save_export_artifact("IP_PULSE_Field_Study.csv", csv_str)
            filename = "IP_PULSE_Field_Study.csv"
            csv_bytes = csv_str.encode("utf-8")
        else:
            output = io.StringIO()
            records = get_lookup_history()
            writer = csv.writer(output)
            writer.writerow(["ID", "Timestamp", "Input", "Domain", "IP Address", "Version", "Country", "City", "Lat", "Lon", "Org", "ISP", "ASN", "DNS (ms)", "API (ms)", "Status"])
            for r in records:
                writer.writerow([r.id, r.timestamp, r.input_value, r.domain, r.ip_address, r.ip_version, r.country, r.city, r.latitude, r.longitude, r.organization, r.isp, r.asn, r.dns_response_time_ms, r.api_response_time_ms, r.status])
            filename = "ip_pulse_history.csv"
            csv_bytes = output.getvalue().encode("utf-8")

        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/api/export/json")
    def get_export_json() -> Response:
        """Export structured research dataset as JSON."""
        payload = export_field_study_json(target_count=50)
        json_str = json.dumps(payload, indent=2)
        save_export_artifact("IP_PULSE_Field_Study.json", json_str)
        return Response(
            content=json_str.encode("utf-8"),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="IP_PULSE_Field_Study.json"'},
        )

    @app.get("/api/export/report")
    @app.get("/api/export/markdown")
    def get_export_report() -> Response:
        """Export comprehensive academic research report as Markdown."""
        report_str = generate_research_report_markdown(target_count=50)
        save_export_artifact("IP_PULSE_Research_Report.md", report_str)
        return Response(
            content=report_str.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="IP_PULSE_Research_Report.md"'},
        )

    @app.get("/api/export/pdf")
    def get_export_pdf() -> Response:
        """Export publication-grade research report as PDF."""
        pdf_bytes = generate_research_report_pdf(target_count=50)
        save_export_artifact("IP_PULSE_Research_Report.pdf", pdf_bytes)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="IP_PULSE_Research_Report.pdf"'},
        )

    @app.get("/api/export/validate")
    def get_export_validate() -> Dict[str, Any]:
        """Run and return dataset quality audit results."""
        return validate_field_study_dataset()

    @app.get("/api/explain/status")
    def get_explain_status() -> Dict[str, Any]:
        """Return operational status and metadata for Explainable AI layer."""
        return {
            "status": "operational" if AI_ENABLED else "disabled",
            "enabled": AI_ENABLED,
            "provider": AI_PROVIDER,
            "model": AI_MODEL,
            "description": "Evidence-grounded explainability engine for Website Trust and IP Risk.",
        }

    @app.post("/api/explain")
    def post_explain(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        """Generate an evidence-grounded AI explanation for an analyzed target."""
        target = str(payload.get("target", "")).strip()
        if not target:
            raise HTTPException(status_code=400, detail="Target domain or IP address is required.")

        intelligence = payload.get("intelligence")
        if not intelligence:
            try:
                intelligence = perform_full_intelligence_scan(target, save_to_db=False)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to scan target for explanation: {str(e)}")

        bypass_cache = bool(payload.get("bypass_cache", False))
        provider_override = payload.get("provider")
        res = explain_intelligence(
            target=target,
            intelligence=intelligence,
            provider_name=provider_override,
            bypass_cache=bypass_cache,
        )
        return res.to_dict()

    @app.get("/api/compare/candidates")
    def get_comparison_candidates_endpoint() -> Dict[str, Any]:
        """Return candidate observations from Field Study & History for investigation workspace."""
        return get_comparison_candidates()

    @app.post("/api/compare")
    def post_compare(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        """Execute multi-observation comparison across 2 to 5 targets."""
        raw_items = payload.get("observations")
        if raw_items is None:
            raise HTTPException(status_code=400, detail="Observations array is required for comparison.")

        result = execute_comparison(raw_items)
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Comparison failed."),
            )
        return result

    @app.post("/api/compare/explain")
    def post_compare_explain(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        """Generate evidence-grounded AI comparison explanation."""
        comp_data = payload.get("comparison") or payload
        provider_override = payload.get("provider")
        return generate_comparison_ai_explanation(comp_data, provider_name=provider_override)

    def _export_comparison_observations(observations: List[Any], export_format: str = "csv") -> Response:
        field_obs_list: List[FieldObservation] = []
        for idx, obs in enumerate(observations, start=1):
            if isinstance(obs, dict):
                fo = FieldObservation(
                    id=obs.get("id", idx),
                    test_id=idx,
                    domain=obs.get("domain", "Unknown"),
                    resolved_ip=obs.get("resolved_ip", "Unknown"),
                    ip_version=obs.get("ip_version", "IPv4"),
                    country=obs.get("country", "Unknown"),
                    region=obs.get("region", "Unknown"),
                    city=obs.get("city", "Unknown"),
                    latitude=obs.get("latitude"),
                    longitude=obs.get("longitude"),
                    geolocation_confidence=obs.get("geolocation_confidence", "Unknown"),
                    asn=obs.get("asn", "Unknown"),
                    organization=obs.get("organization", "Unknown"),
                    isp=obs.get("isp", "Unknown"),
                    network_type=obs.get("network_type", "Unknown"),
                    infrastructure_type=obs.get("infrastructure_type", "Unknown"),
                    https_status=obs.get("https_status", "Unknown"),
                    tls_status=obs.get("tls_status", "Unknown"),
                    vpn_status=obs.get("vpn_status", "Unknown"),
                    proxy_status=obs.get("proxy_status", "Unknown"),
                    tor_status=obs.get("tor_status", "Unknown"),
                    website_trust_score=obs.get("website_trust_score"),
                    website_trust_classification=obs.get("website_trust_classification", "Unknown"),
                    ip_risk_score=obs.get("ip_risk_score"),
                    ip_risk_classification=obs.get("ip_risk_classification", "Unknown"),
                    score_confidence=obs.get("score_confidence", "Unknown"),
                    observed_at=obs.get("tested_at") or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                )
                field_obs_list.append(fo)

        if export_format.lower() == "json":
            json_data = export_field_study_json(observations=field_obs_list)
            json_str = json.dumps(json_data, indent=2)
            return Response(
                content=json_str.encode("utf-8"),
                media_type="application/json; charset=utf-8",
                headers={"Content-Disposition": 'attachment; filename="IP_PULSE_Comparison.json"'},
            )
        else:
            csv_content = export_field_study_csv(observations=field_obs_list)
            return Response(
                content=csv_content.encode("utf-8"),
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": 'attachment; filename="IP_PULSE_Comparison.csv"'},
            )

    @app.post("/api/compare/export")
    def post_compare_export(payload: Dict[str, Any] = Body(...)) -> Response:
        """Export compared observations as CSV or JSON."""
        observations = payload.get("observations", [])
        export_format = str(payload.get("format", "csv")).lower()
        return _export_comparison_observations(observations, export_format)

    @app.get("/api/compare/export")
    def get_compare_export(format: str = Query("csv")) -> Response:
        """Export top candidate observations as CSV or JSON."""
        candidates = get_comparison_candidates().get("candidates", [])
        return _export_comparison_observations(candidates[:5], format)

    @app.post("/api/analyze")
    def post_analyze(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        """Execute complete multi-layered IP Intelligence and Security scan."""
        target = str(payload.get("target") or payload.get("query") or "").strip()
        searched_by = str(payload.get("searched_by") or payload.get("investigator") or "Anonymous").strip() or "Anonymous"
        save_to_field_study = payload.get("save_to_field_study", True)

        if not target:
            raise HTTPException(status_code=400, detail="Target domain or IP address is required.")

        try:
            result = perform_full_intelligence_scan(target, save_to_db=True)
            base = result.base_lookup

            # Automatically record observation in Field Study with searched_by attribution
            field_study_recorded = False
            field_obs_data = None
            if save_to_field_study:
                try:
                    fs_ok, fs_msg, fs_obs = add_field_observation(
                        target=target,
                        lookup_res=result,
                        searched_by=searched_by,
                        update_if_exists=True,
                    )
                    if fs_ok and fs_obs:
                        field_study_recorded = True
                        field_obs_data = fs_obs.to_dict()
                except Exception as fs_err:
                    logger.warning(f"Could not auto-record field observation for {target}: {fs_err}")

            sec = result.security
            intel = result.ip_intel
            risk = result.risk
            chain = result.chain
            ip_val = base.selected_ip or target

            return {
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
                "searched_by": searched_by,
                "field_study_recorded": field_study_recorded,
                "field_study_observation": field_obs_data,
                "provenance": [
                    {"stage": "DNS Resolution", "source": "Core Resolver", "status": base.dns_status, "details": f"Resolved {base.selected_ip}"},
                    {"stage": "Geolocation", "source": "Multi-Provider Geo", "status": base.geolocation_status, "details": f"{base.city}, {base.country}"},
                    {"stage": "Security Probe", "source": "Website Scanner", "status": "AUDITED", "details": f"HTTPS: {getattr(sec, 'https_enabled', False)}"},
                    {"stage": "IP Intelligence", "source": "Infrastructure Engine", "status": "CLASSIFIED", "details": f"Class: {getattr(intel, 'infrastructure_type', 'Unknown')}"},
                ],
            }
        except Exception as e:
            logger.exception(f"Error analyzing target {target}: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis engine error: {str(e)}")

    # -------------------------------------------------------------------------
    # Static Web Files & SPA Fallback
    # -------------------------------------------------------------------------

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> Response:
        """Serve Stitch Single Page Application and static assets with path safety."""
        clean_path = full_path.split("?")[0].lstrip("/")
        if not clean_path:
            clean_path = "index.html"

        dist_dir = FRONTEND_DIR / "dist"
        if dist_dir.exists() and (dist_dir / clean_path).is_file():
            target_file = (dist_dir / clean_path).resolve()
            base_scope = dist_dir
        else:
            if clean_path.startswith("assets/"):
                clean_path = clean_path.replace("assets/", "src/", 1)
            target_file = (FRONTEND_DIR / clean_path).resolve()
            base_scope = FRONTEND_DIR

        # Directory traversal security check
        try:
            target_file.relative_to(base_scope.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

        if not target_file.exists() or not target_file.is_file():
            fallback = FRONTEND_DIR / "index.html"
            if fallback.exists():
                target_file = fallback
            else:
                raise HTTPException(status_code=404, detail="Resource not found")

        mime_type, _ = mimetypes.guess_type(str(target_file))
        if not mime_type:
            mime_type = "application/octet-stream"
        if mime_type.startswith("text/") or mime_type in ["application/javascript", "application/json"]:
            mime_type = f"{mime_type}; charset=utf-8"

        return FileResponse(
            path=str(target_file),
            media_type=mime_type,
            headers={
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "SAMEORIGIN",
                "Referrer-Policy": "strict-origin-when-cross-origin",
            },
        )

    return app
