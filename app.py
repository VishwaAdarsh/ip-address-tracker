"""
IP Address Tracker & Geolocation Tool
Main Application Entry Point (Phase 3 Integration Demonstration)
"""
import sys
from core.dns_resolver import resolve_domain
from core.validator import validate_input


def main() -> None:
    print("IP Address Tracker & Geolocation Tool")
    print("-------------------------------------")
    print("Phase 3: DNS Resolution verified successfully.")
    print(f"Running on Python {sys.version.split()[0]}")
    print()

    # Determine target domain from CLI arguments or use default
    target_domain = sys.argv[1] if len(sys.argv) > 1 else "google.com"

    print(f"Validating input: '{target_domain}'")
    val_res = validate_input(target_domain)
    print(f"  Normalized : {val_res.normalized_input}")
    print(f"  Input Type : {val_res.input_type.value}")
    print(f"  Is Valid   : {val_res.is_valid}")

    if val_res.is_valid:
        print("\nPerforming DNS Resolution...")
        dns_res = resolve_domain(target_domain)
        print(f"  Status          : {dns_res.status.value}")
        print(f"  Resolution Time : {dns_res.resolution_time_ms} ms")
        print(f"  IPv4 Addresses  : {dns_res.ipv4_addresses}")
        print(f"  IPv6 Addresses  : {dns_res.ipv6_addresses}")
        print(f"  All Addresses   : {dns_res.all_addresses}")
        if dns_res.error_message:
            print(f"  Error Message   : {dns_res.error_message}")


if __name__ == "__main__":
    main()
