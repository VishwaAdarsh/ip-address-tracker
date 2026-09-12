"""
Advanced Risk & Intelligence Analytics Module for IP PULSE Platform.

Provides:
- Field study risk & trust score statistical distributions
- Infrastructure category frequency counts (CDN, Cloud, ISP, Enterprise)
- HTTPS / SSL adoption & security header enforcement metrics across dataset
"""
import os
from typing import Dict, Any
import numpy as np
import pandas as pd

from services.risk_analysis_service import perform_full_intelligence_scan


def compute_risk_analytics_from_dataset(csv_path: str) -> Dict[str, Any]:
    """
    Perform statistical audit and risk signal analysis across a dataset CSV file.

    Args:
    - csv_path: Path to field test results CSV file

    Returns:
    - Dictionary containing descriptive stats, infrastructure breakdown, and security adoption metrics
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Field dataset CSV not found at '{csv_path}'")

    df = pd.read_csv(csv_path)

    # Perform full intelligence scans across unique domains in dataset
    trust_scores = []
    risk_scores = []
    infra_types = []
    https_flags = []
    ssl_valid_flags = []
    hsts_flags = []

    domains = df["domain"].dropna().unique() if "domain" in df.columns else df["input_value"].dropna().unique()

    for domain in domains:
        full_res = perform_full_intelligence_scan(str(domain), save_to_db=False)
        trust_scores.append(full_res.risk.trust_score)
        risk_scores.append(full_res.risk.risk_score)
        infra_types.append(full_res.ip_intel.infrastructure_type)
        https_flags.append(full_res.security.https_enabled)
        ssl_valid_flags.append(full_res.security.ssl_valid)
        hsts_flags.append(full_res.security.security_headers.get("hsts", False))

    trust_arr = np.array(trust_scores)
    risk_arr = np.array(risk_scores)

    infra_series = pd.Series(infra_types)
    infra_counts = infra_series.value_counts().to_dict()

    total_count = len(domains)

    return {
        "sample_size": total_count,
        "trust_score_stats": {
            "mean": round(float(np.mean(trust_arr)), 2) if total_count > 0 else 0,
            "median": round(float(np.median(trust_arr)), 2) if total_count > 0 else 0,
            "std": round(float(np.std(trust_arr)), 2) if total_count > 0 else 0,
            "min": int(np.min(trust_arr)) if total_count > 0 else 0,
            "max": int(np.max(trust_arr)) if total_count > 0 else 0,
        },
        "risk_score_stats": {
            "mean": round(float(np.mean(risk_arr)), 2) if total_count > 0 else 0,
            "median": round(float(np.median(risk_arr)), 2) if total_count > 0 else 0,
            "std": round(float(np.std(risk_arr)), 2) if total_count > 0 else 0,
            "min": int(np.min(risk_arr)) if total_count > 0 else 0,
            "max": int(np.max(risk_arr)) if total_count > 0 else 0,
        },
        "infrastructure_distribution": infra_counts,
        "security_adoption": {
            "https_percentage": round((sum(https_flags) / total_count * 100), 2) if total_count > 0 else 0,
            "ssl_valid_percentage": round((sum(ssl_valid_flags) / total_count * 100), 2) if total_count > 0 else 0,
            "hsts_percentage": round((sum(hsts_flags) / total_count * 100), 2) if total_count > 0 else 0,
        },
    }
