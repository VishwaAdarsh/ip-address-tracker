"""
Centralized Visual Design System for PySide6 + QFluentWidgets IP PULSE Platform.

Defines Stitch-aligned visual design tokens:
- Stitch obsidian dark theme surface colors (#0F131C, #181C24, #262A33)
- Cyan & Emerald telemetry accents (#00D2FF, #69F6B9)
- Reusable QSS (Qt Style Sheets) for glassmorphism card containers, inputs, buttons, and badges
"""

# Stitch Visual Palette Constants
BG_DARK = "#0F131C"                 # Stitch Surface Dim (#0F131C)
SURFACE_BG = "#181C24"              # Stitch Surface Container Low (#181C24)
SURFACE_CONTAINER_HIGH = "#262A33"  # Stitch Surface Container High (#262A33)
SURFACE_BORDER = "#3C494E"          # Stitch Outline Variant (#3C494E)
ACCENT_PRIMARY = "#00D2FF"          # Stitch Electric Cyan Primary (#00D2FF)
ACCENT_HOVER = "#47D6FF"            # Stitch Cyan Hover (#47D6FF)
ACCENT_SUCCESS = "#69F6B9"          # Stitch Emerald Tertiary (#69F6B9)
ACCENT_WARNING = "#F59E0B"          # Amber 500
ACCENT_ERROR = "#FFB4AB"            # Stitch Coral Red Error (#FFB4AB)
TEXT_LIGHT = "#DFE2EE"              # Stitch High Contrast Text (#DFE2EE)
TEXT_MUTED = "#BBC9CF"              # Stitch Secondary Text (#BBC9CF)

# Centralized QSS Stylesheet for PySide6 Widgets
CARD_QSS = f"""
QFrame#CardFrame {{
    background-color: {SURFACE_BG};
    border: 1px solid {SURFACE_BORDER};
    border-radius: 8px;
}}
QFrame#CardFrame:hover {{
    border: 1px solid {ACCENT_PRIMARY};
}}
"""

GLASS_CARD_QSS = f"""
QFrame#GlassCard {{
    background-color: {SURFACE_BG};
    border: 1px solid {SURFACE_BORDER};
    border-radius: 10px;
}}
"""

BADGE_SUCCESS_QSS = f"""
QLabel {{
    background-color: rgba(105, 246, 185, 0.15);
    color: {ACCENT_SUCCESS};
    border: 1px solid {ACCENT_SUCCESS};
    border-radius: 4px;
    padding: 4px 10px;
    font-weight: bold;
    font-size: 11px;
}}
"""

BADGE_FAILED_QSS = f"""
QLabel {{
    background-color: rgba(255, 180, 171, 0.15);
    color: {ACCENT_ERROR};
    border: 1px solid {ACCENT_ERROR};
    border-radius: 4px;
    padding: 4px 10px;
    font-weight: bold;
    font-size: 11px;
}}
"""

BADGE_ONLINE_QSS = f"""
QLabel {{
    color: {ACCENT_SUCCESS};
    font-weight: bold;
    font-size: 12px;
}}
"""
