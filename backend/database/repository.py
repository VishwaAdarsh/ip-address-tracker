"""
Database Repository Abstraction for IP PULSE Platform.

Supports:
- Local Development & Testing: SQLite with WAL mode, foreign keys, and safe migrations.
- Production Deployment: PostgreSQL / Supabase with connection pooling, automatic reconnection,
  and identical query semantics.
"""
from abc import ABC, abstractmethod
import contextlib
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.config.settings import BASE_DIR, DATABASE_URL, IS_POSTGRES, SQLITE_DB_PATH
from backend.models.models import FieldObservation, LookupRecord

logger = logging.getLogger(__name__)


def _extract_lookup_fields(result: Any) -> Dict[str, Any]:
    """Helper to extract normalized lookup fields from any lookup result structure."""
    if hasattr(result, "base_lookup"):
        # FullIntelligenceResult
        base = result.base_lookup
        sec = getattr(result, "security", None)
        intel = getattr(result, "ip_intel", None)
        risk = getattr(result, "risk", None)
    else:
        base = result
        sec = getattr(result, "security", None)
        intel = getattr(result, "ip_intel", None)
        risk = getattr(result, "risk", None)

    # Base attributes
    if isinstance(base, dict):
        timestamp = base.get("timestamp", "")
        input_value = base.get("input", base.get("input_value", ""))
        input_type = base.get("input_type", "")
        domain = base.get("domain", base.get("normalized_input", ""))
        ip_address = base.get("ip_address", base.get("selected_ip", ""))
        ip_version = base.get("ip_version", "IPv4")
        country = base.get("country", "Unknown")
        country_code = base.get("country_code", "N/A")
        region = base.get("region", "Unknown")
        city = base.get("city", "Unknown")
        latitude = base.get("latitude")
        longitude = base.get("longitude")
        timezone = base.get("timezone", "N/A")
        organization = base.get("organization", "Unknown")
        isp = base.get("isp", "Unknown")
        asn = base.get("asn", "Unknown")
        dns_response_time_ms = float(base.get("dns_response_time_ms", 0.0) or 0.0)
        api_response_time_ms = float(base.get("api_response_time_ms", 0.0) or 0.0)
        status = base.get("status", base.get("overall_status", "UNKNOWN"))
        error_message = base.get("error_message")
        postal = base.get("postal", "N/A")
        provider = base.get("provider", "Unknown")
        retrieved_at = base.get("retrieved_at", "")
        is_anycast = base.get("is_anycast", False)
    elif isinstance(base, LookupRecord):
        timestamp = base.timestamp
        input_value = base.input_value
        input_type = base.input_type
        domain = base.domain
        ip_address = base.ip_address
        ip_version = base.ip_version
        country = base.country
        country_code = base.country_code
        region = base.region
        city = base.city
        latitude = base.latitude
        longitude = base.longitude
        timezone = base.timezone
        organization = base.organization
        isp = base.isp
        asn = base.asn
        dns_response_time_ms = float(base.dns_response_time_ms or 0.0)
        api_response_time_ms = float(base.api_response_time_ms or 0.0)
        status = base.status
        error_message = base.error_message
        postal = getattr(base, "postal", "N/A") or "N/A"
        provider = getattr(base, "provider", "Unknown") or "Unknown"
        retrieved_at = getattr(base, "retrieved_at", "") or ""
        is_anycast = getattr(base, "is_anycast", False) or False
    else:
        # LookupResult object
        timestamp = getattr(base, "timestamp", "")
        input_value = getattr(base, "input", "")
        input_type = getattr(base, "input_type", "")
        domain = (
            getattr(base, "normalized_input", "")
            if input_type == "DOMAIN"
            else (getattr(base, "normalized_input", "") if getattr(base, "selected_ip", None) else "")
        )
        ip_address = getattr(base, "selected_ip", "") or ""
        ip_version = getattr(base, "ip_version", "IPv4")
        country = getattr(base, "country", "Unknown")
        country_code = getattr(base, "country_code", "N/A")
        region = getattr(base, "region", "Unknown")
        city = getattr(base, "city", "Unknown")
        latitude = getattr(base, "latitude", None)
        longitude = getattr(base, "longitude", None)
        timezone = getattr(base, "timezone", "N/A")
        organization = getattr(base, "organization", "Unknown")
        isp = getattr(base, "isp", "Unknown")
        asn = getattr(base, "asn", "Unknown")
        dns_response_time_ms = float(getattr(base, "dns_response_time_ms", 0.0) or 0.0)
        api_response_time_ms = float(getattr(base, "api_response_time_ms", 0.0) or 0.0)
        overall_status = getattr(base, "overall_status", "UNKNOWN")
        status = overall_status.value if hasattr(overall_status, "value") else str(overall_status)
        error_message = getattr(base, "error_message", None)
        postal = getattr(base, "postal", "N/A") or "N/A"
        provider = getattr(base, "provider", "Unknown") or "Unknown"
        retrieved_at = getattr(base, "retrieved_at", "") or ""
        is_anycast = getattr(base, "is_anycast", False) or False

    # Rich attributes
    infrastructure = "Unknown"
    vpn_status = "Unknown"
    proxy_status = "Unknown"
    tor_status = "Unknown"
    if intel:
        infrastructure = getattr(intel, "infrastructure_type", "Unknown") or "Unknown"
        vpn_status = getattr(intel, "vpn_status", "Unknown") or "Unknown"
        proxy_status = getattr(intel, "proxy_status", "Unknown") or "Unknown"
        tor_status = getattr(intel, "tor_status", "Unknown") or "Unknown"
    elif hasattr(base, "infrastructure") and getattr(base, "infrastructure"):
        infrastructure = getattr(base, "infrastructure")
        vpn_status = getattr(base, "vpn_status", "Unknown")
        proxy_status = getattr(base, "proxy_status", "Unknown")
        tor_status = getattr(base, "tor_status", "Unknown")

    https_status = "Unknown"
    tls_status = "Unknown"
    if sec:
        https_status = "Enabled" if getattr(sec, "https_enabled", False) else "Disabled"
        tls_status = "Valid" if getattr(sec, "ssl_valid", getattr(sec, "certificate_valid", False)) else "Invalid"
    elif hasattr(base, "https_status") and getattr(base, "https_status"):
        https_status = getattr(base, "https_status")
        tls_status = getattr(base, "tls_status", "Unknown")

    trust_score = None
    trust_classification = "Unknown"
    risk_score = None
    risk_classification = "Unknown"
    confidence = "Unknown"
    evidence_coverage = None
    if risk:
        trust_score = getattr(risk, "trust_score", None)
        risk_score = getattr(risk, "risk_score", None)
        trust_classification = getattr(risk, "trust_classification", getattr(risk, "risk_category", "Unknown"))
        risk_classification = getattr(risk, "risk_classification", getattr(risk, "risk_level", "Unknown"))
        confidence = getattr(risk, "confidence_rating", "Unknown")
        evidence_coverage = getattr(risk, "confidence_score", None)
    elif hasattr(base, "trust_score"):
        trust_score = getattr(base, "trust_score", None)
        trust_classification = getattr(base, "trust_classification", "Unknown")
        risk_score = getattr(base, "risk_score", None)
        risk_classification = getattr(base, "risk_classification", "Unknown")
        confidence = getattr(base, "confidence", "Unknown")
        evidence_coverage = getattr(base, "evidence_coverage", None)

    return {
        "timestamp": timestamp,
        "input_value": input_value,
        "input_type": input_type,
        "domain": domain or "",
        "ip_address": ip_address or "",
        "ip_version": ip_version or "N/A",
        "country": country or "N/A",
        "country_code": country_code or "N/A",
        "region": region or "N/A",
        "city": city or "N/A",
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone or "N/A",
        "organization": organization or "N/A",
        "isp": isp or "N/A",
        "asn": asn or "N/A",
        "dns_response_time_ms": dns_response_time_ms,
        "api_response_time_ms": api_response_time_ms,
        "status": status or "",
        "error_message": error_message,
        "infrastructure": infrastructure,
        "vpn_status": vpn_status,
        "proxy_status": proxy_status,
        "tor_status": tor_status,
        "https_status": https_status,
        "tls_status": tls_status,
        "trust_score": trust_score,
        "trust_classification": trust_classification,
        "risk_score": risk_score,
        "risk_classification": risk_classification,
        "confidence": confidence,
        "evidence_coverage": evidence_coverage,
        "postal": postal or "N/A",
        "provider": provider or "Unknown",
        "retrieved_at": retrieved_at or "",
        "is_anycast": bool(is_anycast),
    }


class BaseDatabaseRepository(ABC):
    """Abstract base repository for database operations."""

    @abstractmethod
    def init_schema(self) -> None:
        """Initialize database schema and apply safe schema migrations."""
        pass

    @abstractmethod
    def save_lookup(self, result: Any) -> Optional[int]:
        """Save a completed lookup record to the database."""
        pass

    @abstractmethod
    def get_lookup_history(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[LookupRecord]:
        """Retrieve stored lookup records, newest first."""
        pass

    @abstractmethod
    def delete_lookup(self, record_id: int) -> bool:
        """Delete a single lookup record by stable ID."""
        pass

    @abstractmethod
    def delete_lookups_batch(self, record_ids: List[int]) -> int:
        """Delete multiple lookup records by their stable IDs."""
        pass

    @abstractmethod
    def clear_history(self) -> bool:
        """Clear all stored lookup records."""
        pass

    @abstractmethod
    def save_field_observation(
        self, obs: FieldObservation, update_if_exists: bool = False
    ) -> Optional[int]:
        """Save a structured field study observation."""
        pass

    @abstractmethod
    def get_field_observations(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[FieldObservation]:
        """Retrieve stored field study observations."""
        pass

    @abstractmethod
    def get_field_observation_by_domain(self, domain: str) -> Optional[FieldObservation]:
        """Find a field study observation by normalized domain."""
        pass

    @abstractmethod
    def get_field_observation_by_id(self, obs_id: int) -> Optional[FieldObservation]:
        """Find a field study observation by primary key ID."""
        pass

    @abstractmethod
    def delete_field_observation(self, obs_id: int) -> bool:
        """Delete a single field study observation by ID."""
        pass

    @abstractmethod
    def delete_field_observations_batch(self, obs_ids: List[int]) -> int:
        """Delete multiple field study observations by ID."""
        pass

    @abstractmethod
    def clear_field_study(self) -> bool:
        """Clear all field study observations."""
        pass

    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Check connection health and return metadata."""
        pass

    def close(self) -> None:
        """Close connections or cleanup resources."""
        pass


class SQLiteRepository(BaseDatabaseRepository):
    """Local SQLite Database Repository implementation."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(SQLITE_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        """Close connections or cleanup resources."""
        pass

    @contextlib.contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        try:
            yield conn
        finally:
            conn.close()

    def init_schema(self) -> None:
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
            error_message TEXT,
            infrastructure TEXT DEFAULT 'Unknown',
            vpn_status TEXT DEFAULT 'Unknown',
            proxy_status TEXT DEFAULT 'Unknown',
            tor_status TEXT DEFAULT 'Unknown',
            https_status TEXT DEFAULT 'Unknown',
            tls_status TEXT DEFAULT 'Unknown',
            trust_score REAL,
            trust_classification TEXT DEFAULT 'Unknown',
            risk_score REAL,
            risk_classification TEXT DEFAULT 'Unknown',
            confidence TEXT DEFAULT 'Unknown',
            evidence_coverage REAL,
            postal TEXT DEFAULT 'N/A',
            provider TEXT DEFAULT 'Unknown',
            retrieved_at TEXT,
            is_anycast INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS field_study_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER,
            domain TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT 'General Web',
            resolved_ip TEXT,
            ip_version TEXT DEFAULT 'IPv4',
            country TEXT DEFAULT 'Unknown',
            country_code TEXT DEFAULT 'N/A',
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
            timezone TEXT DEFAULT 'N/A',
            error_message TEXT,
            searched_by TEXT DEFAULT 'Anonymous',
            postal TEXT DEFAULT 'N/A',
            provider TEXT DEFAULT 'Unknown',
            retrieved_at TEXT,
            is_anycast INTEGER DEFAULT 0
        );
        """
        with self._connection() as conn:
            conn.executescript(schema_sql)

            # Idempotent column migrations
            columns_to_add = [
                ("lookup_history", "infrastructure", "TEXT DEFAULT 'Unknown'"),
                ("lookup_history", "vpn_status", "TEXT DEFAULT 'Unknown'"),
                ("lookup_history", "proxy_status", "TEXT DEFAULT 'Unknown'"),
                ("lookup_history", "tor_status", "TEXT DEFAULT 'Unknown'"),
                ("lookup_history", "https_status", "TEXT DEFAULT 'Unknown'"),
                ("lookup_history", "tls_status", "TEXT DEFAULT 'Unknown'"),
                ("lookup_history", "trust_score", "REAL"),
                ("lookup_history", "trust_classification", "TEXT DEFAULT 'Unknown'"),
                ("lookup_history", "risk_score", "REAL"),
                ("lookup_history", "risk_classification", "TEXT DEFAULT 'Unknown'"),
                ("lookup_history", "confidence", "TEXT DEFAULT 'Unknown'"),
                ("lookup_history", "evidence_coverage", "REAL"),
                ("lookup_history", "postal", "TEXT DEFAULT 'N/A'"),
                ("lookup_history", "provider", "TEXT DEFAULT 'Unknown'"),
                ("lookup_history", "retrieved_at", "TEXT"),
                ("lookup_history", "is_anycast", "INTEGER DEFAULT 0"),
                ("field_study_observations", "country_code", "TEXT DEFAULT 'N/A'"),
                ("field_study_observations", "timezone", "TEXT DEFAULT 'N/A'"),
                ("field_study_observations", "searched_by", "TEXT DEFAULT 'Anonymous'"),
                ("field_study_observations", "postal", "TEXT DEFAULT 'N/A'"),
                ("field_study_observations", "provider", "TEXT DEFAULT 'Unknown'"),
                ("field_study_observations", "retrieved_at", "TEXT"),
                ("field_study_observations", "is_anycast", "INTEGER DEFAULT 0"),
            ]
            for tbl, col, col_def in columns_to_add:
                try:
                    conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def};")
                except sqlite3.OperationalError:
                    pass
            conn.commit()

    def save_lookup(self, result: Any) -> Optional[int]:
        self.init_schema()
        f = _extract_lookup_fields(result)
        insert_sql = """
        INSERT INTO lookup_history (
            timestamp, input_value, input_type, domain, ip_address, ip_version,
            country, country_code, region, city, latitude, longitude, timezone,
            organization, isp, asn, dns_response_time_ms, api_response_time_ms,
            status, error_message, infrastructure, vpn_status, proxy_status,
            tor_status, https_status, tls_status, trust_score,
            trust_classification, risk_score, risk_classification,
            confidence, evidence_coverage, postal, provider, retrieved_at, is_anycast
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?, ?, ?
        );
        """
        params = (
            f["timestamp"], f["input_value"], f["input_type"], f["domain"], f["ip_address"], f["ip_version"],
            f["country"], f["country_code"], f["region"], f["city"], f["latitude"], f["longitude"], f["timezone"],
            f["organization"], f["isp"], f["asn"], f["dns_response_time_ms"], f["api_response_time_ms"],
            f["status"], f["error_message"], f["infrastructure"], f["vpn_status"], f["proxy_status"],
            f["tor_status"], f["https_status"], f["tls_status"], f["trust_score"],
            f["trust_classification"], f["risk_score"], f["risk_classification"],
            f["confidence"], f["evidence_coverage"],
            f["postal"], f["provider"], f["retrieved_at"], 1 if f["is_anycast"] else 0
        )
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_sql, params)
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to save lookup result to SQLite: {e}")
            return None

    def get_lookup_history(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[LookupRecord]:
        self.init_schema()
        query_sql = "SELECT * FROM lookup_history ORDER BY timestamp DESC, id DESC"
        params: list = []
        if limit is not None:
            query_sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        records: List[LookupRecord] = []
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query_sql, params)
                rows = cursor.fetchall()
                for row in rows:
                    keys = row.keys()
                    rec = LookupRecord(
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
                        infrastructure=row["infrastructure"] if "infrastructure" in keys and row["infrastructure"] else "Unknown",
                        vpn_status=row["vpn_status"] if "vpn_status" in keys and row["vpn_status"] else "Unknown",
                        proxy_status=row["proxy_status"] if "proxy_status" in keys and row["proxy_status"] else "Unknown",
                        tor_status=row["tor_status"] if "tor_status" in keys and row["tor_status"] else "Unknown",
                        https_status=row["https_status"] if "https_status" in keys and row["https_status"] else "Unknown",
                        tls_status=row["tls_status"] if "tls_status" in keys and row["tls_status"] else "Unknown",
                        trust_score=row["trust_score"] if "trust_score" in keys else None,
                        trust_classification=row["trust_classification"] if "trust_classification" in keys and row["trust_classification"] else "Unknown",
                        risk_score=row["risk_score"] if "risk_score" in keys else None,
                        risk_classification=row["risk_classification"] if "risk_classification" in keys and row["risk_classification"] else "Unknown",
                        confidence=row["confidence"] if "confidence" in keys and row["confidence"] else "Unknown",
                        evidence_coverage=row["evidence_coverage"] if "evidence_coverage" in keys else None,
                        postal=row["postal"] if "postal" in keys and row["postal"] else "N/A",
                        provider=row["provider"] if "provider" in keys and row["provider"] else "Unknown",
                        retrieved_at=row["retrieved_at"] if "retrieved_at" in keys else None,
                        is_anycast=bool(row["is_anycast"]) if "is_anycast" in keys and row["is_anycast"] is not None else False,
                    )
                    records.append(rec)
        except Exception as e:
            logger.error(f"Failed to retrieve lookup history from SQLite: {e}")
        return records

    def delete_lookup(self, record_id: int) -> bool:
        self.init_schema()
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM lookup_history WHERE id = ?;", (record_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete lookup #{record_id} in SQLite: {e}")
            return False

    def delete_lookups_batch(self, record_ids: List[int]) -> int:
        if not record_ids:
            return 0
        self.init_schema()
        placeholders = ",".join(["?"] * len(record_ids))
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM lookup_history WHERE id IN ({placeholders});", record_ids)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to batch delete lookups in SQLite: {e}")
            return 0

    def clear_history(self) -> bool:
        self.init_schema()
        try:
            with self._connection() as conn:
                conn.execute("DELETE FROM lookup_history;")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to clear history in SQLite: {e}")
            return False

    def save_field_observation(
        self, obs: FieldObservation, update_if_exists: bool = False
    ) -> Optional[int]:
        self.init_schema()
        clean_dom = obs.domain.strip().lower()

        if update_if_exists:
            try:
                with self._connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM field_study_observations WHERE domain = ?;", (clean_dom,))
                    existing = cursor.fetchone()
                    if existing:
                        update_sql = """
                        UPDATE field_study_observations SET
                            category = ?, resolved_ip = ?, ip_version = ?,
                            country = ?, country_code = ?, region = ?, city = ?, latitude = ?, longitude = ?,
                            geolocation_confidence = ?, asn = ?, organization = ?, isp = ?,
                            network_type = ?, infrastructure_type = ?, https_status = ?, tls_status = ?,
                            vpn_status = ?, proxy_status = ?, tor_status = ?,
                            website_trust_score = ?, website_trust_classification = ?,
                            ip_risk_score = ?, ip_risk_classification = ?, score_confidence = ?, evidence_coverage = ?,
                            observation_status = ?, observed_at = ?, raw_history_id = ?,
                            dns_response_time_ms = ?, api_response_time_ms = ?, timezone = ?, error_message = ?,
                            searched_by = ?, postal = ?, provider = ?, retrieved_at = ?, is_anycast = ?
                        WHERE id = ?;
                        """
                        params = (
                            obs.category or "General Web", obs.resolved_ip or "", obs.ip_version or "IPv4",
                            obs.country or "Unknown", obs.country_code or "N/A", obs.region or "Unknown", obs.city or "Unknown",
                            obs.latitude, obs.longitude, obs.geolocation_confidence or "Unknown",
                            obs.asn or "Unknown", obs.organization or "Unknown", obs.isp or "Unknown",
                            obs.network_type or "Unknown", obs.infrastructure_type or "Unknown",
                            obs.https_status or "Unknown", obs.tls_status or "Unknown",
                            obs.vpn_status or "Unknown", obs.proxy_status or "Unknown", obs.tor_status or "Unknown",
                            obs.website_trust_score, obs.website_trust_classification or "Unknown",
                            obs.ip_risk_score, obs.ip_risk_classification or "Unknown",
                            obs.score_confidence or "Unknown", obs.evidence_coverage,
                            obs.observation_status or "RECORDED", obs.observed_at, obs.raw_history_id,
                            obs.dns_response_time_ms or 0.0, obs.api_response_time_ms or 0.0,
                            obs.timezone or "N/A", obs.error_message,
                            getattr(obs, "searched_by", "Anonymous") or "Anonymous",
                            obs.postal or "N/A", obs.provider or "Unknown", obs.retrieved_at, 1 if obs.is_anycast else 0,
                            existing["id"]
                        )
                        cursor.execute(update_sql, params)
                        conn.commit()
                        return existing["id"]
            except Exception as e:
                logger.error(f"Failed to update field observation in SQLite: {e}")

        insert_sql = """
        INSERT INTO field_study_observations (
            test_id, domain, category, resolved_ip, ip_version,
            country, country_code, region, city, latitude, longitude, geolocation_confidence,
            asn, organization, isp, network_type, infrastructure_type,
            https_status, tls_status, vpn_status, proxy_status, tor_status,
            website_trust_score, website_trust_classification,
            ip_risk_score, ip_risk_classification, score_confidence, evidence_coverage,
            observation_status, observed_at, raw_history_id,
            dns_response_time_ms, api_response_time_ms, timezone, error_message, searched_by,
            postal, provider, retrieved_at, is_anycast
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?
        );
        """
        params = (
            obs.test_id, clean_dom, obs.category or "General Web", obs.resolved_ip or "", obs.ip_version or "IPv4",
            obs.country or "Unknown", obs.country_code or "N/A", obs.region or "Unknown", obs.city or "Unknown",
            obs.latitude, obs.longitude, obs.geolocation_confidence or "Unknown",
            obs.asn or "Unknown", obs.organization or "Unknown", obs.isp or "Unknown",
            obs.network_type or "Unknown", obs.infrastructure_type or "Unknown",
            obs.https_status or "Unknown", obs.tls_status or "Unknown",
            obs.vpn_status or "Unknown", obs.proxy_status or "Unknown", obs.tor_status or "Unknown",
            obs.website_trust_score, obs.website_trust_classification or "Unknown",
            obs.ip_risk_score, obs.ip_risk_classification or "Unknown",
            obs.score_confidence or "Unknown", obs.evidence_coverage,
            obs.observation_status or "RECORDED", obs.observed_at, obs.raw_history_id,
            obs.dns_response_time_ms or 0.0, obs.api_response_time_ms or 0.0,
            obs.timezone or "N/A", obs.error_message,
            getattr(obs, "searched_by", "Anonymous") or "Anonymous",
            obs.postal or "N/A", obs.provider or "Unknown", obs.retrieved_at, 1 if obs.is_anycast else 0
        )
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_sql, params)
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError as ie:
            logger.warning(f"Duplicate domain rejected for field study in SQLite: {clean_dom} ({ie})")
            return None
        except Exception as e:
            logger.error(f"Failed to save field observation in SQLite: {e}")
            return None

    def _row_to_field_observation(self, row: sqlite3.Row) -> FieldObservation:
        keys = row.keys()
        return FieldObservation(
            id=row["id"],
            test_id=row["test_id"] or 0,
            domain=row["domain"] or "",
            category=row["category"] or "General Web",
            resolved_ip=row["resolved_ip"] or "",
            ip_version=row["ip_version"] or "IPv4",
            country=row["country"] or "Unknown",
            country_code=row["country_code"] if "country_code" in keys and row["country_code"] else "N/A",
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
            searched_by=row["searched_by"] if "searched_by" in keys and row["searched_by"] else "Anonymous",
            observation_status=row["observation_status"] or "RECORDED",
            observed_at=row["observed_at"] or "",
            raw_history_id=row["raw_history_id"],
            dns_response_time_ms=row["dns_response_time_ms"] or 0.0,
            api_response_time_ms=row["api_response_time_ms"] or 0.0,
            timezone=row["timezone"] if "timezone" in keys and row["timezone"] else "N/A",
            error_message=row["error_message"],
            postal=row["postal"] if "postal" in keys and row["postal"] else "N/A",
            provider=row["provider"] if "provider" in keys and row["provider"] else "Unknown",
            retrieved_at=row["retrieved_at"] if "retrieved_at" in keys else None,
            is_anycast=bool(row["is_anycast"]) if "is_anycast" in keys and row["is_anycast"] is not None else False,
        )

    def get_field_observations(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[FieldObservation]:
        self.init_schema()
        query_sql = "SELECT * FROM field_study_observations ORDER BY test_id ASC, id ASC"
        params: list = []
        if limit is not None:
            query_sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        observations: List[FieldObservation] = []
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query_sql, params)
                for r in cursor.fetchall():
                    observations.append(self._row_to_field_observation(r))
        except Exception as e:
            logger.error(f"Failed to retrieve field observations from SQLite: {e}")
        return observations

    def get_field_observation_by_domain(self, domain: str) -> Optional[FieldObservation]:
        self.init_schema()
        clean_dom = domain.strip().lower()
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM field_study_observations WHERE domain = ? LIMIT 1;",
                    (clean_dom,),
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_field_observation(row)
        except Exception as e:
            logger.error(f"Failed to fetch field observation for {domain} in SQLite: {e}")
        return None

    def get_field_observation_by_id(self, obs_id: int) -> Optional[FieldObservation]:
        self.init_schema()
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM field_study_observations WHERE id = ? LIMIT 1;",
                    (obs_id,),
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_field_observation(row)
        except Exception as e:
            logger.error(f"Failed to fetch field observation #{obs_id} in SQLite: {e}")
        return None

    def delete_field_observation(self, obs_id: int) -> bool:
        self.init_schema()
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM field_study_observations WHERE id = ?;", (obs_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete field observation #{obs_id} in SQLite: {e}")
            return False

    def delete_field_observations_batch(self, obs_ids: List[int]) -> int:
        if not obs_ids:
            return 0
        self.init_schema()
        placeholders = ",".join(["?"] * len(obs_ids))
        try:
            with self._connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"DELETE FROM field_study_observations WHERE id IN ({placeholders});",
                    obs_ids,
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to batch delete field observations in SQLite: {e}")
            return 0

    def clear_field_study(self) -> bool:
        self.init_schema()
        try:
            with self._connection() as conn:
                conn.execute("DELETE FROM field_study_observations;")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to clear field study in SQLite: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "type": "sqlite",
            "connected": self.db_path.exists(),
            "location": str(self.db_path),
            "persistent_storage": False,
        }


class PostgresRepository(BaseDatabaseRepository):
    """Production PostgreSQL Database Repository (Render / Supabase / Neon)."""

    def __init__(self, connection_url: Optional[str] = None):
        raw_url = (connection_url or DATABASE_URL).strip()
        # Normalize postgres:// to postgresql:// for compatibility
        if raw_url.startswith("postgres://"):
            raw_url = "postgresql://" + raw_url[len("postgres://"):]
        self.connection_url = raw_url

    @contextlib.contextmanager
    def _connection(self):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        # Supabase / cloud postgres typically require SSL
        conn = psycopg2.connect(
            self.connection_url,
            cursor_factory=RealDictCursor,
            connect_timeout=10,
        )
        conn.autocommit = False
        try:
            yield conn
        finally:
            conn.close()

    def init_schema(self) -> None:
        schema_sql = """
        CREATE TABLE IF NOT EXISTS lookup_history (
            id SERIAL PRIMARY KEY,
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
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            timezone TEXT,
            organization TEXT,
            isp TEXT,
            asn TEXT,
            dns_response_time_ms DOUBLE PRECISION,
            api_response_time_ms DOUBLE PRECISION,
            status TEXT NOT NULL,
            error_message TEXT,
            infrastructure TEXT DEFAULT 'Unknown',
            vpn_status TEXT DEFAULT 'Unknown',
            proxy_status TEXT DEFAULT 'Unknown',
            tor_status TEXT DEFAULT 'Unknown',
            https_status TEXT DEFAULT 'Unknown',
            tls_status TEXT DEFAULT 'Unknown',
            trust_score DOUBLE PRECISION,
            trust_classification TEXT DEFAULT 'Unknown',
            risk_score DOUBLE PRECISION,
            risk_classification TEXT DEFAULT 'Unknown',
            confidence TEXT DEFAULT 'Unknown',
            evidence_coverage DOUBLE PRECISION,
            postal TEXT DEFAULT 'N/A',
            provider TEXT DEFAULT 'Unknown',
            retrieved_at TEXT,
            is_anycast BOOLEAN DEFAULT FALSE
        );

        CREATE TABLE IF NOT EXISTS field_study_observations (
            id SERIAL PRIMARY KEY,
            test_id INTEGER,
            domain TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT 'General Web',
            resolved_ip TEXT,
            ip_version TEXT DEFAULT 'IPv4',
            country TEXT DEFAULT 'Unknown',
            country_code TEXT DEFAULT 'N/A',
            region TEXT DEFAULT 'Unknown',
            city TEXT DEFAULT 'Unknown',
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
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
            website_trust_score DOUBLE PRECISION,
            website_trust_classification TEXT DEFAULT 'Unknown',
            ip_risk_score DOUBLE PRECISION,
            ip_risk_classification TEXT DEFAULT 'Unknown',
            score_confidence TEXT DEFAULT 'Unknown',
            evidence_coverage DOUBLE PRECISION,
            observation_status TEXT DEFAULT 'RECORDED',
            observed_at TEXT NOT NULL,
            raw_history_id INTEGER,
            dns_response_time_ms DOUBLE PRECISION DEFAULT 0.0,
            api_response_time_ms DOUBLE PRECISION DEFAULT 0.0,
            timezone TEXT DEFAULT 'N/A',
            error_message TEXT,
            searched_by TEXT DEFAULT 'Anonymous',
            postal TEXT DEFAULT 'N/A',
            provider TEXT DEFAULT 'Unknown',
            retrieved_at TEXT,
            is_anycast BOOLEAN DEFAULT FALSE
        );
        """
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
                    # Safe migrations
                    migrations = [
                        ("lookup_history", "infrastructure", "TEXT DEFAULT 'Unknown'"),
                        ("lookup_history", "vpn_status", "TEXT DEFAULT 'Unknown'"),
                        ("lookup_history", "proxy_status", "TEXT DEFAULT 'Unknown'"),
                        ("lookup_history", "tor_status", "TEXT DEFAULT 'Unknown'"),
                        ("lookup_history", "https_status", "TEXT DEFAULT 'Unknown'"),
                        ("lookup_history", "tls_status", "TEXT DEFAULT 'Unknown'"),
                        ("lookup_history", "trust_score", "DOUBLE PRECISION"),
                        ("lookup_history", "trust_classification", "TEXT DEFAULT 'Unknown'"),
                        ("lookup_history", "risk_score", "DOUBLE PRECISION"),
                        ("lookup_history", "risk_classification", "TEXT DEFAULT 'Unknown'"),
                        ("lookup_history", "confidence", "TEXT DEFAULT 'Unknown'"),
                        ("lookup_history", "evidence_coverage", "DOUBLE PRECISION"),
                        ("lookup_history", "postal", "TEXT DEFAULT 'N/A'"),
                        ("lookup_history", "provider", "TEXT DEFAULT 'Unknown'"),
                        ("lookup_history", "retrieved_at", "TEXT"),
                        ("lookup_history", "is_anycast", "BOOLEAN DEFAULT FALSE"),
                        ("field_study_observations", "country_code", "TEXT DEFAULT 'N/A'"),
                        ("field_study_observations", "timezone", "TEXT DEFAULT 'N/A'"),
                        ("field_study_observations", "searched_by", "TEXT DEFAULT 'Anonymous'"),
                        ("field_study_observations", "postal", "TEXT DEFAULT 'N/A'"),
                        ("field_study_observations", "provider", "TEXT DEFAULT 'Unknown'"),
                        ("field_study_observations", "retrieved_at", "TEXT"),
                        ("field_study_observations", "is_anycast", "BOOLEAN DEFAULT FALSE"),
                    ]
                    for tbl, col, col_def in migrations:
                        cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS {col} {col_def};")
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
            raise

    def save_lookup(self, result: Any) -> Optional[int]:
        self.init_schema()
        f = _extract_lookup_fields(result)
        insert_sql = """
        INSERT INTO lookup_history (
            timestamp, input_value, input_type, domain, ip_address, ip_version,
            country, country_code, region, city, latitude, longitude, timezone,
            organization, isp, asn, dns_response_time_ms, api_response_time_ms,
            status, error_message, infrastructure, vpn_status, proxy_status,
            tor_status, https_status, tls_status, trust_score,
            trust_classification, risk_score, risk_classification,
            confidence, evidence_coverage, postal, provider, retrieved_at, is_anycast
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        ) RETURNING id;
        """
        params = (
            f["timestamp"], f["input_value"], f["input_type"], f["domain"], f["ip_address"], f["ip_version"],
            f["country"], f["country_code"], f["region"], f["city"], f["latitude"], f["longitude"], f["timezone"],
            f["organization"], f["isp"], f["asn"], f["dns_response_time_ms"], f["api_response_time_ms"],
            f["status"], f["error_message"], f["infrastructure"], f["vpn_status"], f["proxy_status"],
            f["tor_status"], f["https_status"], f["tls_status"], f["trust_score"],
            f["trust_classification"], f["risk_score"], f["risk_classification"],
            f["confidence"], f["evidence_coverage"],
            f["postal"], f["provider"], f["retrieved_at"], bool(f["is_anycast"])
        )
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(insert_sql, params)
                    row = cursor.fetchone()
                    conn.commit()
                    return row["id"] if row else None
        except Exception as e:
            logger.error(f"Failed to save lookup result to PostgreSQL: {e}")
            return None

    def get_lookup_history(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[LookupRecord]:
        self.init_schema()
        query_sql = "SELECT * FROM lookup_history ORDER BY timestamp DESC, id DESC"
        params: list = []
        if limit is not None:
            query_sql += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

        records: List[LookupRecord] = []
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query_sql, params)
                    rows = cursor.fetchall()
                    for r in rows:
                        rec = LookupRecord(
                            id=r["id"],
                            timestamp=r["timestamp"],
                            input_value=r["input_value"],
                            input_type=r["input_type"],
                            domain=r["domain"] or "",
                            ip_address=r["ip_address"] or "",
                            ip_version=r["ip_version"] or "N/A",
                            country=r["country"] or "N/A",
                            country_code=r["country_code"] or "N/A",
                            region=r["region"] or "N/A",
                            city=r["city"] or "N/A",
                            latitude=r["latitude"],
                            longitude=r["longitude"],
                            timezone=r["timezone"] or "N/A",
                            organization=r["organization"] or "N/A",
                            isp=r["isp"] or "N/A",
                            asn=r["asn"] or "N/A",
                            dns_response_time_ms=r["dns_response_time_ms"] or 0.0,
                            api_response_time_ms=r["api_response_time_ms"] or 0.0,
                            status=r["status"] or "",
                            error_message=r["error_message"],
                            infrastructure=r.get("infrastructure") or "Unknown",
                            vpn_status=r.get("vpn_status") or "Unknown",
                            proxy_status=r.get("proxy_status") or "Unknown",
                            tor_status=r.get("tor_status") or "Unknown",
                            https_status=r.get("https_status") or "Unknown",
                            tls_status=r.get("tls_status") or "Unknown",
                            trust_score=r.get("trust_score"),
                            trust_classification=r.get("trust_classification") or "Unknown",
                            risk_score=r.get("risk_score"),
                            risk_classification=r.get("risk_classification") or "Unknown",
                            confidence=r.get("confidence") or "Unknown",
                            evidence_coverage=r.get("evidence_coverage"),
                            postal=r.get("postal") or "N/A",
                            provider=r.get("provider") or "Unknown",
                            retrieved_at=r.get("retrieved_at"),
                            is_anycast=bool(r.get("is_anycast", False)),
                        )
                        records.append(rec)
        except Exception as e:
            logger.error(f"Failed to retrieve lookup history from PostgreSQL: {e}")
        return records

    def delete_lookup(self, record_id: int) -> bool:
        self.init_schema()
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM lookup_history WHERE id = %s;", (record_id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete lookup #{record_id} in PostgreSQL: {e}")
            return False

    def delete_lookups_batch(self, record_ids: List[int]) -> int:
        if not record_ids:
            return 0
        self.init_schema()
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM lookup_history WHERE id = ANY(%s);", (record_ids,))
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to batch delete lookups in PostgreSQL: {e}")
            return 0

    def clear_history(self) -> bool:
        self.init_schema()
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM lookup_history;")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to clear history in PostgreSQL: {e}")
            return False

    def save_field_observation(
        self, obs: FieldObservation, update_if_exists: bool = False
    ) -> Optional[int]:
        self.init_schema()
        clean_dom = obs.domain.strip().lower()

        if update_if_exists:
            update_sql = """
            INSERT INTO field_study_observations (
                test_id, domain, category, resolved_ip, ip_version,
                country, country_code, region, city, latitude, longitude, geolocation_confidence,
                asn, organization, isp, network_type, infrastructure_type,
                https_status, tls_status, vpn_status, proxy_status, tor_status,
                website_trust_score, website_trust_classification,
                ip_risk_score, ip_risk_classification, score_confidence, evidence_coverage,
                observation_status, observed_at, raw_history_id,
                dns_response_time_ms, api_response_time_ms, timezone, error_message, searched_by,
                postal, provider, retrieved_at, is_anycast
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (domain) DO UPDATE SET
                category = EXCLUDED.category,
                resolved_ip = EXCLUDED.resolved_ip,
                ip_version = EXCLUDED.ip_version,
                country = EXCLUDED.country,
                country_code = EXCLUDED.country_code,
                region = EXCLUDED.region,
                city = EXCLUDED.city,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                geolocation_confidence = EXCLUDED.geolocation_confidence,
                asn = EXCLUDED.asn,
                organization = EXCLUDED.organization,
                isp = EXCLUDED.isp,
                network_type = EXCLUDED.network_type,
                infrastructure_type = EXCLUDED.infrastructure_type,
                https_status = EXCLUDED.https_status,
                tls_status = EXCLUDED.tls_status,
                vpn_status = EXCLUDED.vpn_status,
                proxy_status = EXCLUDED.proxy_status,
                tor_status = EXCLUDED.tor_status,
                website_trust_score = EXCLUDED.website_trust_score,
                website_trust_classification = EXCLUDED.website_trust_classification,
                ip_risk_score = EXCLUDED.ip_risk_score,
                ip_risk_classification = EXCLUDED.ip_risk_classification,
                score_confidence = EXCLUDED.score_confidence,
                evidence_coverage = EXCLUDED.evidence_coverage,
                observation_status = EXCLUDED.observation_status,
                observed_at = EXCLUDED.observed_at,
                raw_history_id = EXCLUDED.raw_history_id,
                dns_response_time_ms = EXCLUDED.dns_response_time_ms,
                api_response_time_ms = EXCLUDED.api_response_time_ms,
                timezone = EXCLUDED.timezone,
                error_message = EXCLUDED.error_message,
                searched_by = EXCLUDED.searched_by,
                postal = EXCLUDED.postal,
                provider = EXCLUDED.provider,
                retrieved_at = EXCLUDED.retrieved_at,
                is_anycast = EXCLUDED.is_anycast
            RETURNING id;
            """
        else:
            update_sql = """
            INSERT INTO field_study_observations (
                test_id, domain, category, resolved_ip, ip_version,
                country, country_code, region, city, latitude, longitude, geolocation_confidence,
                asn, organization, isp, network_type, infrastructure_type,
                https_status, tls_status, vpn_status, proxy_status, tor_status,
                website_trust_score, website_trust_classification,
                ip_risk_score, ip_risk_classification, score_confidence, evidence_coverage,
                observation_status, observed_at, raw_history_id,
                dns_response_time_ms, api_response_time_ms, timezone, error_message, searched_by,
                postal, provider, retrieved_at, is_anycast
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            ) RETURNING id;
            """

        params = (
            obs.test_id, clean_dom, obs.category or "General Web", obs.resolved_ip or "", obs.ip_version or "IPv4",
            obs.country or "Unknown", obs.country_code or "N/A", obs.region or "Unknown", obs.city or "Unknown",
            obs.latitude, obs.longitude, obs.geolocation_confidence or "Unknown",
            obs.asn or "Unknown", obs.organization or "Unknown", obs.isp or "Unknown",
            obs.network_type or "Unknown", obs.infrastructure_type or "Unknown",
            obs.https_status or "Unknown", obs.tls_status or "Unknown",
            obs.vpn_status or "Unknown", obs.proxy_status or "Unknown", obs.tor_status or "Unknown",
            obs.website_trust_score, obs.website_trust_classification or "Unknown",
            obs.ip_risk_score, obs.ip_risk_classification or "Unknown",
            obs.score_confidence or "Unknown", obs.evidence_coverage,
            obs.observation_status or "RECORDED", obs.observed_at, obs.raw_history_id,
            obs.dns_response_time_ms or 0.0, obs.api_response_time_ms or 0.0,
            obs.timezone or "N/A", obs.error_message,
            getattr(obs, "searched_by", "Anonymous") or "Anonymous",
            obs.postal or "N/A", obs.provider or "Unknown", obs.retrieved_at, bool(obs.is_anycast)
        )
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(update_sql, params)
                    row = cursor.fetchone()
                    conn.commit()
                    return row["id"] if row else None
        except Exception as e:
            if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                logger.warning(f"Duplicate domain rejected for field study in PostgreSQL: {clean_dom}")
                return None
            logger.error(f"Failed to save field observation in PostgreSQL: {e}")
            return None

    def _dict_to_field_observation(self, r: Dict[str, Any]) -> FieldObservation:
        return FieldObservation(
            id=r["id"],
            test_id=r["test_id"] or 0,
            domain=r["domain"] or "",
            category=r["category"] or "General Web",
            resolved_ip=r["resolved_ip"] or "",
            ip_version=r["ip_version"] or "IPv4",
            country=r["country"] or "Unknown",
            country_code=r.get("country_code") or "N/A",
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
            searched_by=r.get("searched_by") or "Anonymous",
            observation_status=r["observation_status"] or "RECORDED",
            observed_at=r["observed_at"] or "",
            raw_history_id=r["raw_history_id"],
            dns_response_time_ms=r["dns_response_time_ms"] or 0.0,
            api_response_time_ms=r["api_response_time_ms"] or 0.0,
            timezone=r.get("timezone") or "N/A",
            error_message=r["error_message"],
            postal=r.get("postal") or "N/A",
            provider=r.get("provider") or "Unknown",
            retrieved_at=r.get("retrieved_at"),
            is_anycast=bool(r.get("is_anycast", False)),
        )

    def get_field_observations(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[FieldObservation]:
        self.init_schema()
        query_sql = "SELECT * FROM field_study_observations ORDER BY test_id ASC, id ASC"
        params: list = []
        if limit is not None:
            query_sql += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

        observations: List[FieldObservation] = []
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query_sql, params)
                    rows = cursor.fetchall()
                    for r in rows:
                        observations.append(self._dict_to_field_observation(r))
        except Exception as e:
            logger.error(f"Failed to retrieve field observations from PostgreSQL: {e}")
        return observations

    def get_field_observation_by_domain(self, domain: str) -> Optional[FieldObservation]:
        self.init_schema()
        clean_dom = domain.strip().lower()
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM field_study_observations WHERE domain = %s LIMIT 1;",
                        (clean_dom,),
                    )
                    row = cursor.fetchone()
                    if row:
                        return self._dict_to_field_observation(row)
        except Exception as e:
            logger.error(f"Failed to fetch field observation for {domain} in PostgreSQL: {e}")
        return None

    def get_field_observation_by_id(self, obs_id: int) -> Optional[FieldObservation]:
        self.init_schema()
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM field_study_observations WHERE id = %s LIMIT 1;",
                        (obs_id,),
                    )
                    row = cursor.fetchone()
                    if row:
                        return self._dict_to_field_observation(row)
        except Exception as e:
            logger.error(f"Failed to fetch field observation #{obs_id} in PostgreSQL: {e}")
        return None

    def delete_field_observation(self, obs_id: int) -> bool:
        self.init_schema()
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM field_study_observations WHERE id = %s;", (obs_id,)
                    )
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete field observation #{obs_id} in PostgreSQL: {e}")
            return False

    def delete_field_observations_batch(self, obs_ids: List[int]) -> int:
        if not obs_ids:
            return 0
        self.init_schema()
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM field_study_observations WHERE id = ANY(%s);",
                        (obs_ids,),
                    )
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to batch delete field observations in PostgreSQL: {e}")
            return 0

    def clear_field_study(self) -> bool:
        self.init_schema()
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM field_study_observations;")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to clear field study in PostgreSQL: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1;")
                return {
                    "type": "postgres",
                    "connected": True,
                    "persistent_storage": True,
                }
        except Exception as e:
            return {
                "type": "postgres",
                "connected": False,
                "error": str(e),
                "persistent_storage": True,
            }


_active_repository: Optional[BaseDatabaseRepository] = None


def get_repository(
    db_path: Optional[Union[str, Path]] = None,
    database_url: Optional[str] = None,
    force_new: bool = False,
) -> BaseDatabaseRepository:
    """
    Get or create active database repository.
    Selects PostgreSQL when database_url or DATABASE_URL environment variable is configured;
    otherwise falls back to local SQLite repository.
    """
    global _active_repository

    # If explicit parameters provided, create targeted repository instance
    if database_url or (DATABASE_URL and not db_path):
        url = database_url or DATABASE_URL
        if url.startswith("postgres://") or url.startswith("postgresql://"):
            return PostgresRepository(connection_url=url)

    if db_path:
        return SQLiteRepository(db_path=db_path)

    if _active_repository is None or force_new:
        if IS_POSTGRES:
            logger.info("Initializing PostgreSQL database repository for production.")
            _active_repository = PostgresRepository(connection_url=DATABASE_URL)
        else:
            _active_repository = SQLiteRepository(db_path=SQLITE_DB_PATH)

    return _active_repository


def reset_repository_singleton() -> None:
    """Reset the global repository singleton for testing isolation."""
    global _active_repository
    if _active_repository:
        try:
            _active_repository.close()
        except Exception:
            pass
    _active_repository = None
