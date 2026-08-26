"""
Centralized Visual Design System for PySide6 + QFluentWidgets IP PULSE Console.

Defines:
- Dark Slate & Navy color palettes
- Consistent typography scales
- Reusable QSS (Qt Style Sheets) for glassmorphism card containers, inputs, buttons, and badges
"""

# Palette Constants
BG_DARK = "#0F172A"         # Deep Slate 900
SURFACE_BG = "#1E293B"      # Slate 800 (Card surface)
SURFACE_BORDER = "#334155"  # Slate 700 (Subtle border)
ACCENT_PRIMARY = "#0EA5E9"  # Sky Blue 500
ACCENT_HOVER = "#0284C7"    # Sky Blue 600
ACCENT_SUCCESS = "#10B981"  # Emerald 500
ACCENT_WARNING = "#F59E0B"  # Amber 500
ACCENT_ERROR = "#EF4444"    # Red 500
TEXT_LIGHT = "#F8FAFC"      # Slate 50 (High contrast)
TEXT_MUTED = "#94A3B8"      # Slate 400 (Secondary label)

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
    background-color: rgba(16, 185, 129, 0.15);
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
    background-color: rgba(239, 68, 68, 0.15);
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
