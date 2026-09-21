"""
Database Access Layer for IP Address Tracker & Geolocation Tool.

Responsible for:
- Managing SQLite database connections and table initialization
- Persisting completed LookupResult objects into lookup_history table
- Using parameterized SQL statements to prevent SQL injection
- Providing methods for history retrieval, single record deletion, and clearing history
"""
import contextlib
import logging
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING, Any, List, Optional, Union

from backend.config.settings import BASE_DIR
from backend.models.models import FieldObservation, LookupRecord

if TYPE_CHECKING:
    from backend.services.lookup_service import LookupResult

logger = logging.getLogger(__name__)


def get_db_path(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """Return the absolute path to the SQLite database file, ensuring data directory exists."""
    if custom_path:
        path = Path(custom_path)
    else:
        path = BASE_DIR / "data" / "ip_tracker.db"

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection(
    db_path: Optional[Union[str, Path]] = None
) -> sqlite3.Connection:
    """Open and return a SQLite database connection with row_factory enabled and foreign keys enforced."""
    target_path = get_db_path(db_path)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn



def init_db(db_path: Optional[Union[str, Path]] = None) -> None:
    """Initialize SQLite database schema for lookup history and 50-site field study."""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS lookup_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        input_value TEXT NOT NULL,
        input_type TEXT NOT NULL,
        domain TEXT,
        ip_address TEXT,
        ip_version TEXT,
        country TEXT,
        country_code TEXT,
        region TEXT,
        city TEXT,
        latitude REAL,
        longitude REAL,
        timezone TEXT,
        organization TEXT,
        isp TEXT,
        asn TEXT,
        dns_response_time_ms REAL,
        api_response_time_ms REAL,
        status TEXT NOT NULL,
        error_message TEXT
    );

    CREATE TABLE IF NOT EXISTS field_study_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER,
        domain TEXT NOT NULL UNIQUE,
        category TEXT DEFAULT 'General Web',
        resolved_ip TEXT,
        ip_version TEXT DEFAULT 'IPv4',
        country TEXT DEFAULT 'Unknown',
        region TEXT DEFAULT 'Unknown',
        city TEXT DEFAULT 'Unknown',
        latitude REAL,
        longitude REAL,
        geolocation_confidence TEXT DEFAULT 'Unknown',
        asn TEXT DEFAULT 'Unknown',
        organization TEXT DEFAULT 'Unknown',
        isp TEXT DEFAULT 'Unknown',
        network_type TEXT DEFAULT 'Unknown',
        infrastructure_type TEXT DEFAULT 'Unknown',
        https_status TEXT DEFAULT 'Unknown',
        tls_status TEXT DEFAULT 'Unknown',
        vpn_status TEXT DEFAULT 'Unknown',
        proxy_status TEXT DEFAULT 'Unknown',
        tor_status TEXT DEFAULT 'Unknown',
        website_trust_score REAL,
        website_trust_classification TEXT DEFAULT 'Unknown',
        ip_risk_score REAL,
        ip_risk_classification TEXT DEFAULT 'Unknown',
        score_confidence TEXT DEFAULT 'Unknown',
        evidence_coverage REAL,
        observation_status TEXT DEFAULT 'RECORDED',
        observed_at TEXT NOT NULL,
        raw_history_id INTEGER,
        dns_response_time_ms REAL DEFAULT 0.0,
        api_response_time_ms REAL DEFAULT 0.0,
        error_message TEXT,
        searched_by TEXT DEFAULT 'Anonymous'
    );
    """
    try:
        conn = get_connection(db_path)
        try:
            conn.executescript(schema_sql)
            # Safe schema migration for searched_by column
            try:
                conn.execute("ALTER TABLE field_study_observations ADD COLUMN searched_by TEXT DEFAULT 'Anonymous';")
            except sqlite3.OperationalError:
                pass
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize SQLite database schema: {e}")
        raise


def save_lookup(
    result: Any, db_path: Optional[Union[str, Path]] = None
) -> Optional[int]:
    """
    Save a completed LookupResult to the lookup_history table using parameterized SQL.

    Returns:
    - Inserted record ID on success, or None on failure without raising exceptions.
    """
    init_db(db_path)

    insert_sql = """
    INSERT INTO lookup_history (
        timestamp, input_value, input_type, domain, ip_address, ip_version,
        country, country_code, region, city, latitude, longitude, timezone,
        organization, isp, asn, dns_response_time_ms, api_response_time_ms,
        status, error_message
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    );
    """

    params = (
        result.timestamp,
        result.input,
        result.input_type,
        result.normalized_input
        if result.input_type == "DOMAIN"
        else (result.normalized_input if result.selected_ip else ""),
        result.selected_ip or "",
        result.ip_version,
        result.country,
        result.country_code,
        result.region,
        result.city,
        result.latitude,
        result.longitude,
        result.timezone,
        result.organization,
        result.isp,
        result.asn,
        result.dns_response_time_ms,
        result.api_response_time_ms,
        result.overall_status.value,
        result.error_message,
    )

    try:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(insert_sql, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to save lookup result to database: {e}")
        return None


def get_lookup_history(
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Union[str, Path]] = None,
) -> List[LookupRecord]:
    """
    Retrieve stored lookup history records, ordered by timestamp DESC (newest first).

    Parameters:
    - limit: Maximum number of records to retrieve (None for all records).
    - offset: Number of records to skip.
    """
    init_db(db_path)

    query_sql = """
    SELECT
        id, timestamp, input_value, input_type, domain, ip_address, ip_version,
        country, country_code, region, city, latitude, longitude, timezone,
        organization, isp, asn, dns_response_time_ms, api_response_time_ms,
        status, error_message
    FROM lookup_history
    ORDER BY timestamp DESC, id DESC
    """

    params: list = []
    if limit is not None:
        query_sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    records: List[LookupRecord] = []

    try:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()
            for row in rows:
                record = LookupRecord(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    input_value=row["input_value"],
                    input_type=row["input_type"],
                    domain=row["domain"] or "",
                    ip_address=row["ip_address"] or "",
                    ip_version=row["ip_version"] or "N/A",
                    country=row["country"] or "N/A",
                    country_code=row["country_code"] or "N/A",
                    region=row["region"] or "N/A",
                    city=row["city"] or "N/A",
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    timezone=row["timezone"] or "N/A",
                    organization=row["organization"] or "N/A",
                    isp=row["isp"] or "N/A",
                    asn=row["asn"] or "N/A",
                    dns_response_time_ms=row["dns_response_time_ms"] or 0.0,
                    api_response_time_ms=row["api_response_time_ms"] or 0.0,
                    status=row["status"] or "",
                    error_message=row["error_message"],
                )
                records.append(record)
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to retrieve lookup history from database: {e}")

    return records


def delete_lookup(
    record_id: int, db_path: Optional[Union[str, Path]] = None
) -> bool:
    """Delete a single lookup record by ID. Returns True if record was deleted."""
    init_db(db_path)

    delete_sql = "DELETE FROM lookup_history WHERE id = ?;"

    try:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(delete_sql, (record_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to delete lookup record {record_id}: {e}")
        return False


def clear_history(db_path: Optional[Union[str, Path]] = None) -> bool:
    """Clear all stored lookup records from lookup_history table."""
    init_db(db_path)

    clear_sql = "DELETE FROM lookup_history;"

    try:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(clear_sql)
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to clear lookup history: {e}")
        return False


# =============================================================================
# 50-Site Field Study Observation Operations (Phase 19)
# =============================================================================

def save_field_observation(
    obs: FieldObservation,
    db_path: Optional[Union[str, Path]] = None,
    update_if_exists: bool = False,
) -> Optional[int]:
    """
    Save a structured 50-site field observation to field_study_observations table.
    Enforces domain uniqueness or updates existing record if update_if_exists=True.

    Returns:
    - Inserted or updated record ID on success, or None on duplicate/failure.
    """
    init_db(db_path)

    if update_if_exists:
        try:
            conn = get_connection(db_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM field_study_observations WHERE domain = ?;",
                    (obs.domain.strip().lower(),),
                )
                existing_row = cursor.fetchone()
                if existing_row:
                    update_sql = """
                    UPDATE field_study_observations SET
                        category = ?, resolved_ip = ?, ip_version = ?,
                        country = ?, region = ?, city = ?, latitude = ?, longitude = ?,
                        geolocation_confidence = ?, asn = ?, organization = ?, isp = ?,
                        network_type = ?, infrastructure_type = ?, https_status = ?, tls_status = ?,
                        vpn_status = ?, proxy_status = ?, tor_status = ?,
                        website_trust_score = ?, website_trust_classification = ?,
                        ip_risk_score = ?, ip_risk_classification = ?, score_confidence = ?, evidence_coverage = ?,
                        observation_status = ?, observed_at = ?, raw_history_id = ?,
                        dns_response_time_ms = ?, api_response_time_ms = ?, error_message = ?,
                        searched_by = ?
                    WHERE id = ?;
                    """
                    update_params = (
                        obs.category or "General Web",
                        obs.resolved_ip or "",
                        obs.ip_version or "IPv4",
                        obs.country or "Unknown",
                        obs.region or "Unknown",
                        obs.city or "Unknown",
                        obs.latitude,
                        obs.longitude,
                        obs.geolocation_confidence or "Unknown",
                        obs.asn or "Unknown",
                        obs.organization or "Unknown",
                        obs.isp or "Unknown",
                        obs.network_type or "Unknown",
                        obs.infrastructure_type or "Unknown",
                        obs.https_status or "Unknown",
                        obs.tls_status or "Unknown",
                        obs.vpn_status or "Unknown",
                        obs.proxy_status or "Unknown",
                        obs.tor_status or "Unknown",
                        obs.website_trust_score,
                        obs.website_trust_classification or "Unknown",
                        obs.ip_risk_score,
                        obs.ip_risk_classification or "Unknown",
                        obs.score_confidence or "Unknown",
                        obs.evidence_coverage,
                        obs.observation_status or "RECORDED",
                        obs.observed_at,
                        obs.raw_history_id,
                        obs.dns_response_time_ms or 0.0,
                        obs.api_response_time_ms or 0.0,
                        obs.error_message,
                        getattr(obs, "searched_by", "Anonymous") or "Anonymous",
                        existing_row["id"],
                    )
                    cursor.execute(update_sql, update_params)
                    conn.commit()
                    return existing_row["id"]
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to update existing field observation: {e}")

    insert_sql = """
    INSERT INTO field_study_observations (
        test_id, domain, category, resolved_ip, ip_version,
        country, region, city, latitude, longitude, geolocation_confidence,
        asn, organization, isp, network_type, infrastructure_type,
        https_status, tls_status, vpn_status, proxy_status, tor_status,
        website_trust_score, website_trust_classification,
        ip_risk_score, ip_risk_classification, score_confidence, evidence_coverage,
        observation_status, observed_at, raw_history_id,
        dns_response_time_ms, api_response_time_ms, error_message, searched_by
    ) VALUES (
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?
    );
    """

    params = (
        obs.test_id,
        obs.domain.strip().lower(),
        obs.category or "General Web",
        obs.resolved_ip or "",
        obs.ip_version or "IPv4",
        obs.country or "Unknown",
        obs.region or "Unknown",
        obs.city or "Unknown",
        obs.latitude,
        obs.longitude,
        obs.geolocation_confidence or "Unknown",
        obs.asn or "Unknown",
        obs.organization or "Unknown",
        obs.isp or "Unknown",
        obs.network_type or "Unknown",
        obs.infrastructure_type or "Unknown",
        obs.https_status or "Unknown",
        obs.tls_status or "Unknown",
        obs.vpn_status or "Unknown",
        obs.proxy_status or "Unknown",
        obs.tor_status or "Unknown",
        obs.website_trust_score,
        obs.website_trust_classification or "Unknown",
        obs.ip_risk_score,
        obs.ip_risk_classification or "Unknown",
        obs.score_confidence or "Unknown",
        obs.evidence_coverage,
        obs.observation_status or "RECORDED",
        obs.observed_at,
        obs.raw_history_id,
        obs.dns_response_time_ms or 0.0,
        obs.api_response_time_ms or 0.0,
        obs.error_message,
        getattr(obs, "searched_by", "Anonymous") or "Anonymous",
    )

    try:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(insert_sql, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    except sqlite3.IntegrityError as ie:
        logger.warning(f"Duplicate domain rejected for field study: {obs.domain} ({ie})")
        return None
    except Exception as e:
        logger.error(f"Failed to save field observation: {e}")
        return None


def _row_to_field_observation(row: sqlite3.Row) -> FieldObservation:
    """Helper to convert sqlite3.Row into FieldObservation dataclass."""
    searched_by = "Anonymous"
    try:
        if "searched_by" in row.keys() and row["searched_by"]:
            searched_by = row["searched_by"]
    except Exception:
        pass

    return FieldObservation(
        id=row["id"],
        test_id=row["test_id"] or 0,
        domain=row["domain"] or "",
        category=row["category"] or "General Web",
        resolved_ip=row["resolved_ip"] or "",
        ip_version=row["ip_version"] or "IPv4",
        country=row["country"] or "Unknown",
        region=row["region"] or "Unknown",
        city=row["city"] or "Unknown",
        latitude=row["latitude"],
        longitude=row["longitude"],
        geolocation_confidence=row["geolocation_confidence"] or "Unknown",
        asn=row["asn"] or "Unknown",
        organization=row["organization"] or "Unknown",
        isp=row["isp"] or "Unknown",
        network_type=row["network_type"] or "Unknown",
        infrastructure_type=row["infrastructure_type"] or "Unknown",
        https_status=row["https_status"] or "Unknown",
        tls_status=row["tls_status"] or "Unknown",
        vpn_status=row["vpn_status"] or "Unknown",
        proxy_status=row["proxy_status"] or "Unknown",
        tor_status=row["tor_status"] or "Unknown",
        website_trust_score=row["website_trust_score"],
        website_trust_classification=row["website_trust_classification"] or "Unknown",
        ip_risk_score=row["ip_risk_score"],
        ip_risk_classification=row["ip_risk_classification"] or "Unknown",
        score_confidence=row["score_confidence"] or "Unknown",
        evidence_coverage=row["evidence_coverage"],
        searched_by=searched_by,
        observation_status=row["observation_status"] or "RECORDED",
        observed_at=row["observed_at"] or "",
        raw_history_id=row["raw_history_id"],
        dns_response_time_ms=row["dns_response_time_ms"] or 0.0,
        api_response_time_ms=row["api_response_time_ms"] or 0.0,
        error_message=row["error_message"],
    )


def get_field_observations(
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Union[str, Path]] = None,
) -> List[FieldObservation]:
    """Retrieve stored field study observations ordered by test_id ASC, id ASC."""
    init_db(db_path)

    query_sql = """
    SELECT * FROM field_study_observations
    ORDER BY test_id ASC, id ASC
    """
    params: list = []
    if limit is not None:
        query_sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    observations: List[FieldObservation] = []
    try:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()
            for r in rows:
                observations.append(_row_to_field_observation(r))
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to retrieve field observations: {e}")

    return observations


def get_field_observation_by_domain(
    domain: str, db_path: Optional[Union[str, Path]] = None
) -> Optional[FieldObservation]:
    """Find a field study observation by normalized domain string."""
    init_db(db_path)
    clean_dom = domain.strip().lower()

    query_sql = "SELECT * FROM field_study_observations WHERE domain = ? LIMIT 1;"
    try:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(query_sql, (clean_dom,))
            row = cursor.fetchone()
            if row:
                return _row_to_field_observation(row)
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to fetch field observation for {domain}: {e}")

    return None


def get_field_observation_by_id(
    obs_id: int, db_path: Optional[Union[str, Path]] = None
) -> Optional[FieldObservation]:
    """Find a field study observation by primary key ID."""
    init_db(db_path)

    query_sql = "SELECT * FROM field_study_observations WHERE id = ? LIMIT 1;"
    try:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(query_sql, (obs_id,))
            row = cursor.fetchone()
            if row:
                return _row_to_field_observation(row)
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to fetch field observation #{obs_id}: {e}")

    return None


def delete_field_observation(
    obs_id: int, db_path: Optional[Union[str, Path]] = None
) -> bool:
    """Delete a single field study observation by ID."""
    init_db(db_path)
    try:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM field_study_observations WHERE id = ?;", (obs_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to delete field observation #{obs_id}: {e}")
        return False


def clear_field_study(db_path: Optional[Union[str, Path]] = None) -> bool:
    """Clear all stored records from field_study_observations table."""
    init_db(db_path)
    try:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM field_study_observations;")
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to clear field study observations: {e}")
        return False


def migrate_historical_to_field_study(
    db_path: Optional[Union[str, Path]] = None,
    force: bool = False,
) -> int:
    """
    Backfill unique domain lookups from lookup_history into field_study_observations
    ONLY if explicitly requested via force=True.
    Default is disabled to preserve clean live user search state.
    """
    if not force:
        return 0

    init_db(db_path)
    existing_obs = get_field_observations(db_path=db_path)
    if existing_obs:
        return 0  # Already has observations, do not auto-backfill

    history_records = get_lookup_history(db_path=db_path)
    if not history_records:
        return 0

    # Read category map if websites.csv exists
    category_map: dict = {}
    try:
        from backend.services.field_test_service import load_test_websites
        websites = load_test_websites()
        category_map = {w["domain"]: w["category"] for w in websites}
    except Exception:
        pass

    seen_domains: set = set()
    inserted_count = 0
    # Process chronologically (earliest first)
    chronological_recs = list(reversed(history_records))

    for rec in chronological_recs:
        dom = (rec.domain or rec.input_value or "").lower().strip()
        if not dom or rec.status == "INVALID_INPUT" or not rec.ip_address:
            continue
        if dom in seen_domains:
            continue
        seen_domains.add(dom)

        cat = category_map.get(dom, "General Web")
        obs = FieldObservation(
            test_id=inserted_count + 1,
            domain=dom,
            category=cat,
            resolved_ip=rec.ip_address,
            ip_version=rec.ip_version or "IPv4",
            country=rec.country or "Unknown",
            region=rec.region or "Unknown",
            city=rec.city or "Unknown",
            latitude=rec.latitude,
            longitude=rec.longitude,
            geolocation_confidence="MEDIUM" if rec.country != "N/A" else "UNKNOWN",
            asn=rec.asn or "Unknown",
            organization=rec.organization or "Unknown",
            isp=rec.isp or "Unknown",
            network_type="Unknown",
            infrastructure_type="Unknown",
            https_status="Unknown",
            tls_status="Unknown",
            vpn_status="Unknown",
            proxy_status="Unknown",
            tor_status="Unknown",
            website_trust_score=85.0 if rec.status == "SUCCESS" else 40.0,
            website_trust_classification="GENERALLY SAFE" if rec.status == "SUCCESS" else "REVIEW RECOMMENDED",
            ip_risk_score=15.0 if rec.status == "SUCCESS" else 50.0,
            ip_risk_classification="LOW RISK" if rec.status == "SUCCESS" else "MODERATE",
            score_confidence="MEDIUM",
            evidence_coverage=0.5,
            observation_status="RECORDED",
            observed_at=rec.timestamp,
            raw_history_id=rec.id,
            dns_response_time_ms=rec.dns_response_time_ms,
            api_response_time_ms=rec.api_response_time_ms,
            error_message=rec.error_message,
        )
        saved_id = save_field_observation(obs, db_path=db_path)
        if saved_id is not None:
            inserted_count += 1

    return inserted_count

