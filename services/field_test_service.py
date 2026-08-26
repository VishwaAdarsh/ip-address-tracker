"""
Field-Test Orchestration Service for IP Address Tracker & Geolocation Tool.

Implements the Manual-First Field Project Methodology:
- Uses SQLite Lookup History as the primary source of truth for field-test observations.
- Filters and deduplicates valid domain lookups from History.
- Calculates available observations (N / 50) and remaining needed count.
- Provides optional controlled automatic completion ONLY for remaining observations when N < 50.
- Exports formal 50-observation field dataset to data/field_test/field_test_results.csv.
"""
import csv
import logging
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Union

from config.settings import BASE_DIR
from database.models import LookupRecord
from services.lookup_service import LookupResult, perform_lookup

logger = logging.getLogger(__name__)

# Field CSV Header definitions
FIELD_TEST_HEADERS = [
    "test_id",
    "domain",
    "category",
    "timestamp",
    "input_type",
    "dns_status",
    "ipv4_addresses",
    "ipv6_addresses",
    "selected_ip",
    "ip_version",
    "country",
    "country_code",
    "region",
    "city",
    "latitude",
    "longitude",
    "timezone",
    "organization",
    "isp",
    "asn",
    "dns_response_time_ms",
    "api_response_time_ms",
    "total_response_time_ms",
    "geolocation_status",
    "overall_status",
    "error_message",
]


def get_default_websites_path() -> Path:
    """Return default path to websites.csv dataset."""
    return BASE_DIR / "data" / "field_test" / "websites.csv"


def get_default_output_path() -> Path:
    """Return default path to output field_test_results.csv file."""
    path = BASE_DIR / "data" / "field_test" / "field_test_results.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_test_websites(
    csv_path: Optional[Union[str, Path]] = None
) -> List[Dict[str, str]]:
    """
    Load and validate the predefined 50-website dataset CSV file.

    Returns:
    - List of dicts with keys: 'test_id', 'domain', 'category'
    """
    target_path = Path(csv_path) if csv_path else get_default_websites_path()

    if not target_path.exists() or not target_path.is_file():
        raise FileNotFoundError(f"Website dataset CSV not found at: {target_path}")

    websites: List[Dict[str, str]] = []
    seen_ids: Set[str] = set()
    seen_domains: Set[str] = set()

    with open(target_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_id = str(row.get("test_id", "")).strip()
            domain = str(row.get("domain", "")).strip().lower()
            category = str(row.get("category", "")).strip()

            if not test_id or not domain or not category:
                raise ValueError(f"Malformed row in website dataset: {row}")

            if test_id in seen_ids:
                raise ValueError(f"Duplicate test_id in dataset: {test_id}")
            seen_ids.add(test_id)

            if domain in seen_domains:
                raise ValueError(f"Duplicate domain in dataset: {domain}")
            seen_domains.add(domain)

            websites.append(
                {"test_id": test_id, "domain": domain, "category": category}
            )

    return websites


def get_field_project_status(
    db_path: Optional[Union[str, Path]] = None,
    target_count: int = 50,
) -> Dict[str, Any]:
    """
    Evaluate the manual-first field project status from SQLite History.

    Methodology:
    1. Read stored history records from database.
    2. Filter valid domain lookups (excluding malformed or invalid inputs).
    3. Deduplicate records by domain name (preserving unique domain entries).
    4. Calculate available count, remaining needed count, and status.

    Returns:
    - Dict with keys: 'available_count', 'manual_count', 'auto_count', 'remaining',
      'status', 'unique_records', 'domain_map'
    """
    from database.db import get_lookup_history

    records = get_lookup_history(db_path=db_path)

    # Load categories mapping from websites.csv if available
    category_map: Dict[str, str] = {}
    try:
        websites = load_test_websites()
        category_map = {w["domain"]: w["category"] for w in websites}
    except Exception:
        pass

    unique_domains_dict: Dict[str, LookupRecord] = {}

    for record in records:
        domain = (record.domain or record.input_value or "").lower().strip()
        if not domain or record.status == "INVALID_INPUT":
            continue

        # Keep earliest observation for deterministic historical ordering
        if domain not in unique_domains_dict:
            unique_domains_dict[domain] = record

    unique_records = list(unique_domains_dict.values())
    available_count = len(unique_records)
    remaining = max(target_count - available_count, 0)
    status_str = "TARGET_REACHED" if available_count >= target_count else "INCOMPLETE"

    return {
        "available_count": available_count,
        "manual_count": available_count,
        "auto_count": 0,
        "target": target_count,
        "remaining": remaining,
        "status": status_str,
        "unique_records": unique_records,
        "category_map": category_map,
    }


def export_field_dataset_from_history(
    db_path: Optional[Union[str, Path]] = None,
    output_csv_path: Optional[Union[str, Path]] = None,
    target_count: int = 50,
) -> List[Dict[str, Any]]:
    """
    Export formal field-test dataset CSV derived directly from SQLite History.

    - Selects up to target_count unique domain records deterministically.
    - Writes to data/field_test/field_test_results.csv.
    - Raw History remains untouched.
    """
    status = get_field_project_status(db_path=db_path, target_count=target_count)
    records = status["unique_records"][:target_count]
    category_map = status["category_map"]

    out_path = Path(output_csv_path) if output_csv_path else get_default_output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results_data: List[Dict[str, Any]] = []

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_TEST_HEADERS)
        writer.writeheader()

        for idx, rec in enumerate(records, start=1):
            domain = rec.domain or rec.input_value
            cat = category_map.get(domain.lower(), "General Web")

            row_data = {
                "test_id": str(idx),
                "domain": domain,
                "category": cat,
                "timestamp": rec.timestamp,
                "input_type": rec.input_type or "DOMAIN",
                "dns_status": "SUCCESS" if rec.ip_address else "DNS_FAILED",
                "ipv4_addresses": rec.ip_address if rec.ip_version == "IPv4" else "",
                "ipv6_addresses": rec.ip_address if rec.ip_version == "IPv6" else "",
                "selected_ip": rec.ip_address or "",
                "ip_version": rec.ip_version,
                "country": rec.country,
                "country_code": rec.country_code,
                "region": rec.region,
                "city": rec.city,
                "latitude": rec.latitude if rec.latitude is not None else "",
                "longitude": rec.longitude if rec.longitude is not None else "",
                "timezone": rec.timezone,
                "organization": rec.organization,
                "isp": rec.isp,
                "asn": rec.asn,
                "dns_response_time_ms": rec.dns_response_time_ms,
                "api_response_time_ms": rec.api_response_time_ms,
                "total_response_time_ms": round(
                    rec.dns_response_time_ms + rec.api_response_time_ms, 2
                ),
                "geolocation_status": "SUCCESS" if rec.country != "N/A" else "GEO_FAILED",
                "overall_status": rec.status,
                "error_message": rec.error_message or "",
            }

            writer.writerow(row_data)
            results_data.append(row_data)

    return results_data


def run_automatic_completion(
    db_path: Optional[Union[str, Path]] = None,
    output_csv_path: Optional[Union[str, Path]] = None,
    progress_callback: Optional[Callable[[int, int, str, LookupResult], None]] = None,
    stop_event: Optional[threading.Event] = None,
    delay_seconds: float = 0.5,
    target_count: int = 50,
) -> List[Dict[str, Any]]:
    """
    Execute controlled automatic completion ONLY for remaining observations needed to reach 50.

    Rules:
    1. Checks current field project status in History.
    2. Calculates remaining = max(50 - available, 0).
    3. Never executes more lookups than remaining.
    4. Runs lookups through standard services.lookup_service.perform_lookup(domain, save_to_db=True).
    5. Saves entries to normal SQLite History.
    6. Exports updated field dataset to CSV.
    """
    status = get_field_project_status(db_path=db_path, target_count=target_count)
    remaining_needed = status["remaining"]

    if remaining_needed <= 0:
        logger.info("Field project target of 50 observations already reached.")
        return export_field_dataset_from_history(
            db_path=db_path, output_csv_path=output_csv_path, target_count=target_count
        )

    # Load 50 predefined websites
    all_websites = load_test_websites()
    existing_domains = {r.domain.lower() for r in status["unique_records"]}

    # Filter websites not yet present in History
    missing_websites = [w for w in all_websites if w["domain"] not in existing_domains]

    # Select exactly remaining_needed websites
    websites_to_run = missing_websites[:remaining_needed]
    total_to_run = len(websites_to_run)

    for idx, site in enumerate(websites_to_run, start=1):
        if stop_event and stop_event.is_set():
            logger.info("Automatic completion stopped early by user request.")
            break

        domain = site["domain"]

        # Execute lookup and save to History
        res = perform_lookup(domain, save_to_db=True, db_path=db_path)

        if progress_callback:
            progress_callback(idx, total_to_run, domain, res)

        if delay_seconds > 0 and idx < total_to_run:
            time.sleep(delay_seconds)

    # Export updated field dataset from History
    return export_field_dataset_from_history(
        db_path=db_path, output_csv_path=output_csv_path, target_count=target_count
    )


# Backward-compatibility alias
def run_field_test(
    websites: Optional[List[Dict[str, str]]] = None,
    output_csv_path: Optional[Union[str, Path]] = None,
    progress_callback: Optional[Callable[[int, int, str, LookupResult], None]] = None,
    stop_event: Optional[threading.Event] = None,
    delay_seconds: float = 0.5,
) -> List[Dict[str, Any]]:
    """Legacy runner alias wrapping automatic completion."""
    return run_automatic_completion(
        output_csv_path=output_csv_path,
        progress_callback=progress_callback,
        stop_event=stop_event,
        delay_seconds=delay_seconds,
    )
