"""
Unified Database Access Layer for IP PULSE Platform.

Supports:
- Local Development & Testing: SQLite with WAL mode, foreign keys, and safe schema migrations.
- Production Deployment: PostgreSQL / Supabase persistent hosted database configured via DATABASE_URL.
- Preserves 100% API backwards compatibility with all services and automated tests.
"""
import logging
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from backend.config.settings import BASE_DIR, DATABASE_URL, IS_POSTGRES, MIGRATE_ON_STARTUP, SQLITE_DB_PATH
from backend.database.repository import (
    BaseDatabaseRepository,
    PostgresRepository,
    SQLiteRepository,
    get_repository,
)
from backend.models.models import FieldObservation, LookupRecord

if TYPE_CHECKING:
    from backend.services.lookup_service import LookupResult

logger = logging.getLogger(__name__)


def get_db_path(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """Return absolute path to SQLite database file."""
    if custom_path:
        path = Path(custom_path)
    else:
        path = SQLITE_DB_PATH

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection(
    db_path: Optional[Union[str, Path]] = None
) -> sqlite3.Connection:
    """
    Open and return a SQLite database connection with row_factory enabled.
    Maintained for legacy compatibility with tests.
    """
    target_path = get_db_path(db_path)
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> None:
    """Initialize database schema on active storage engine (SQLite or PostgreSQL)."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    repo.init_schema()

    # Optional auto-migration from SQLite to PostgreSQL if configured
    if IS_POSTGRES and MIGRATE_ON_STARTUP and not db_path:
        try:
            from backend.database.migration import migrate_sqlite_to_postgres
            current_obs = repo.get_field_observations(limit=1)
            if not current_obs:
                logger.info("Empty PostgreSQL detected. Running automated migration from SQLite...")
                migrate_sqlite_to_postgres(sqlite_path=SQLITE_DB_PATH, postgres_url=DATABASE_URL)
        except Exception as e:
            logger.warning(f"Startup migration skipped or encountered error: {e}")


def save_lookup(
    result: Any,
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> Optional[int]:
    """Save a completed lookup result or record to active database."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.save_lookup(result)


def get_lookup_history(
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> List[LookupRecord]:
    """Retrieve stored lookup records, ordered newest first."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.get_lookup_history(limit=limit, offset=offset)


def delete_lookup(
    record_id: int,
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> bool:
    """Delete a single lookup record by stable ID."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.delete_lookup(record_id)


def delete_lookups_batch(
    record_ids: List[int],
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> int:
    """Delete multiple lookup records by their stable IDs."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.delete_lookups_batch(record_ids)


def clear_history(
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> bool:
    """Clear all stored lookup records."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.clear_history()


def save_field_observation(
    obs: FieldObservation,
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
    update_if_exists: bool = False,
) -> Optional[int]:
    """Save a structured field study observation."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.save_field_observation(obs, update_if_exists=update_if_exists)


def get_field_observations(
    limit: Optional[int] = None,
    offset: int = 0,
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> List[FieldObservation]:
    """Retrieve stored field study observations."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.get_field_observations(limit=limit, offset=offset)


def get_field_observation_by_domain(
    domain: str,
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> Optional[FieldObservation]:
    """Find a field study observation by normalized domain."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.get_field_observation_by_domain(domain)


def get_field_observation_by_id(
    obs_id: int,
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> Optional[FieldObservation]:
    """Find a field study observation by primary key ID."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.get_field_observation_by_id(obs_id)


def delete_field_observation(
    obs_id: int,
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> bool:
    """Delete a single field study observation by ID."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.delete_field_observation(obs_id)


def delete_field_observations_batch(
    obs_ids: List[int],
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> int:
    """Delete multiple field study observations by ID."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.delete_field_observations_batch(obs_ids)


def clear_field_study(
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
) -> bool:
    """Clear all field study observations."""
    repo = get_repository(db_path=db_path, database_url=database_url)
    return repo.clear_field_study()


def get_db_status() -> Dict[str, Any]:
    """Return health and storage engine status for telemetry reporting."""
    repo = get_repository()
    return repo.get_health_status()


def migrate_historical_to_field_study(
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
    force: bool = False,
) -> int:
    """
    Backfill unique domain lookups from lookup_history into field_study_observations
    ONLY if explicitly requested via force=True.
    Default is disabled to preserve clean live user search state.
    """
    if not force:
        return 0

    init_db(db_path=db_path, database_url=database_url)
    existing_obs = get_field_observations(db_path=db_path, database_url=database_url)
    if existing_obs:
        return 0

    history_records = get_lookup_history(db_path=db_path, database_url=database_url)
    if not history_records:
        return 0

    category_map: dict = {}
    try:
        from backend.services.field_test_service import load_test_websites
        websites = load_test_websites()
        category_map = {w["domain"]: w["category"] for w in websites}
    except Exception:
        pass

    seen_domains: set = set()
    inserted_count = 0
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
            country_code=rec.country_code or "N/A",
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
            timezone=rec.timezone or "N/A",
            error_message=rec.error_message,
        )
        saved_id = save_field_observation(obs, db_path=db_path, database_url=database_url)
        if saved_id is not None:
            inserted_count += 1

    return inserted_count
