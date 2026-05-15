"""
CryptoViz Design System
Single source of truth for all visual design tokens.
CSS custom properties are generated from here — nothing is hardcoded anywhere else.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class ColorPalette:
    # Background layers
    bg_root: str = "#050505"
    bg_surface: str = "#0d0d0d"
    bg_elevated: str = "#141414"

    # Text hierarchy
    text_primary: str = "#f0f0f0"
    text_secondary: str = "#a0a0a0"
    text_muted: str = "#555555"
    text_label: str = "#666666"    # uppercase small labels

    # Borders
    border_strong: str = "#1a1a1a"
    border_subtle: str = "#0f0f0f"

    # Accent
    blue: str = "#0066FF"

    # Dynamic — set per alert
    trend: str = "#00FF88"         # overridden to #FF3344 for bearish


@dataclass
class Typography:
    family_display: str = "'Inter', -apple-system, sans-serif"
    family_mono: str = "'IBM Plex Mono', 'JetBrains Mono', monospace"

    # Scale (px)
    hero: int = 160
    h1: int = 96
    h2: int = 72
    h3: int = 56
    stat_large: int = 80
    stat: int = 60
    body: int = 22
    label: int = 12
    micro: int = 11

    weight_bold: int = 700
    weight_medium: int = 500
    weight_regular: int = 400

    tracking_tight: str = "-0.04em"
    tracking_normal: str = "-0.01em"
    tracking_wide: str = "0.15em"
    tracking_widest: str = "0.25em"


@dataclass
class Motion:
    # Easing
    ease_snap: str = "expo.out"
    ease_smooth: str = "power3.out"
    ease_exit: str = "power4.in"
    ease_bounce: str = "back.out(1.5)"

    # Durations (seconds)
    fast: float = 0.25
    normal: float = 0.45
    slow: float = 0.65
    stagger: float = 0.08


@dataclass
class Layout:
    canvas_w: int = 1920
    canvas_h: int = 1080
    chart_w: int = 1200    # left panel for chart
    padding_outer: int = 80
    padding_inner: int = 52


COLORS = ColorPalette()
TYPE = Typography()
MOTION = Motion()
LAYOUT = Layout()


def get_trend_colors(is_positive: bool) -> tuple[str, str]:
    """Returns (trend_color, opposite_color) based on price direction."""
    if is_positive:
        return "#00FF88", "#FF3344"
    return "#FF3344", "#00FF88"


def css_vars(trend_color: str) -> str:
    """Generate CSS custom property block for a composition."""
    return f"""
  --bg: {COLORS.bg_root};
  --surface: {COLORS.bg_surface};
  --elevated: {COLORS.bg_elevated};
  --text: {COLORS.text_primary};
  --text-2: {COLORS.text_secondary};
  --text-3: {COLORS.text_muted};
  --label: {COLORS.text_label};
  --border: {COLORS.border_strong};
  --border-s: {COLORS.border_subtle};
  --blue: {COLORS.blue};
  --tc: {trend_color};
  --font: {TYPE.family_display};
  --mono: {TYPE.family_mono};
""".strip()
