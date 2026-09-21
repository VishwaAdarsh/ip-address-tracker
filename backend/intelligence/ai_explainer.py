"""
Explainable AI Intelligence Layer Module for IP PULSE Platform (Phase 22).

Provides:
- Strict evidence-grounded AI explanation layer on top of deterministic IP PULSE intelligence
- Multi-provider abstraction (Local Rule-Based Factual Engine and Google Gemini API)
- Zero data fabrication guarantee: explicitly reports UNKNOWN for unmeasured dimensions
- Strict non-definitive security claims policy (no "100% safe" or "definitely malicious")
- Data minimization and privacy protection: sends only necessary intelligence telemetry
- In-memory duplicate request caching and timeout protection
- 100% score preservation: Trust Score and IP Risk Score remain completely unmodified
"""
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
import datetime
import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Union

from backend.config.settings import (
    AI_API_KEY,
    AI_ENABLED,
    AI_MODEL,
    AI_PROVIDER,
    AI_TIMEOUT,
)
from backend.intelligence.intel_chain import IntelligenceChain
from backend.intelligence.ip_intel import IPIntelligence
from backend.security.risk_engine import RiskScore
from backend.security.security_scanner import SecurityInfo

logger = logging.getLogger(__name__)

# Standardized limitations disclaimer
STANDARD_LIMITATIONS_DISCLAIMER = (
    "AI explanations are analytical syntheses of empirical point-in-time telemetry. "
    "They do not constitute certified cybersecurity audits, legal attestations, or guarantees of future behavior. "
    "Deterministic classifications and underlying technical evidence remain authoritative."
)


@dataclass
class AIExplanationResult:
    """Standardized result model for AI Explanations."""

    status: str                                  # "success", "provider_unavailable", "quota_exceeded", "timeout", "error"
    provider: str                                # "rule_based", "gemini", etc.
    model: str                                   # e.g. "gemini-2.5-flash" or "deterministic-v1"
    summary: str
    trust_explanation: str
    risk_explanation: str
    positive_signals: List[str] = field(default_factory=list)
    negative_signals: List[str] = field(default_factory=list)
    unknown_signals: List[str] = field(default_factory=list)
    recommendation: str = ""
    limitations: str = STANDARD_LIMITATIONS_DISCLAIMER
    cached: bool = False
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert explanation result to clean JSON-serializable dictionary."""
        return asdict(self)


def sanitize_security_claims(text: str) -> str:
    """
    Post-process explanation text to ensure no definitive or absolute security claims
    were generated (enforcing Section 4: No Definitive Security Claims).
    """
    replacements = [
        (r"\b100%\s*safe\b", "appears lower risk based on available signals"),
        (r"\bcompletely\s*safe\b", "generally safe indicators"),
        (r"\bcompletely\s*secure\b", "configured with robust transport security"),
        (r"\bdefinitely\s*genuine\b", "exhibits authentic infrastructure characteristics"),
        (r"\bdefinitely\s*fake\b", "exhibits elevated anomaly indicators"),
        (r"\bdefinitely\s*malicious\b", "presents significant risk factors"),
        (r"\bguaranteed\s*safe\b", "currently shows no active anomalies"),
        (r"\bguaranteed\s*secure\b", "meets standard encryption benchmarks"),
    ]
    cleaned = text
    for pattern, repl in replacements:
        cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
    return cleaned


def build_explanation_payload(
    target: str,
    intelligence: Union[Dict[str, Any], Any],
) -> Dict[str, Any]:
    """
    Construct a data-minimized, strictly factual explanation payload from scan results.
    
    Privacy & Data Minimization:
    - Never includes database paths, file systems, API keys, or user identities.
    - Only extracts verified network, security, and risk evidence.
    """
    payload: Dict[str, Any] = {
        "target": target,
        "domain": target,
        "resolved_ip": "UNKNOWN",
        "ip_version": "UNKNOWN",
        "country": "UNKNOWN",
        "region": "UNKNOWN",
        "city": "UNKNOWN",
        "latitude": None,
        "longitude": None,
        "asn": "UNKNOWN",
        "organization": "UNKNOWN",
        "isp": "UNKNOWN",
        "network_type": "UNKNOWN",
        "infrastructure_type": "UNKNOWN",
        "vpn_status": "UNKNOWN",
        "proxy_status": "UNKNOWN",
        "tor_status": "UNKNOWN",
        "datacenter_status": "UNKNOWN",
        "https_enabled": "UNKNOWN",
        "tls_valid": "UNKNOWN",
        "tls_version": "UNKNOWN",
        "tls_issuer": "UNKNOWN",
        "ssl_expiry_days": "UNKNOWN",
        "hsts_enabled": "UNKNOWN",
        "csp_enabled": "UNKNOWN",
        "redirect_count": 0,
        "website_trust_score": None,
        "website_trust_level": "UNKNOWN",
        "ip_risk_score": None,
        "ip_risk_level": "UNKNOWN",
        "confidence_score": None,
        "ip_personality": "UNKNOWN",
        "positive_signals": [],
        "negative_signals": [],
        "unknown_signals": [],
    }

    # Case A: Input is a Dictionary (e.g. from api/server.py or frontend JSON)
    if isinstance(intelligence, dict):
        base = intelligence.get("base", {})
        sec = intelligence.get("security", {})
        intel = intelligence.get("ip_intel", {})
        risk = intelligence.get("risk", {})
        chain = intelligence.get("intelligence_chain", {})
        personality = intelligence.get("personality") or intelligence.get("ip_personality")

        payload["resolved_ip"] = base.get("selected_ip") or intel.get("ip_address") or "UNKNOWN"
        payload["ip_version"] = base.get("ip_version") or "UNKNOWN"
        payload["country"] = base.get("country") or "UNKNOWN"
        payload["region"] = base.get("region") or "UNKNOWN"
        payload["city"] = base.get("city") or "UNKNOWN"
        payload["latitude"] = base.get("latitude")
        payload["longitude"] = base.get("longitude")
        payload["asn"] = base.get("asn") or intel.get("asn") or "UNKNOWN"
        payload["organization"] = base.get("organization") or intel.get("organization") or "UNKNOWN"
        payload["isp"] = base.get("isp") or intel.get("isp") or "UNKNOWN"
        payload["network_type"] = intel.get("network_type") or "UNKNOWN"
        payload["infrastructure_type"] = intel.get("infrastructure_type") or chain.get("infrastructure") or "UNKNOWN"
        payload["vpn_status"] = intel.get("vpn_status") or "UNKNOWN"
        payload["proxy_status"] = intel.get("proxy_status") or "UNKNOWN"
        payload["tor_status"] = intel.get("tor_status") or "UNKNOWN"
        payload["datacenter_status"] = intel.get("datacenter_status") or "UNKNOWN"

        payload["https_enabled"] = sec.get("is_https", "UNKNOWN")
        payload["tls_valid"] = sec.get("tls_valid", "UNKNOWN")
        payload["tls_version"] = sec.get("tls_version") or "UNKNOWN"
        payload["tls_issuer"] = sec.get("issuer_org") or "UNKNOWN"
        payload["ssl_expiry_days"] = sec.get("expires_in_days", "UNKNOWN")
        payload["hsts_enabled"] = sec.get("hsts_header", "UNKNOWN")
        payload["csp_enabled"] = sec.get("csp_header", "UNKNOWN")
        payload["redirect_count"] = sec.get("redirect_count", 0)

        payload["website_trust_score"] = risk.get("trust_score")
        payload["website_trust_level"] = risk.get("trust", {}).get("classification") if isinstance(risk.get("trust"), dict) else risk.get("trust_level", "UNKNOWN")
        payload["ip_risk_score"] = risk.get("risk_score")
        payload["ip_risk_level"] = risk.get("risk_category") or risk.get("risk_level", "UNKNOWN")
        payload["confidence_score"] = risk.get("confidence_score")
        
        if isinstance(personality, dict):
            payload["ip_personality"] = personality.get("summary") or "UNKNOWN"
        elif isinstance(personality, str):
            payload["ip_personality"] = personality

        payload["positive_signals"] = list(risk.get("positive_factors") or [])
        payload["negative_signals"] = list(risk.get("risk_factors") or [])

    # Case B: Input is an Object with attributes (e.g. FullIntelligenceResult)
    else:
        base = getattr(intelligence, "base_lookup", None)
        sec = getattr(intelligence, "security", None)
        intel = getattr(intelligence, "ip_intel", None)
        risk = getattr(intelligence, "risk", None)
        chain = getattr(intelligence, "chain", None)

        if base:
            payload["resolved_ip"] = getattr(base, "selected_ip", "UNKNOWN") or "UNKNOWN"
            payload["ip_version"] = getattr(base, "ip_version", "UNKNOWN") or "UNKNOWN"
            payload["country"] = getattr(base, "country", "UNKNOWN") or "UNKNOWN"
            payload["region"] = getattr(base, "region", "UNKNOWN") or "UNKNOWN"
            payload["city"] = getattr(base, "city", "UNKNOWN") or "UNKNOWN"
            payload["latitude"] = getattr(base, "latitude", None)
            payload["longitude"] = getattr(base, "longitude", None)
            payload["asn"] = getattr(base, "asn", "UNKNOWN") or "UNKNOWN"
            payload["organization"] = getattr(base, "organization", "UNKNOWN") or "UNKNOWN"
            payload["isp"] = getattr(base, "isp", "UNKNOWN") or "UNKNOWN"

        if intel:
            payload["infrastructure_type"] = getattr(intel, "infrastructure_type", "UNKNOWN") or "UNKNOWN"
            payload["network_type"] = getattr(intel, "network_type", "UNKNOWN") or "UNKNOWN"
            payload["vpn_status"] = "DETECTED" if getattr(intel, "is_vpn", False) else "NOT_DETECTED"
            payload["proxy_status"] = "DETECTED" if getattr(intel, "is_proxy", False) else "NOT_DETECTED"
            payload["tor_status"] = "DETECTED" if getattr(intel, "is_tor", False) else "NOT_DETECTED"
            payload["datacenter_status"] = "DETECTED" if getattr(intel, "is_datacenter", False) else "NOT_DETECTED"

        if sec:
            payload["https_enabled"] = getattr(sec, "https_enabled", "UNKNOWN")
            payload["tls_valid"] = getattr(sec, "ssl_valid", "UNKNOWN")
            payload["tls_version"] = getattr(sec, "tls_version", "UNKNOWN") or "UNKNOWN"
            payload["tls_issuer"] = getattr(sec, "ssl_issuer", "UNKNOWN") or "UNKNOWN"
            payload["ssl_expiry_days"] = getattr(sec, "ssl_expiry_days", "UNKNOWN")
            payload["redirect_count"] = getattr(sec, "redirect_count", 0)
            headers = getattr(sec, "security_headers", {})
            if isinstance(headers, dict):
                payload["hsts_enabled"] = headers.get("hsts", "UNKNOWN")
                payload["csp_enabled"] = headers.get("csp", "UNKNOWN")

        if risk:
            payload["website_trust_score"] = getattr(risk, "trust_score", None)
            payload["ip_risk_score"] = getattr(risk, "risk_score", None)
            payload["ip_risk_level"] = getattr(risk, "risk_level", "UNKNOWN")
            payload["confidence_score"] = getattr(risk, "confidence_score", None)
            payload["positive_signals"] = list(getattr(risk, "positive_factors", []))
            payload["negative_signals"] = list(getattr(risk, "risk_factors", []))

        if chain:
            payload["ip_personality"] = getattr(chain, "ip_personality", "UNKNOWN") or "UNKNOWN"

    # Identify Unknown / Unavailable signals explicitly
    unknowns = []
    if payload["country"] in ("UNKNOWN", "N/A", "", None):
        unknowns.append("Geographic Location Telemetry (Country/City)")
    if payload["asn"] in ("UNKNOWN", "N/A", "", None):
        unknowns.append("Autonomous System (ASN) Registration")
    if payload["tls_issuer"] in ("UNKNOWN", "N/A", "", None):
        unknowns.append("TLS Certificate Authority Issuer")
    if payload["hsts_enabled"] in ("UNKNOWN", None):
        unknowns.append("HTTP Strict Transport Security (HSTS) Header")
    if payload["csp_enabled"] in ("UNKNOWN", None):
        unknowns.append("Content Security Policy (CSP) Header")
    if payload["network_type"] in ("UNKNOWN", "N/A", "", None):
        unknowns.append("Carrier / Enterprise Network Type")
    
    payload["unknown_signals"] = unknowns
    return payload


class AIExplanationProvider(ABC):
    """Abstract Base Class for AI Explanation Providers."""

    @abstractmethod
    def generate_explanation(self, payload: Dict[str, Any]) -> AIExplanationResult:
        """Generate a verified, evidence-grounded explanation from the provided payload."""
        pass


class RuleBasedAIProvider(AIExplanationProvider):
    """
    Deterministic, offline factual explanation engine.
    
    Synthesizes real empirical signals into structured, professional natural language
    without external API calls, latency, or monetary costs.
    """

    def generate_explanation(self, payload: Dict[str, Any]) -> AIExplanationResult:
        target = payload.get("target", "target")
        ip = payload.get("resolved_ip", "UNKNOWN")
        asn = payload.get("asn", "UNKNOWN")
        org = payload.get("organization", "UNKNOWN")
        country = payload.get("country", "UNKNOWN")
        city = payload.get("city", "UNKNOWN")
        trust_score = payload.get("website_trust_score")
        trust_level = payload.get("website_trust_level", "UNKNOWN")
        risk_score = payload.get("ip_risk_score")
        risk_level = payload.get("ip_risk_level", "UNKNOWN")
        infra = payload.get("infrastructure_type", "Unknown Infrastructure")
        personality = payload.get("ip_personality", "Standard network endpoint")
        https = payload.get("https_enabled")
        tls_valid = payload.get("tls_valid")
        tls_issuer = payload.get("tls_issuer", "UNKNOWN")
        expiry = payload.get("ssl_expiry_days")
        hsts = payload.get("hsts_enabled")
        vpn = payload.get("vpn_status", "UNKNOWN")
        tor = payload.get("tor_status", "UNKNOWN")
        dc = payload.get("datacenter_status", "UNKNOWN")
        positive_factors = payload.get("positive_signals", [])
        risk_factors = payload.get("negative_signals", [])
        unknown_signals = payload.get("unknown_signals", [])

        # 1. Executive Summary
        location_str = f"{city}, {country}".strip(", ") if city != "UNKNOWN" or country != "UNKNOWN" else "an unknown location"
        sec_str = "enforcing encrypted HTTPS" if https is True else ("lacking transport encryption (HTTP)" if https is False else "with unmeasured transport encryption")
        summary = (
            f"Target '{target}' resolves to {ip} ({org}, {asn}) geolocated in {location_str}. "
            f"The host operates under a '{infra}' profile {sec_str}. "
            f"Deterministic evaluation registers a Website Trust Score of {trust_score if trust_score is not None else 'N/A'}/100 "
            f"and an IP Risk Score of {risk_score if risk_score is not None else 'N/A'}/100, placing it in the '{risk_level} Risk' bracket."
        )

        # 2. Trust Score Explanation
        trust_reasons = []
        if https is True:
            if tls_valid is True:
                trust_reasons.append(f"A valid TLS certificate is present, issued by '{tls_issuer}'")
                if isinstance(expiry, (int, float)) and expiry > 0:
                    trust_reasons.append(f"Certificate has {int(expiry)} days remaining before expiration")
            else:
                trust_reasons.append("HTTPS is active, but the TLS certificate validation was unsuccessful or self-signed")
        elif https is False:
            trust_reasons.append("HTTPS is not enforced; plain unencrypted HTTP transport penalizes the Trust Score")
        else:
            trust_reasons.append("Transport encryption signals were unavailable or unmeasured")

        if hsts is True:
            trust_reasons.append("HTTP Strict Transport Security (HSTS) is enabled, protecting against downgrade attacks")
        
        trust_explanation = (
            f"The Website Trust Score of {trust_score if trust_score is not None else 'N/A'}/100 is driven by empirical transport signals: "
            + "; ".join(trust_reasons) + "."
        )

        # 3. Risk Score Explanation
        risk_reasons = []
        if vpn == "DETECTED":
            risk_reasons.append("Commercial VPN exit node presence detected")
        if tor == "DETECTED":
            risk_reasons.append("Tor anonymizing relay detected")
        if dc == "DETECTED":
            risk_reasons.append(f"Hosting infrastructure is located in a datacenter / cloud facility ({infra})")
        if not risk_reasons:
            risk_reasons.append("No active anonymizer nodes, proxies, or high-risk routing anomalies were detected")
        
        risk_explanation = (
            f"The IP Risk Score of {risk_score if risk_score is not None else 'N/A'}/100 reflects infrastructure and network provenance: "
            + "; ".join(risk_reasons) + "."
        )

        # 4. Recommendation & Synthesis
        if risk_score is not None and risk_score <= 25 and (trust_score is None or trust_score >= 70):
            recommendation = (
                f"The target appears lower risk based on available technical signals. "
                f"Network profile '{personality}' aligns with established hosting norms. Standard precautions apply."
            )
        elif risk_score is not None and risk_score >= 60:
            recommendation = (
                f"Review recommended: Elevated risk signals or anonymization mechanisms were identified. "
                f"Verify domain ownership and observe caution before transmitting sensitive credentials."
            )
        else:
            recommendation = (
                f"Assessment indicates moderate risk characteristics or partial evidence coverage. "
                f"Examine underlying infrastructure and verify domain authenticity independently."
            )

        return AIExplanationResult(
            status="success",
            provider="rule_based",
            model="deterministic-factual-v1",
            summary=sanitize_security_claims(summary),
            trust_explanation=sanitize_security_claims(trust_explanation),
            risk_explanation=sanitize_security_claims(risk_explanation),
            positive_signals=list(positive_factors),
            negative_signals=list(risk_factors),
            unknown_signals=list(unknown_signals),
            recommendation=sanitize_security_claims(recommendation),
            limitations=STANDARD_LIMITATIONS_DISCLAIMER,
            cached=False,
        )


class GeminiAIProvider(AIExplanationProvider):
    """
    Google Gemini API provider utilizing structured output and strict evidence grounding.
    """

    def __init__(self, api_key: str = "", model_name: str = "gemini-2.5-flash", timeout: float = 10.0):
        self.api_key = api_key or AI_API_KEY
        self.model_name = model_name or AI_MODEL
        self.timeout = timeout

    def generate_explanation(self, payload: Dict[str, Any]) -> AIExplanationResult:
        if not self.api_key:
            logger.warning("Gemini AI Provider requested without API key.")
            return AIExplanationResult(
                status="provider_unavailable",
                provider="gemini",
                model=self.model_name,
                summary="AI explanation unavailable. Gemini API key (AI_API_KEY or GEMINI_API_KEY) is not configured.",
                trust_explanation="Deterministic analysis remains fully available.",
                risk_explanation="Deterministic analysis remains fully available.",
                recommendation="Configure an API key in your environment or use the local rule-based engine.",
                limitations=STANDARD_LIMITATIONS_DISCLAIMER,
                error_message="Missing API key",
            )

        # Build strict system prompt and user input
        system_instruction = (
            "You are the IP PULSE Explainable AI Engine. Your task is to provide a concise, professional explanation "
            "of an existing technical scan based ONLY on the provided JSON intelligence data.\n\n"
            "CRITICAL RULES:\n"
            "1. STRICT FACTUAL GROUNDING: NEVER invent DNS records, certificate information, threat intelligence, "
            "malware detections, or company reputation. If a field is UNKNOWN or missing, explicitly state it is unavailable.\n"
            "2. NO DEFINITIVE SECURITY CLAIMS: NEVER say '100% safe', 'definitely genuine', 'definitely malicious', "
            "or 'completely secure'. Instead use calibrated language like 'appears lower risk based on available signals', "
            "'generally safe indicators', or 'review recommended'.\n"
            "3. SCORE PRESERVATION: NEVER alter the Trust Score or IP Risk Score. Explain why the existing deterministic scores were assigned.\n"
            "4. OUTPUT FORMAT: Output valid JSON adhering exactly to the requested schema."
        )

        prompt = (
            f"Analyze the following network intelligence and produce an explanation:\n"
            f"{json.dumps(payload, indent=2)}\n\n"
            f"Respond with JSON having these exact keys:\n"
            f"- summary (string: concise overview answering what was detected)\n"
            f"- trust_explanation (string: explains why Trust Score received this value)\n"
            f"- risk_explanation (string: explains why Risk Score received this value)\n"
            f"- positive_signals (array of strings)\n"
            f"- negative_signals (array of strings)\n"
            f"- unknown_signals (array of strings)\n"
            f"- recommendation (string: calibrated user takeaway and review advice)"
        )

        try:
            # Attempt official google.genai package first
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )
                raw_text = response.text or "{}"
            except Exception as lib_err:
                logger.debug(f"google.genai library call failed ({lib_err}), falling back to direct REST request.")
                # Direct REST fallback using requests
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
                req_body = {
                    "contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt}"}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json",
                    },
                }
                resp = requests.post(url, json=req_body, timeout=self.timeout)
                if resp.status_code == 429:
                    return AIExplanationResult(
                        status="quota_exceeded",
                        provider="gemini",
                        model=self.model_name,
                        summary="AI explanation quota limit reached. Deterministic intelligence is unaffected.",
                        trust_explanation="Deterministic analysis remains available.",
                        risk_explanation="Deterministic analysis remains available.",
                        recommendation="Try again later or use the local rule-based provider.",
                        error_message="HTTP 429 Quota Exceeded",
                    )
                resp.raise_for_status()
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

            # Parse and validate JSON structure
            # Clean possible markdown wrapping (```json ... ```)
            clean_json = raw_text.strip()
            if clean_json.startswith("```"):
                clean_json = re.sub(r"^```(?:json)?\n?", "", clean_json)
                clean_json = re.sub(r"\n?```$", "", clean_json)

            parsed = json.loads(clean_json)

            return AIExplanationResult(
                status="success",
                provider="gemini",
                model=self.model_name,
                summary=sanitize_security_claims(parsed.get("summary", "Summary unavailable.")),
                trust_explanation=sanitize_security_claims(parsed.get("trust_explanation", "Trust analysis unavailable.")),
                risk_explanation=sanitize_security_claims(parsed.get("risk_explanation", "Risk analysis unavailable.")),
                positive_signals=parsed.get("positive_signals", payload.get("positive_signals", [])),
                negative_signals=parsed.get("negative_signals", payload.get("negative_signals", [])),
                unknown_signals=parsed.get("unknown_signals", payload.get("unknown_signals", [])),
                recommendation=sanitize_security_claims(parsed.get("recommendation", "Review recommended.")),
                limitations=STANDARD_LIMITATIONS_DISCLAIMER,
                cached=False,
            )

        except Exception as err:
            logger.error(f"Gemini AI provider invocation failed: {err}")
            err_str = str(err).lower()
            if "timeout" in err_str:
                status = "timeout"
                msg = "AI provider request timed out. Deterministic analysis is fully preserved."
            elif "429" in err_str or "quota" in err_str:
                status = "quota_exceeded"
                msg = "AI provider rate limit reached. Deterministic analysis is fully preserved."
            else:
                status = "error"
                msg = f"AI explanation generation encountered an issue: {str(err)}"

            return AIExplanationResult(
                status=status,
                provider="gemini",
                model=self.model_name,
                summary=msg,
                trust_explanation="Deterministic analysis remains available.",
                risk_explanation="Deterministic analysis remains available.",
                recommendation="Review the deterministic Trust & Risk score cards.",
                error_message=str(err),
            )


# In-memory explanation cache (Target + Evidence Hash -> AIExplanationResult)
_EXPLANATION_CACHE: Dict[str, AIExplanationResult] = {}
_MAX_CACHE_ENTRIES = 100


def _compute_evidence_hash(payload: Dict[str, Any]) -> str:
    """Compute a deterministic hash of the intelligence payload to prevent duplicate API calls."""
    key_fields = {
        "target": payload.get("target"),
        "ip": payload.get("resolved_ip"),
        "trust": payload.get("website_trust_score"),
        "risk": payload.get("ip_risk_score"),
        "https": payload.get("https_enabled"),
        "tls": payload.get("tls_valid"),
        "vpn": payload.get("vpn_status"),
        "infra": payload.get("infrastructure_type"),
    }
    raw = json.dumps(key_fields, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def get_ai_provider(provider_name: Optional[str] = None) -> AIExplanationProvider:
    """Factory resolver for AI explanation providers."""
    name = (provider_name or AI_PROVIDER or "rule_based").lower().strip()
    if name == "gemini":
        return GeminiAIProvider()
    # Default to high-quality deterministic rule-based engine
    return RuleBasedAIProvider()


def explain_intelligence(
    target: str,
    intelligence: Union[Dict[str, Any], Any],
    provider_name: Optional[str] = None,
    bypass_cache: bool = False,
) -> AIExplanationResult:
    """
    Main entry point for Phase 22 Explainable AI Intelligence.

    Args:
    - target: Target domain or IP string
    - intelligence: FullIntelligenceResult or scan result dictionary
    - provider_name: Optional explicit provider override ("rule_based", "gemini")
    - bypass_cache: bool flag to ignore in-memory cache

    Returns:
    - AIExplanationResult with validated structured content
    """
    if not AI_ENABLED:
        return AIExplanationResult(
            status="provider_unavailable",
            provider=provider_name or AI_PROVIDER,
            model="disabled",
            summary="AI explanation layer is currently disabled in configuration (AI_ENABLED=false).",
            trust_explanation="Deterministic analysis remains fully available.",
            risk_explanation="Deterministic analysis remains fully available.",
            recommendation="Enable AI_ENABLED in configuration to activate explanations.",
            error_message="AI layer disabled",
        )

    # 1. Build minimized payload
    payload = build_explanation_payload(target, intelligence)

    # 2. Check In-Memory Cache (Cost & Quota Protection)
    cache_key = f"{target.strip().lower()}::{_compute_evidence_hash(payload)}"
    if not bypass_cache and cache_key in _EXPLANATION_CACHE:
        cached_res = _EXPLANATION_CACHE[cache_key]
        return AIExplanationResult(
            status=cached_res.status,
            provider=cached_res.provider,
            model=cached_res.model,
            summary=cached_res.summary,
            trust_explanation=cached_res.trust_explanation,
            risk_explanation=cached_res.risk_explanation,
            positive_signals=list(cached_res.positive_signals),
            negative_signals=list(cached_res.negative_signals),
            unknown_signals=list(cached_res.unknown_signals),
            recommendation=cached_res.recommendation,
            limitations=cached_res.limitations,
            cached=True,
            error_message=cached_res.error_message,
        )

    # 3. Resolve Provider and Generate Explanation
    provider = get_ai_provider(provider_name)
    result = provider.generate_explanation(payload)

    # 4. Cache successful or rule-based results (up to max limit)
    if result.status == "success":
        if len(_EXPLANATION_CACHE) >= _MAX_CACHE_ENTRIES:
            # Evict oldest entry
            _EXPLANATION_CACHE.pop(next(iter(_EXPLANATION_CACHE)))
        _EXPLANATION_CACHE[cache_key] = result

    return result


def generate_ai_explanation(
    target: str,
    security: SecurityInfo,
    ip_intel: IPIntelligence,
    risk: RiskScore,
    chain: IntelligenceChain,
) -> str:
    """
    Backward-compatible adapter for existing risk_analysis_service.py integration.
    
    Returns a unified multi-paragraph explanation string.
    """
    # Build a pseudo payload from objects
    payload = build_explanation_payload(
        target,
        type("TempResult", (), {
            "base_lookup": None,
            "security": security,
            "ip_intel": ip_intel,
            "risk": risk,
            "chain": chain,
        })(),
    )
    result = RuleBasedAIProvider().generate_explanation(payload)
    paragraphs = [
        result.summary,
        f"Trust Analysis: {result.trust_explanation}",
        f"Risk Analysis: {result.risk_explanation}",
        f"Synthesis: {result.recommendation}",
    ]
    return "\n\n".join(paragraphs)
