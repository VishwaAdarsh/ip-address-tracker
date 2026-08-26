"""
IP Address Tracker & Geolocation Tool
Main Application Entry Point (Phase 5 Integrated Engine Demonstration)
"""
import sys
from config.settings import GEO_PROVIDER_NAME
from services.lookup_service import perform_lookup


def main() -> None:
    print("IP Address Tracker & Geolocation Tool")
    print("-------------------------------------")
    print("Phase 5: Integrated Lookup Engine verified successfully.")
    print(f"Provider: {GEO_PROVIDER_NAME}")
    print(f"Running on Python {sys.version.split()[0]}")
    print()

    target_input = sys.argv[1] if len(sys.argv) > 1 else "google.com"
    print(f"Executing Integrated Lookup for: '{target_input}'\n")

    res = perform_lookup(target_input)

    print("--- Lookup Summary ---")
    print(f"Input                 : {res.input}")
    print(f"Normalized Input      : {res.normalized_input}")
    print(f"Input Type            : {res.input_type}")
    print(f"Overall Status        : {res.overall_status.value}")
    print(f"DNS Status            : {res.dns_status}")
    print(f"Geolocation Status    : {res.geolocation_status}")
    print()
    print("--- Network & Address Info ---")
    print(f"IPv4 Addresses        : {res.ipv4_addresses}")
    print(f"IPv6 Addresses        : {res.ipv6_addresses}")
    print(f"All Resolved IPs      : {res.resolved_addresses}")
    print(f"Selected Target IP    : {res.selected_ip}")
    print(f"IP Version            : {res.ip_version}")
    print()
    print("--- Geolocation Data ---")
    print(f"Country               : {res.country} ({res.country_code})")
    print(f"Region                : {res.region}")
    print(f"City                  : {res.city}")
    print(f"Coordinates           : Lat {res.latitude}, Lon {res.longitude}")
    print(f"Timezone              : {res.timezone}")
    print(f"Organization          : {res.organization}")
    print(f"ISP                   : {res.isp}")
    print(f"ASN                   : {res.asn}")
    print()
    print("--- Execution Timing ---")
    print(f"DNS Response Time     : {res.dns_response_time_ms} ms")
    print(f"API Response Time     : {res.api_response_time_ms} ms")
    print(f"Total Lookup Time     : {res.total_response_time_ms} ms")

    if res.error_message:
        print(f"\nError Message         : {res.error_message}")


if __name__ == "__main__":
    main()
