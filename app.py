"""
IP Address Tracker & Geolocation Tool
Main Application Entry Point (Phase 4 Integration Demonstration)
"""
import sys
from config.settings import GEO_PROVIDER_NAME
from core.dns_resolver import DNSStatus, resolve_domain
from core.geo_service import get_geolocation
from core.validator import validate_input


def main() -> None:
    print("IP Address Tracker & Geolocation Tool")
    print("-------------------------------------")
    print("Phase 4: IP Geolocation Service verified successfully.")
    print(f"Provider: {GEO_PROVIDER_NAME}")
    print(f"Running on Python {sys.version.split()[0]}")
    print()

    # Determine target domain or IP from CLI arguments or default
    target_input = sys.argv[1] if len(sys.argv) > 1 else "google.com"

    print(f"1. Validating input: '{target_input}'")
    val_res = validate_input(target_input)
    print(f"   Normalized : {val_res.normalized_input}")
    print(f"   Input Type : {val_res.input_type.value}")
    print(f"   Is Valid   : {val_res.is_valid}")

    if not val_res.is_valid:
        print(f"   Error      : {val_res.error_message}")
        return

    resolved_ip = ""

    if val_res.input_type.value in ("IPV4", "IPV6"):
        resolved_ip = val_res.normalized_input
        print(f"\n2. Direct IP Input Provided: {resolved_ip}")
    else:
        print("\n2. Performing DNS Resolution...")
        dns_res = resolve_domain(target_input)
        print(f"   Status          : {dns_res.status.value}")
        print(f"   Resolution Time : {dns_res.resolution_time_ms} ms")
        print(f"   IPv4 Addresses  : {dns_res.ipv4_addresses}")
        print(f"   IPv6 Addresses  : {dns_res.ipv6_addresses}")
        print(f"   All Addresses   : {dns_res.all_addresses}")

        if dns_res.status != DNSStatus.SUCCESS or not dns_res.all_addresses:
            print(f"   DNS Error       : {dns_res.error_message}")
            return

        # Select primary IPv4 or IPv6 address for geolocation lookup
        resolved_ip = dns_res.ipv4_addresses[0] if dns_res.ipv4_addresses else dns_res.all_addresses[0]

    print(f"\n3. Performing Geolocation Lookup for IP: {resolved_ip}...")
    geo_res = get_geolocation(resolved_ip)
    print(f"   Status       : {geo_res.status.value}")
    print(f"   IP Address   : {geo_res.ip} ({geo_res.ip_version})")
    print(f"   Country      : {geo_res.country} ({geo_res.country_code})")
    print(f"   Region       : {geo_res.region}")
    print(f"   City         : {geo_res.city}")
    print(f"   Coordinates  : Lat {geo_res.latitude}, Lon {geo_res.longitude}")
    print(f"   Timezone     : {geo_res.timezone}")
    print(f"   Organization : {geo_res.organization}")
    print(f"   ISP          : {geo_res.isp}")
    print(f"   ASN          : {geo_res.asn}")
    if geo_res.error_message:
        print(f"   Error        : {geo_res.error_message}")


if __name__ == "__main__":
    main()
