"""
Data Analyzer Module for IP Address Tracker & Geolocation Tool.

Provides:
- Dataset loading and validation for 50-website research observations
- Missing-data analysis and validation reporting
- Descriptive statistics computation (mean, median, min, max, std, percentiles) for timing metrics
- Categorical distribution analysis (country, IPv4/IPv6, status, category, ISP, ASN)
- Cleaned derived dataset export to data/analysis/cleaned_results.csv (raw data preserved untouched)
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd

from config.settings import BASE_DIR

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
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


def get_default_raw_csv_path() -> Path:
    """Return path to raw research field-test results CSV."""
    return BASE_DIR / "data" / "field_test" / "field_test_results.csv"


def get_default_analysis_dir() -> Path:
    """Return path to data/analysis/ output directory."""
    path = BASE_DIR / "data" / "analysis"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_and_validate_dataset(
    csv_path: Optional[Union[str, Path]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load raw field-test CSV results and perform comprehensive validation checks.

    Returns:
    - (DataFrame, validation_report_dict)
    """
    target_path = Path(csv_path) if csv_path else get_default_raw_csv_path()

    if not target_path.exists():
        raise FileNotFoundError(f"Field test results dataset not found at: {target_path}")

    df = pd.read_csv(target_path, dtype=str)

    validation_report = {
        "record_count": len(df),
        "columns_valid": list(df.columns) == EXPECTED_COLUMNS,
        "missing_columns": [col for col in EXPECTED_COLUMNS if col not in df.columns],
        "test_ids_valid": True,
        "timing_issues": [],
        "coordinate_issues": [],
        "warnings": [],
    }

    # Convert numeric fields safely
    numeric_cols = ["dns_response_time_ms", "api_response_time_ms", "total_response_time_ms"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # Check negative values
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                validation_report["timing_issues"].append(f"{col} contains {neg_count} negative values")

    coord_cols = ["latitude", "longitude"]
    for col in coord_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Validate coordinate bounds
    if "latitude" in df.columns:
        invalid_lat = df["latitude"].dropna().apply(lambda x: not (-90.0 <= x <= 90.0)).sum()
        if invalid_lat > 0:
            validation_report["coordinate_issues"].append(f"Latitude contains {invalid_lat} out-of-range values")

    if "longitude" in df.columns:
        invalid_lon = df["longitude"].dropna().apply(lambda x: not (-180.0 <= x <= 180.0)).sum()
        if invalid_lon > 0:
            validation_report["coordinate_issues"].append(f"Longitude contains {invalid_lon} out-of-range values")

    return df, validation_report


def compute_missing_data_report(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Calculate missing and unreturned attribute counts across fields."""
    report = {}
    total_records = len(df)

    key_fields = [
        "city",
        "region",
        "country",
        "latitude",
        "longitude",
        "timezone",
        "organization",
        "isp",
        "asn",
        "selected_ip",
    ]

    for field in key_fields:
        if field in df.columns:
            series = df[field]
            missing_count = series.isna().sum() + (series == "N/A").sum() + (series == "").sum()
            present_count = total_records - missing_count
            report[field] = {
                "present_count": int(present_count),
                "missing_count": int(missing_count),
                "missing_percentage": round((missing_count / total_records) * 100, 2) if total_records > 0 else 0.0,
            }

    return report


def compute_descriptive_stats(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Compute descriptive statistics (mean, median, min, max, std, percentiles) for timing metrics."""
    stats = {}
    timing_fields = [
        "dns_response_time_ms",
        "api_response_time_ms",
        "total_response_time_ms",
    ]

    for field in timing_fields:
        if field in df.columns:
            s = df[field].dropna()
            if len(s) > 0:
                p25 = float(np.percentile(s, 25))
                p75 = float(np.percentile(s, 75))
                stats[field] = {
                    "count": int(len(s)),
                    "mean": round(float(s.mean()), 2),
                    "std": round(float(s.std()), 2) if len(s) > 1 else 0.0,
                    "min": round(float(s.min()), 2),
                    "p25": round(p25, 2),
                    "median": round(float(s.median()), 2),
                    "p75": round(p75, 2),
                    "max": round(float(s.max()), 2),
                    "iqr": round(p75 - p25, 2),
                }
            else:
                stats[field] = {
                    "count": 0,
                    "mean": 0.0,
                    "std": 0.0,
                    "min": 0.0,
                    "p25": 0.0,
                    "median": 0.0,
                    "p75": 0.0,
                    "max": 0.0,
                    "iqr": 0.0,
                }

    return stats


def compute_distributions(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute frequency distribution tables for categorical attributes."""
    dist = {}

    if "country" in df.columns:
        c_series = df["country"].fillna("N/A").replace("", "N/A")
        dist["country_distribution"] = c_series.value_counts().to_dict()

    if "ip_version" in df.columns:
        v_series = df["ip_version"].fillna("N/A").replace("", "N/A")
        dist["ip_version_distribution"] = v_series.value_counts().to_dict()

    if "overall_status" in df.columns:
        s_series = df["overall_status"].fillna("N/A").replace("", "N/A")
        dist["status_distribution"] = s_series.value_counts().to_dict()

    if "category" in df.columns:
        cat_series = df["category"].fillna("N/A").replace("", "N/A")
        dist["category_distribution"] = cat_series.value_counts().to_dict()

    if "isp" in df.columns:
        isp_series = df["isp"].fillna("N/A").replace("", "N/A")
        dist["top_isps"] = isp_series.value_counts().head(10).to_dict()

    if "organization" in df.columns:
        org_series = df["organization"].fillna("N/A").replace("", "N/A")
        dist["top_organizations"] = org_series.value_counts().head(10).to_dict()

    if "asn" in df.columns:
        asn_series = df["asn"].fillna("N/A").replace("", "N/A")
        dist["top_asns"] = asn_series.value_counts().head(10).to_dict()

    return dist


def export_cleaned_dataset(
    df: pd.DataFrame, output_path: Optional[Union[str, Path]] = None
) -> Path:
    """Save derived cleaned dataset to data/analysis/cleaned_results.csv."""
    target_path = (
        Path(output_path)
        if output_path
        else get_default_analysis_dir() / "cleaned_results.csv"
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_path, index=False)
    return target_path
