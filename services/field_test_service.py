"""
Field-Test Orchestration Service for IP Address Tracker & Geolocation Tool.

Responsible for:
- Loading and validating the predefined 50-website sample (data/field_test/websites.csv)
- Executing lookups sequentially using services.lookup_service.perform_lookup
- Serializing address lists and handling missing values cleanly
- Persisting research results to data/field_test/field_test_results.csv
- Preserving individual lookup failures as valid research observations
- Supporting stop/pause requests and real-time progress callbacks
"""
import csv
import logging
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Union

from config.settings import BASE_DIR
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
    Raises:
    - ValueError if dataset is invalid, incomplete, or missing.
    """
    target_path = Path(csv_path) if csv_path else get_default_websites_path()

    if not target_path.exists() or not target_path.is_file():
        raise FileNotFoundError(f"Website dataset CSV not found at: {target_path}")

    websites: List[Dict[str, str]] = []
    seen_ids = set()
    seen_domains = set()

    with open(target_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_id = str(row.get("test_id", "")).strip()
            domain = str(row.get("domain", "")).strip().lower()
            category = str(row.get("category", "")).strip()

            if not test_id or not domain or not category:
                raise ValueError(
                    f"Malformed row in website dataset: {row}"
                )

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


def run_field_test(
    websites: Optional[List[Dict[str, str]]] = None,
    output_csv_path: Optional[Union[str, Path]] = None,
    progress_callback: Optional[Callable[[int, int, str, LookupResult], None]] = None,
    stop_event: Optional[threading.Event] = None,
    delay_seconds: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Execute sequential field-test lookups for test websites and write to CSV.

    Parameters:
    - websites: Optional website list (loads default 50 sites if None).
    - output_csv_path: Optional target CSV path.
    - progress_callback: Optional callable(current_index, total_count, domain, LookupResult).
    - stop_event: Optional threading.Event to pause/stop processing.
    - delay_seconds: Delay between sequential requests to respect API rate limits.
    """
    if websites is None:
        websites = load_test_websites()

    out_path = Path(output_csv_path) if output_csv_path else get_default_output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results_data: List[Dict[str, Any]] = []
    total_count = len(websites)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_TEST_HEADERS)
        writer.writeheader()

        for idx, site in enumerate(websites, start=1):
            if stop_event and stop_event.is_set():
                logger.info("Field test stopped early by user request.")
                break

            domain = site["domain"]
            test_id = site["test_id"]
            category = site["category"]

            # Perform lookup (save_to_db=False keeps research dataset separate from lookup history)
            res = perform_lookup(domain, save_to_db=False)

            # Format row for research dataset CSV
            row_data = {
                "test_id": test_id,
                "domain": domain,
                "category": category,
                "timestamp": res.timestamp,
                "input_type": res.input_type,
                "dns_status": res.dns_status,
                "ipv4_addresses": ";".join(res.ipv4_addresses),
                "ipv6_addresses": ";".join(res.ipv6_addresses),
                "selected_ip": res.selected_ip or "",
                "ip_version": res.ip_version,
                "country": res.country,
                "country_code": res.country_code,
                "region": res.region,
                "city": res.city,
                "latitude": res.latitude if res.latitude is not None else "",
                "longitude": res.longitude if res.longitude is not None else "",
                "timezone": res.timezone,
                "organization": res.organization,
                "isp": res.isp,
                "asn": res.asn,
                "dns_response_time_ms": res.dns_response_time_ms,
                "api_response_time_ms": res.api_response_time_ms,
                "total_response_time_ms": res.total_response_time_ms,
                "geolocation_status": res.geolocation_status,
                "overall_status": res.overall_status.value,
                "error_message": res.error_message or "",
            }

            writer.writerow(row_data)
            f.flush()

            results_data.append(row_data)

            if progress_callback:
                progress_callback(idx, total_count, domain, res)

            if delay_seconds > 0 and idx < total_count:
                time.sleep(delay_seconds)

    return results_data
