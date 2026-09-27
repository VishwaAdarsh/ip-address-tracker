"""
Safe Database Migration Utility for IP PULSE Platform.

Migrates legitimate records from local SQLite (data/ip_tracker.db) into
production PostgreSQL / Supabase datastore.
Safely excludes known invalid/test domains and duplicate records.
"""
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Union

from backend.config.settings import DATABASE_URL, IS_POSTGRES, SQLITE_DB_PATH
from backend.database.repository import PostgresRepository, SQLiteRepository, get_repository
from backend.models.models import FieldObservation, LookupRecord

logger = logging.getLogger(__name__)

# Known mock / dummy test domains to filter out
KNOWN_MOCK_DOMAINS = {
    "",
    "nonexistent.invalid",
    "invalid.domain.test",
    "test.dummy",
    "mock.local",
}


def is_legitimate_record(domain: str, ip: str) -> bool:
    """Validate whether an observation domain and IP represent legitimate real data."""
    dom = (domain or "").strip().lower()
    ip_val = (ip or "").strip()
    if not dom and not ip_val:
        return False
    if dom in KNOWN_MOCK_DOMAINS:
        return False
    if dom.endswith(".invalid") or dom.endswith(".test"):
        return False
    return True


def migrate_sqlite_to_postgres(
    sqlite_path: Optional[Union[str, Path]] = None,
    postgres_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Safely migrate stored real observations from SQLite into PostgreSQL.

    Returns:
    - Summary dict with migrated counts for lookup_history and field_study_observations.
    """
    src_path = Path(sqlite_path or SQLITE_DB_PATH)
    if not src_path.exists():
        logger.warning(f"Source SQLite database does not exist at '{src_path}'. Migration aborted.")
        return {"success": False, "error": f"SQLite database not found at {src_path}", "history_migrated": 0, "field_study_migrated": 0}

    target_url = postgres_url or DATABASE_URL
    if not target_url:
        logger.warning("No PostgreSQL DATABASE_URL configured. Migration aborted.")
        return {"success": False, "error": "No DATABASE_URL configured.", "history_migrated": 0, "field_study_migrated": 0}

    # Initialize destination repository
    dest_repo = PostgresRepository(connection_url=target_url)
    dest_repo.init_schema()

    # Read from SQLite directly
    conn = sqlite3.connect(src_path)
    conn.row_factory = sqlite3.Row

    history_migrated = 0
    field_study_migrated = 0

    try:
        # 1. Migrate Lookup History
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lookup_history ORDER BY id ASC;")
        history_rows = cursor.fetchall()
        for r in history_rows:
            dom = r["domain"] or r["input_value"] or ""
            ip = r["ip_address"] or ""
            if not is_legitimate_record(dom, ip):
                continue

            keys = r.keys()
            rec = LookupRecord(
                timestamp=r["timestamp"],
                input_value=r["input_value"],
                input_type=r["input_type"],
                domain=r["domain"] or "",
                ip_address=r["ip_address"] or "",
                ip_version=r["ip_version"] or "IPv4",
                country=r["country"] or "Unknown",
                country_code=r["country_code"] if "country_code" in keys else "N/A",
                region=r["region"] or "Unknown",
                city=r["city"] or "Unknown",
                latitude=r["latitude"],
                longitude=r["longitude"],
                timezone=r["timezone"] if "timezone" in keys else "N/A",
                organization=r["organization"] or "Unknown",
                isp=r["isp"] or "Unknown",
                asn=r["asn"] or "Unknown",
                dns_response_time_ms=r["dns_response_time_ms"] or 0.0,
                api_response_time_ms=r["api_response_time_ms"] or 0.0,
                status=r["status"] or "SUCCESS",
                error_message=r["error_message"],
                infrastructure=r["infrastructure"] if "infrastructure" in keys and r["infrastructure"] else "Unknown",
                vpn_status=r["vpn_status"] if "vpn_status" in keys and r["vpn_status"] else "Unknown",
                proxy_status=r["proxy_status"] if "proxy_status" in keys and r["proxy_status"] else "Unknown",
                tor_status=r["tor_status"] if "tor_status" in keys and r["tor_status"] else "Unknown",
                https_status=r["https_status"] if "https_status" in keys and r["https_status"] else "Unknown",
                tls_status=r["tls_status"] if "tls_status" in keys and r["tls_status"] else "Unknown",
                trust_score=r["trust_score"] if "trust_score" in keys else None,
                trust_classification=r["trust_classification"] if "trust_classification" in keys and r["trust_classification"] else "Unknown",
                risk_score=r["risk_score"] if "risk_score" in keys else None,
                risk_classification=r["risk_classification"] if "risk_classification" in keys and r["risk_classification"] else "Unknown",
                confidence=r["confidence"] if "confidence" in keys and r["confidence"] else "Unknown",
                evidence_coverage=r["evidence_coverage"] if "evidence_coverage" in keys else None,
            )
            saved_id = dest_repo.save_lookup(rec)
            if saved_id is not None:
                history_migrated += 1

        # 2. Migrate Field Study Observations
        cursor.execute("SELECT * FROM field_study_observations ORDER BY id ASC;")
        field_rows = cursor.fetchall()
        for r in field_rows:
            dom = r["domain"] or ""
            ip = r["resolved_ip"] or ""
            if not is_legitimate_record(dom, ip):
                continue

            keys = r.keys()
            obs = FieldObservation(
                test_id=r["test_id"] or 0,
                domain=dom,
                category=r["category"] or "General Web",
                resolved_ip=r["resolved_ip"] or "",
                ip_version=r["ip_version"] or "IPv4",
                country=r["country"] or "Unknown",
                country_code=r["country_code"] if "country_code" in keys and r["country_code"] else "N/A",
                region=r["region"] or "Unknown",
                city=r["city"] or "Unknown",
                latitude=r["latitude"],
                longitude=r["longitude"],
                geolocation_confidence=r["geolocation_confidence"] or "Unknown",
                asn=r["asn"] or "Unknown",
                organization=r["organization"] or "Unknown",
                isp=r["isp"] or "Unknown",
                network_type=r["network_type"] or "Unknown",
                infrastructure_type=r["infrastructure_type"] or "Unknown",
                https_status=r["https_status"] or "Unknown",
                tls_status=r["tls_status"] or "Unknown",
                vpn_status=r["vpn_status"] or "Unknown",
                proxy_status=r["proxy_status"] or "Unknown",
                tor_status=r["tor_status"] or "Unknown",
                website_trust_score=r["website_trust_score"],
                website_trust_classification=r["website_trust_classification"] or "Unknown",
                ip_risk_score=r["ip_risk_score"],
                ip_risk_classification=r["ip_risk_classification"] or "Unknown",
                score_confidence=r["score_confidence"] or "Unknown",
                evidence_coverage=r["evidence_coverage"],
                observation_status=r["observation_status"] or "RECORDED",
                observed_at=r["observed_at"] or "",
                raw_history_id=r["raw_history_id"],
                dns_response_time_ms=r["dns_response_time_ms"] or 0.0,
                api_response_time_ms=r["api_response_time_ms"] or 0.0,
                timezone=r["timezone"] if "timezone" in keys and r["timezone"] else "N/A",
                error_message=r["error_message"],
                searched_by=r["searched_by"] if "searched_by" in keys and r["searched_by"] else "Anonymous",
            )
            saved_id = dest_repo.save_field_observation(obs, update_if_exists=True)
            if saved_id is not None:
                field_study_migrated += 1

    finally:
        conn.close()

    summary = {
        "success": True,
        "history_migrated": history_migrated,
        "field_study_migrated": field_study_migrated,
    }
    logger.info(f"Migration completed: {summary}")
    return summary


if __name__ == "__main__":
    import sys
    print("Executing IP PULSE SQLite -> PostgreSQL Migration...")
    res = migrate_sqlite_to_postgres()
    print("Result:", res)
