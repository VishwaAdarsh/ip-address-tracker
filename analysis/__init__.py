"""
Analysis package for field-test data processing, statistics, and visualization.
"""
from analysis.analyzer import (
    compute_descriptive_stats,
    compute_distributions,
    compute_missing_data_report,
    export_cleaned_dataset,
    get_default_analysis_dir,
    get_default_raw_csv_path,
    load_and_validate_dataset,
)
try:
    from analysis.report_generator import generate_analysis_outputs
    from analysis.visualizer import generate_all_charts, get_default_charts_dir
except ImportError:
    generate_analysis_outputs = None  # type: ignore
    generate_all_charts = None  # type: ignore
    get_default_charts_dir = None  # type: ignore

from services.analytics_service import compute_field_study_analytics

__all__ = [
    "load_and_validate_dataset",
    "compute_descriptive_stats",
    "compute_distributions",
    "compute_missing_data_report",
    "export_cleaned_dataset",
    "generate_all_charts",
    "generate_analysis_outputs",
    "get_default_analysis_dir",
    "get_default_raw_csv_path",
    "get_default_charts_dir",
    "compute_field_study_analytics",
]
