"""
Comprehensive Test Suite for Phase 17 Explainable Website Trust & IP Risk Engine.
Validates all 18 core evaluation scenarios, determinism, boundaries,
signal attribution, classifications, and confidence calculations.
"""
import unittest

from backend.intelligence.ip_intel import IPIntelligence, IPIntelligenceResult
from backend.security.risk_engine import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_UNKNOWN,
    IP_RISK_DISCLAIMER,
    RISK_TIER_CRITICAL,
    RISK_TIER_ELEVATED,
    RISK_TIER_HIGH,
    RISK_TIER_LOW,
    RISK_TIER_MODERATE,
    RISK_TIER_UNKNOWN,
    TRUST_DISCLAIMER,
    TRUST_TIER_GENERALLY_SAFE,
    TRUST_TIER_HIGH_RISK,
    TRUST_TIER_LIKELY_SAFE,
    TRUST_TIER_REVIEW_RECOMMENDED,
    TRUST_TIER_SUSPICIOUS,
    TRUST_TIER_UNKNOWN,
    UNIFIED_DISCLAIMER,
    calculate_confidence,
    classify_ip_risk_score,
    classify_trust_score,
    evaluate_ip_risk,
    evaluate_trust_and_risk,
    evaluate_website_trust,
)
from backend.security.security_scanner import SecurityInfo, WebsiteSecurityResult


class TestExplainableScoringEngine(unittest.TestCase):
    """Validation of all 18 evaluation scenarios for Phase 17."""

    # --------------------------------------------------------------------------
    # Scenario 1: All positive signals
    # --------------------------------------------------------------------------
    def test_01_all_positive_signals(self):
        sec = SecurityInfo(
            target="example.com",
            https_enabled=True,
            ssl_valid=True,
            ssl_issuer="DigiCert Global Root G2",
            ssl_expiry_days=180,
            redirect_count=1,
            security_headers={"hsts": True, "csp": True, "x_frame_options": True},
        )
        intel = IPIntelligence(
            is_tor=False,
            is_proxy=False,
            is_vpn=False,
            is_datacenter=False,
            infrastructure_type="CDN / Edge Hub",
        )

        trust = evaluate_website_trust(sec)
        ip_risk = evaluate_ip_risk(intel)

        # Base 50 + 20(https) + 15(cert) + 15(valid) + 5(lifespan) + 10(redirect) + 10(hsts) + 5(headers) = 130 -> clamped to 100
        self.assertEqual(trust.score, 100)
        self.assertEqual(trust.classification, TRUST_TIER_LIKELY_SAFE)
        self.assertEqual(trust.confidence, CONFIDENCE_HIGH)
        self.assertEqual(trust.evidence_coverage, "8/8")
        self.assertGreater(trust.positive_points, 0)
        self.assertEqual(trust.negative_points, 0)

        # Base 5 - 5(CDN) = 0
        self.assertEqual(ip_risk.score, 0)
        self.assertEqual(ip_risk.classification, RISK_TIER_LOW)
        self.assertEqual(ip_risk.confidence, CONFIDENCE_HIGH)
        self.assertEqual(ip_risk.evidence_coverage, "5/5")
        self.assertEqual(ip_risk.mitigation_points, 5)

    # --------------------------------------------------------------------------
    # Scenario 2: Mixed positive and negative signals
    # --------------------------------------------------------------------------
    def test_02_mixed_positive_and_negative_signals(self):
        # Mixed: HTTPS enabled (+20), but invalid cert (-25), expired (-15), no redirect (-10)
        sec = WebsiteSecurityResult(
            domain="expired-warning.com",
            https_enabled=True,
            certificate_present=True,
            certificate_valid=False,
            certificate_issuer="Self-Signed",
            certificate_days_remaining=-5,
            http_to_https_redirect=False,
        )
        intel = IPIntelligence(
            is_tor=False,
            is_proxy=False,
            is_vpn=False,
            is_datacenter=True,
            infrastructure_type="Cloud Hosting",
        )

        trust = evaluate_website_trust(sec)
        ip_risk = evaluate_ip_risk(intel)

        # Base 50 + 20(https) + 15(cert present) - 25(invalid) - 15(expired) - 10(no redirect) = 35
        self.assertEqual(trust.score, 35)
        self.assertEqual(trust.classification, TRUST_TIER_SUSPICIOUS)
        self.assertGreater(trust.positive_points, 0)
        self.assertGreater(trust.negative_points, 0)

        # Base 5 + 10(datacenter) = 15
        self.assertEqual(ip_risk.score, 15)
        self.assertEqual(ip_risk.classification, RISK_TIER_LOW)
        self.assertEqual(ip_risk.risk_points, 10)

    # --------------------------------------------------------------------------
    # Scenario 3: No available signals (empty/None)
    # --------------------------------------------------------------------------
    def test_03_no_available_signals_empty_or_none(self):
        trust = evaluate_website_trust(None)
        ip_risk = evaluate_ip_risk(None)

        self.assertEqual(trust.score, 50)
        self.assertEqual(trust.confidence, CONFIDENCE_UNKNOWN)
        self.assertEqual(trust.evidence_coverage, "0/8")
        self.assertEqual(len(trust.signals), 0)
        self.assertGreater(len(trust.unknown_signals), 0)

        self.assertEqual(ip_risk.score, 5)
        self.assertEqual(ip_risk.confidence, CONFIDENCE_UNKNOWN)
        self.assertEqual(ip_risk.evidence_coverage, "0/5")
        self.assertEqual(len(ip_risk.signals), 0)
        self.assertGreater(len(ip_risk.unknown_signals), 0)

        unified = evaluate_trust_and_risk(None, None)
        self.assertEqual(unified.trust_score, 50)
        self.assertEqual(unified.risk_score, 5)
        self.assertEqual(unified.disclaimer, UNIFIED_DISCLAIMER)
        self.assertIn("Assessment limited", unified.trust.explanation)
        self.assertIn("Assessment limited", unified.ip_risk.explanation)

    # --------------------------------------------------------------------------
    # Scenario 4: Unknown signals (neutral 0 pt treatment)
    # --------------------------------------------------------------------------
    def test_04_unknown_signals_neutral_zero_points(self):
        # WebsiteSecurityResult with all None/Unknown fields
        sec = WebsiteSecurityResult(
            domain="unresolved.internal",
            https_enabled=None,
            http_to_https_redirect=None,
            tls_available=None,
            certificate_present=None,
            certificate_valid=None,
            certificate_status="Unknown",
            certificate_issuer="Unknown",
            certificate_days_remaining=None,
        )
        trust = evaluate_website_trust(sec)

        # All signals should be classified as unknown with 0 points
        self.assertEqual(trust.score, 50)
        self.assertEqual(trust.positive_points, 0)
        self.assertEqual(trust.negative_points, 0)
        self.assertEqual(trust.available_signals_count, 0)
        self.assertEqual(trust.total_signals_count, 8)
        self.assertEqual(trust.confidence, CONFIDENCE_UNKNOWN)
        for sig in trust.unknown_signals:
            self.assertEqual(sig["points"], 0)
            self.assertFalse(sig["is_available"])

    # --------------------------------------------------------------------------
    # Scenario 5: HTTPS enabled vs disabled
    # --------------------------------------------------------------------------
    def test_05_https_enabled_vs_disabled(self):
        sec_enabled = WebsiteSecurityResult(
            domain="secure.com",
            https_enabled=True,
            certificate_present=True,
            certificate_valid=True,
            certificate_days_remaining=60,
        )
        sec_disabled = WebsiteSecurityResult(
            domain="plain-http.com",
            https_enabled=False,
            certificate_present=False,
            certificate_valid=False,
            certificate_days_remaining=None,
            http_to_https_redirect=False,
        )

        trust_enabled = evaluate_website_trust(sec_enabled)
        trust_disabled = evaluate_website_trust(sec_disabled)

        self.assertGreater(trust_enabled.score, trust_disabled.score)
        # Enabled gets +20, Disabled gets -25 on HTTPS transport signal
        https_sig_en = next(s for s in trust_enabled.signals if s["name"] == "HTTPS Protocol")
        https_sig_dis = next(s for s in trust_disabled.signals if s["name"] == "HTTPS Protocol")
        self.assertEqual(https_sig_en["points"], 20)
        self.assertEqual(https_sig_dis["points"], -25)

    # --------------------------------------------------------------------------
    # Scenario 6: Invalid certificate vs valid certificate
    # --------------------------------------------------------------------------
    def test_06_invalid_certificate_vs_valid_certificate(self):
        sec_valid = WebsiteSecurityResult(
            domain="trusted.com",
            https_enabled=True,
            certificate_present=True,
            certificate_valid=True,
            certificate_issuer="Let's Encrypt",
            certificate_days_remaining=60,
        )
        sec_invalid = WebsiteSecurityResult(
            domain="untrusted.com",
            https_enabled=True,
            certificate_present=True,
            certificate_valid=False,
            certificate_issuer="Untrusted Root",
            certificate_days_remaining=60,
        )

        trust_valid = evaluate_website_trust(sec_valid)
        trust_invalid = evaluate_website_trust(sec_invalid)

        self.assertGreater(trust_valid.score, trust_invalid.score)
        val_sig = next(s for s in trust_valid.signals if s["name"] == "Certificate Trust Chain")
        inval_sig = next(s for s in trust_invalid.signals if s["name"] == "Certificate Trust Chain")
        self.assertEqual(val_sig["points"], 15)
        self.assertEqual(inval_sig["points"], -25)

    # --------------------------------------------------------------------------
    # Scenario 7: VPN detected
    # --------------------------------------------------------------------------
    def test_07_vpn_detected(self):
        intel_vpn = IPIntelligence(
            is_vpn=True,
            is_tor=False,
            is_proxy=False,
            is_datacenter=False,
            infrastructure_type="Commercial ISP",
        )
        ip_risk = evaluate_ip_risk(intel_vpn)

        # Base 5 + 20(VPN) = 25
        self.assertEqual(ip_risk.score, 25)
        self.assertEqual(ip_risk.classification, RISK_TIER_MODERATE)
        vpn_sig = next(s for s in ip_risk.signals if s["name"] == "Commercial VPN")
        self.assertEqual(vpn_sig["status"], "Detected")
        self.assertEqual(vpn_sig["points"], 20)

    # --------------------------------------------------------------------------
    # Scenario 8: Proxy detected
    # --------------------------------------------------------------------------
    def test_08_proxy_detected(self):
        intel_proxy = IPIntelligence(
            is_proxy=True,
            is_tor=False,
            is_vpn=False,
            is_datacenter=False,
            infrastructure_type="Commercial ISP",
        )
        ip_risk = evaluate_ip_risk(intel_proxy)

        # Base 5 + 25(Proxy) = 30
        self.assertEqual(ip_risk.score, 30)
        self.assertEqual(ip_risk.classification, RISK_TIER_MODERATE)
        proxy_sig = next(s for s in ip_risk.signals if s["name"] == "Proxy Gateway")
        self.assertEqual(proxy_sig["status"], "Detected")
        self.assertEqual(proxy_sig["points"], 25)

    # --------------------------------------------------------------------------
    # Scenario 9: Tor detected
    # --------------------------------------------------------------------------
    def test_09_tor_detected(self):
        intel_tor = IPIntelligence(
            is_tor=True,
            is_proxy=False,
            is_vpn=False,
            is_datacenter=False,
            infrastructure_type="Unknown",
        )
        ip_risk = evaluate_ip_risk(intel_tor)

        # Base 5 + 65(Tor) = 70
        self.assertEqual(ip_risk.score, 70)
        self.assertEqual(ip_risk.classification, RISK_TIER_HIGH)
        tor_sig = next(s for s in ip_risk.signals if s["name"] == "Tor Exit Node")
        self.assertEqual(tor_sig["status"], "Detected")
        self.assertEqual(tor_sig["points"], 65)

    # --------------------------------------------------------------------------
    # Scenario 10: Datacenter infrastructure
    # --------------------------------------------------------------------------
    def test_10_datacenter_infrastructure(self):
        intel_dc = IPIntelligence(
            is_datacenter=True,
            is_tor=False,
            is_proxy=False,
            is_vpn=False,
            infrastructure_type="Cloud Hosting",
        )
        ip_risk = evaluate_ip_risk(intel_dc)

        # Base 5 + 10(Datacenter) = 15
        # Datacenter alone does NOT mark host as malicious or critical
        self.assertEqual(ip_risk.score, 15)
        self.assertEqual(ip_risk.classification, RISK_TIER_LOW)
        dc_sig = next(s for s in ip_risk.signals if s["name"] == "Datacenter Hosting")
        self.assertEqual(dc_sig["points"], 10)

    # --------------------------------------------------------------------------
    # Scenario 11: Normal infrastructure (baseline risk != 0)
    # --------------------------------------------------------------------------
    def test_11_normal_infrastructure_baseline_risk_not_zero(self):
        intel_normal = IPIntelligence(
            is_tor=False,
            is_proxy=False,
            is_vpn=False,
            is_datacenter=False,
            infrastructure_type="Commercial ISP",
        )
        ip_risk = evaluate_ip_risk(intel_normal)

        # Base ambient risk is 5, NOT 0
        self.assertEqual(ip_risk.score, 5)
        self.assertEqual(ip_risk.classification, RISK_TIER_LOW)
        self.assertEqual(ip_risk.risk_points, 0)
        self.assertEqual(len(ip_risk.signals), 0)
        self.assertGreater(len(ip_risk.neutral_signals), 0)

    # --------------------------------------------------------------------------
    # Scenario 12: Multiple risk signals combined
    # --------------------------------------------------------------------------
    def test_12_multiple_risk_signals_combined(self):
        intel_multi = IPIntelligence(
            is_tor=True,         # +65
            is_proxy=True,       # +25
            is_vpn=True,         # +20
            is_datacenter=True,  # +10
            infrastructure_type="Cloud Hosting",
        )
        ip_risk = evaluate_ip_risk(intel_multi)

        # Base 5 + 65 + 25 + 20 + 10 = 125 -> clamped to 100
        self.assertEqual(ip_risk.score, 100)
        self.assertEqual(ip_risk.classification, RISK_TIER_CRITICAL)
        self.assertEqual(ip_risk.risk_points, 120)

    # --------------------------------------------------------------------------
    # Scenario 13: Determinism: identical inputs produce identical scores
    # --------------------------------------------------------------------------
    def test_13_determinism(self):
        sec = SecurityInfo(
            target="google.com",
            https_enabled=True,
            ssl_valid=True,
            ssl_issuer="GTS CA 1C3",
            ssl_expiry_days=75,
            redirect_count=1,
            security_headers={"hsts": True, "csp": False, "x_frame_options": True},
        )
        intel = IPIntelligence(
            is_tor=False,
            is_proxy=False,
            is_vpn=False,
            is_datacenter=True,
            infrastructure_type="CDN / Edge Hub",
        )

        first_trust = evaluate_website_trust(sec)
        first_risk = evaluate_ip_risk(intel)

        for _ in range(50):
            next_trust = evaluate_website_trust(sec)
            next_risk = evaluate_ip_risk(intel)
            self.assertEqual(first_trust.score, next_trust.score)
            self.assertEqual(first_trust.classification, next_trust.classification)
            self.assertEqual(first_trust.confidence, next_trust.confidence)
            self.assertEqual(first_trust.evidence_coverage, next_trust.evidence_coverage)
            self.assertEqual(first_risk.score, next_risk.score)
            self.assertEqual(first_risk.classification, next_risk.classification)
            self.assertEqual(first_risk.confidence, next_risk.confidence)

    # --------------------------------------------------------------------------
    # Scenario 14: Score never below 0
    # --------------------------------------------------------------------------
    def test_14_score_never_below_zero(self):
        sec_horrible = WebsiteSecurityResult(
            domain="malformed.insecure",
            https_enabled=False,           # -25
            certificate_present=False,     # -20
            certificate_valid=False,
            certificate_days_remaining=-100, # -15
            http_to_https_redirect=False,  # -10
        )
        # Base 50 - 25 - 20 - 15 - 10 = -20 -> clamped to 0
        trust = evaluate_website_trust(sec_horrible)
        self.assertGreaterEqual(trust.score, 0)
        self.assertEqual(trust.score, 0)
        self.assertEqual(trust.classification, TRUST_TIER_HIGH_RISK)

        intel_cdn = IPIntelligence(
            is_tor=False,
            is_proxy=False,
            is_vpn=False,
            is_datacenter=False,
            infrastructure_type="CDN / Edge Hub", # -5 mitigation
        )
        # Base 5 - 5 = 0
        ip_risk = evaluate_ip_risk(intel_cdn)
        self.assertGreaterEqual(ip_risk.score, 0)
        self.assertEqual(ip_risk.score, 0)

    # --------------------------------------------------------------------------
    # Scenario 15: Score never exceeds 100
    # --------------------------------------------------------------------------
    def test_15_score_never_exceeds_100(self):
        sec_perfect = SecurityInfo(
            target="perfect-grade.com",
            https_enabled=True,            # +20
            ssl_valid=True,                # +15
            ssl_issuer="DigiCert EV",
            ssl_expiry_days=300,           # +5
            redirect_count=1,              # +10
            security_headers={"hsts": True, "csp": True, "x_frame_options": True}, # +10, +5
        )
        # Base 50 + 80 = 130 -> clamped to 100
        trust = evaluate_website_trust(sec_perfect)
        self.assertLessEqual(trust.score, 100)
        self.assertEqual(trust.score, 100)

        intel_risky = IPIntelligence(
            is_tor=True,        # +65
            is_proxy=True,      # +25
            is_vpn=True,        # +20
            is_datacenter=True, # +10
        )
        # Base 5 + 120 = 125 -> clamped to 100
        ip_risk = evaluate_ip_risk(intel_risky)
        self.assertLessEqual(ip_risk.score, 100)
        self.assertEqual(ip_risk.score, 100)

    # --------------------------------------------------------------------------
    # Scenario 16: Classification thresholds mapping
    # --------------------------------------------------------------------------
    def test_16_classification_thresholds_mapping(self):
        # Website Trust thresholds
        self.assertEqual(classify_trust_score(100), TRUST_TIER_LIKELY_SAFE)
        self.assertEqual(classify_trust_score(80), TRUST_TIER_LIKELY_SAFE)
        self.assertEqual(classify_trust_score(79), TRUST_TIER_GENERALLY_SAFE)
        self.assertEqual(classify_trust_score(60), TRUST_TIER_GENERALLY_SAFE)
        self.assertEqual(classify_trust_score(59), TRUST_TIER_REVIEW_RECOMMENDED)
        self.assertEqual(classify_trust_score(40), TRUST_TIER_REVIEW_RECOMMENDED)
        self.assertEqual(classify_trust_score(39), TRUST_TIER_SUSPICIOUS)
        self.assertEqual(classify_trust_score(20), TRUST_TIER_SUSPICIOUS)
        self.assertEqual(classify_trust_score(19), TRUST_TIER_HIGH_RISK)
        self.assertEqual(classify_trust_score(0), TRUST_TIER_HIGH_RISK)
        self.assertEqual(classify_trust_score(50, available_signals=0), TRUST_TIER_UNKNOWN)

        # IP Risk thresholds
        self.assertEqual(classify_ip_risk_score(0), RISK_TIER_LOW)
        self.assertEqual(classify_ip_risk_score(19), RISK_TIER_LOW)
        self.assertEqual(classify_ip_risk_score(20), RISK_TIER_MODERATE)
        self.assertEqual(classify_ip_risk_score(39), RISK_TIER_MODERATE)
        self.assertEqual(classify_ip_risk_score(40), RISK_TIER_ELEVATED)
        self.assertEqual(classify_ip_risk_score(59), RISK_TIER_ELEVATED)
        self.assertEqual(classify_ip_risk_score(60), RISK_TIER_HIGH)
        self.assertEqual(classify_ip_risk_score(79), RISK_TIER_HIGH)
        self.assertEqual(classify_ip_risk_score(80), RISK_TIER_CRITICAL)
        self.assertEqual(classify_ip_risk_score(100), RISK_TIER_CRITICAL)
        self.assertEqual(classify_ip_risk_score(5, available_signals=0), RISK_TIER_UNKNOWN)

    # --------------------------------------------------------------------------
    # Scenario 17: Confidence calculation independence from score
    # --------------------------------------------------------------------------
    def test_17_confidence_calculation_independence_from_score(self):
        # Case A: High evidence coverage (8/8) on an insecure site -> High confidence, low score
        sec_bad = SecurityInfo(
            target="insecure-known.com",
            https_enabled=False,
            ssl_valid=False,
            ssl_issuer="N/A",
            ssl_expiry_days=-20,
            redirect_count=0,
            security_headers={"hsts": False, "csp": False, "x_frame_options": False},
        )
        trust_bad = evaluate_website_trust(sec_bad)
        self.assertEqual(trust_bad.confidence, CONFIDENCE_HIGH)
        self.assertLess(trust_bad.score, 30)

        # Case B: Zero evidence coverage (0/8) -> Unknown confidence, neutral score
        trust_none = evaluate_website_trust(None)
        self.assertEqual(trust_none.confidence, CONFIDENCE_UNKNOWN)
        self.assertEqual(trust_none.score, 50)

        # Direct verification of calculate_confidence utility
        tier, ratio = calculate_confidence(available_count=8, total_count=8)
        self.assertEqual(tier, CONFIDENCE_HIGH)
        self.assertEqual(ratio, 1.0)

        tier_med, ratio_med = calculate_confidence(available_count=5, total_count=8)
        self.assertEqual(tier_med, CONFIDENCE_MEDIUM)
        self.assertAlmostEqual(ratio_med, 0.62, places=2)

        tier_low, ratio_low = calculate_confidence(available_count=2, total_count=8)
        self.assertEqual(tier_low, CONFIDENCE_LOW)

        tier_unk, ratio_unk = calculate_confidence(available_count=0, total_count=8)
        self.assertEqual(tier_unk, CONFIDENCE_UNKNOWN)

    # --------------------------------------------------------------------------
    # Scenario 18: Evidence coverage calculation (X/Y format)
    # --------------------------------------------------------------------------
    def test_18_evidence_coverage_calculation(self):
        sec_partial = WebsiteSecurityResult(
            domain="partial.com",
            https_enabled=True,
            certificate_valid=True,
            certificate_days_remaining=90,
            # Other signals omitted / None
        )
        trust = evaluate_website_trust(sec_partial)

        self.assertTrue("/" in trust.evidence_coverage)
        parts = [int(p) for p in trust.evidence_coverage.split("/")]
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], trust.available_signals_count)
        self.assertEqual(parts[1], trust.total_signals_count)
        self.assertEqual(parts[0] + len(trust.unknown_signals), parts[1])

        intel_full = IPIntelligence(
            is_tor=False,
            is_proxy=False,
            is_vpn=False,
            is_datacenter=False,
            infrastructure_type="Commercial ISP",
        )
        ip_risk = evaluate_ip_risk(intel_full)
        self.assertEqual(ip_risk.evidence_coverage, "5/5")
        self.assertEqual(ip_risk.available_signals_count, 5)
        self.assertEqual(ip_risk.total_signals_count, 5)


if __name__ == "__main__":
    unittest.main()
