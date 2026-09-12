"""
Chart Visualization Module for IP Address Tracker & Geolocation Tool.

Provides:
- Generation of 7 publication-quality dark-themed research charts using matplotlib
- Charts generated:
  1. country_distribution.png
  2. ip_version_distribution.png
  3. status_distribution.png
  4. dns_response_time.png
  5. api_response_time.png
  6. total_response_time.png
  7. category_distribution.png
"""
import logging
from pathlib import Path
from typing import List, Optional, Union

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for rendering clean PNGs
import matplotlib.pyplot as plt
import pandas as pd

from config.settings import BASE_DIR

logger = logging.getLogger(__name__)

# Dark Theme Palette Constants
BG_DARK = "#0F172A"       # Deep slate 900
SURFACE_DARK = "#1E293B"  # Slate 800
BORDER_DARK = "#334155"   # Slate 700
ACCENT_BLUE = "#0EA5E9"   # Sky 500
ACCENT_GREEN = "#10B981"  # Emerald 500
ACCENT_PURPLE = "#8B5CF6" # Purple 500
ACCENT_ORANGE = "#F59E0B" # Amber 500
ACCENT_RED = "#EF4444"    # Red 500
TEXT_LIGHT = "#F8FAFC"    # Slate 50
TEXT_MUTED = "#94A3B8"    # Slate 400


def get_default_charts_dir() -> Path:
    """Return default output directory for generated chart PNGs."""
    path = BASE_DIR / "data" / "analysis" / "charts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def apply_dark_style(fig: plt.Figure, ax: plt.Axes) -> None:
    """Apply consistent dark slate styling to matplotlib figure and axes."""
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE_DARK)

    ax.spines["top"].set_color(BORDER_DARK)
    ax.spines["bottom"].set_color(BORDER_DARK)
    ax.spines["left"].set_color(BORDER_DARK)
    ax.spines["right"].set_color(BORDER_DARK)

    ax.tick_params(colors=TEXT_LIGHT, which="both")
    ax.xaxis.label.set_color(TEXT_LIGHT)
    ax.yaxis.label.set_color(TEXT_LIGHT)
    ax.title.set_color(TEXT_LIGHT)
    ax.grid(True, linestyle="--", alpha=0.25, color=BORDER_DARK)


def generate_all_charts(
    df: pd.DataFrame, output_dir: Optional[Union[str, Path]] = None
) -> List[Path]:
    """
    Generate all 7 research charts from the field-test DataFrame.

    Returns list of saved chart PNG file paths.
    """
    target_dir = Path(output_dir) if output_dir else get_default_charts_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: List[Path] = []

    # 1. Country Distribution Chart
    if "country" in df.columns:
        p1 = target_dir / "country_distribution.png"
        fig, ax = plt.subplots(figsize=(9, 5))
        apply_dark_style(fig, ax)

        counts = df["country"].fillna("N/A").replace("", "N/A").value_counts().head(10)
        bars = ax.barh(counts.index[::-1], counts.values[::-1], color=ACCENT_BLUE, edgecolor=BORDER_DARK)
        ax.set_title("Top 10 Geolocation Countries (50-Website Field Sample)", fontsize=11, fontweight="bold", pad=12)
        ax.set_xlabel("Number of Websites", fontsize=10)

        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.2, bar.get_y() + bar.get_height()/2, f"{int(width)}", va="center", ha="left", color=TEXT_LIGHT, fontsize=9)

        plt.tight_layout()
        fig.savefig(p1, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        saved_paths.append(p1)

    # 2. IP Version Distribution Chart
    if "ip_version" in df.columns:
        p2 = target_dir / "ip_version_distribution.png"
        fig, ax = plt.subplots(figsize=(6, 5))
        fig.patch.set_facecolor(BG_DARK)
        ax.set_facecolor(BG_DARK)

        v_counts = df["ip_version"].fillna("N/A").replace("", "N/A").value_counts()
        colors = [ACCENT_BLUE, ACCENT_PURPLE, ACCENT_ORANGE][:len(v_counts)]
        wedges, texts, autotexts = ax.pie(
            v_counts.values,
            labels=v_counts.index,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            textprops={"color": TEXT_LIGHT},
            wedgeprops={"edgecolor": BORDER_DARK, "linewidth": 1.5},
        )
        for at in autotexts:
            at.set_color("#FFFFFF")
            at.set_fontweight("bold")

        ax.set_title("Selected IP Protocol Version Distribution", color=TEXT_LIGHT, fontsize=11, fontweight="bold", pad=12)
        plt.tight_layout()
        fig.savefig(p2, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        saved_paths.append(p2)

    # 3. Lookup Status Distribution Chart
    if "overall_status" in df.columns:
        p3 = target_dir / "status_distribution.png"
        fig, ax = plt.subplots(figsize=(8, 4.5))
        apply_dark_style(fig, ax)

        st_counts = df["overall_status"].fillna("N/A").value_counts()
        bars = ax.bar(st_counts.index, st_counts.values, color=ACCENT_GREEN, edgecolor=BORDER_DARK, width=0.5)
        ax.set_title("Lookup Status Outcomes (Field Experiment)", fontsize=11, fontweight="bold", pad=12)
        ax.set_ylabel("Count of Websites", fontsize=10)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 0.5, f"{int(height)}", ha="center", va="bottom", color=TEXT_LIGHT, fontsize=9)

        plt.tight_layout()
        fig.savefig(p3, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        saved_paths.append(p3)

    # 4. DNS Response Time Histogram
    if "dns_response_time_ms" in df.columns:
        p4 = target_dir / "dns_response_time.png"
        fig, ax = plt.subplots(figsize=(8, 4.5))
        apply_dark_style(fig, ax)

        s_dns = pd.to_numeric(df["dns_response_time_ms"], errors="coerce").dropna()
        if len(s_dns) > 0:
            ax.hist(s_dns, bins=12, color=ACCENT_BLUE, edgecolor=BORDER_DARK, alpha=0.85)
            median_val = s_dns.median()
            ax.axvline(median_val, color=ACCENT_ORANGE, linestyle="--", linewidth=2, label=f"Median: {median_val:.1f} ms")
            ax.legend(facecolor=SURFACE_DARK, edgecolor=BORDER_DARK, labelcolor=TEXT_LIGHT)

        ax.set_title("DNS Resolution Time Distribution", fontsize=11, fontweight="bold", pad=12)
        ax.set_xlabel("DNS Resolution Time (ms)", fontsize=10)
        ax.set_ylabel("Frequency", fontsize=10)

        plt.tight_layout()
        fig.savefig(p4, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        saved_paths.append(p4)

    # 5. Geolocation API Response Time Histogram
    if "api_response_time_ms" in df.columns:
        p5 = target_dir / "api_response_time.png"
        fig, ax = plt.subplots(figsize=(8, 4.5))
        apply_dark_style(fig, ax)

        s_api = pd.to_numeric(df["api_response_time_ms"], errors="coerce").dropna()
        if len(s_api) > 0:
            ax.hist(s_api, bins=12, color=ACCENT_PURPLE, edgecolor=BORDER_DARK, alpha=0.85)
            med_api = s_api.median()
            ax.axvline(med_api, color=ACCENT_ORANGE, linestyle="--", linewidth=2, label=f"Median: {med_api:.1f} ms")
            ax.legend(facecolor=SURFACE_DARK, edgecolor=BORDER_DARK, labelcolor=TEXT_LIGHT)

        ax.set_title("Geolocation API Response Time Distribution", fontsize=11, fontweight="bold", pad=12)
        ax.set_xlabel("API Response Time (ms)", fontsize=10)
        ax.set_ylabel("Frequency", fontsize=10)

        plt.tight_layout()
        fig.savefig(p5, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        saved_paths.append(p5)

    # 6. Total Lookup Response Time Histogram
    if "total_response_time_ms" in df.columns:
        p6 = target_dir / "total_response_time.png"
        fig, ax = plt.subplots(figsize=(8, 4.5))
        apply_dark_style(fig, ax)

        s_tot = pd.to_numeric(df["total_response_time_ms"], errors="coerce").dropna()
        if len(s_tot) > 0:
            ax.hist(s_tot, bins=12, color=ACCENT_GREEN, edgecolor=BORDER_DARK, alpha=0.85)
            med_tot = s_tot.median()
            ax.axvline(med_tot, color=ACCENT_ORANGE, linestyle="--", linewidth=2, label=f"Median: {med_tot:.1f} ms")
            ax.legend(facecolor=SURFACE_DARK, edgecolor=BORDER_DARK, labelcolor=TEXT_LIGHT)

        ax.set_title("Total Lookup Execution Time Distribution", fontsize=11, fontweight="bold", pad=12)
        ax.set_xlabel("Total Execution Time (ms)", fontsize=10)
        ax.set_ylabel("Frequency", fontsize=10)

        plt.tight_layout()
        fig.savefig(p6, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        saved_paths.append(p6)

    # 7. Category Distribution Chart
    if "category" in df.columns:
        p7 = target_dir / "category_distribution.png"
        fig, ax = plt.subplots(figsize=(9, 5))
        apply_dark_style(fig, ax)

        cat_counts = df["category"].fillna("N/A").value_counts()
        bars = ax.barh(cat_counts.index[::-1], cat_counts.values[::-1], color=ACCENT_ORANGE, edgecolor=BORDER_DARK)
        ax.set_title("Website Sample Category Representation", fontsize=11, fontweight="bold", pad=12)
        ax.set_xlabel("Count of Websites", fontsize=10)

        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, f"{int(width)}", va="center", ha="left", color=TEXT_LIGHT, fontsize=9)

        plt.tight_layout()
        fig.savefig(p7, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        saved_paths.append(p7)

    return saved_paths
