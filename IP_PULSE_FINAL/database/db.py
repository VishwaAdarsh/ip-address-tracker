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
from typing import List, Optional, Union

from config.settings import BASE_DIR
from database.models import LookupRecord
from services.lookup_service import LookupResult

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
    """Open and return a SQLite database connection with row_factory enabled."""
    target_path = get_db_path(db_path)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Union[str, Path]] = None) -> None:
    """Initialize SQLite database schema for lookup history."""
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
    """
    try:
        conn = get_connection(db_path)
        try:
            conn.execute(schema_sql)
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize SQLite database schema: {e}")
        raise


def save_lookup(
    result: LookupResult, db_path: Optional[Union[str, Path]] = None
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
