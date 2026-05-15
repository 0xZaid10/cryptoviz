"""
Chart data precomputation.
All SVG math done in Python — compositions receive ready-to-render coordinates.
"""

import math
from dataclasses import dataclass, field
from typing import List
from styles.design_system import LAYOUT


@dataclass
class ChartData:
    # Canvas
    w: int = 0
    h: int = 0
    pad_x: int = 0
    pad_y: int = 0
    plot_w: float = 0
    plot_h: float = 0

    # Price range
    p_min: float = 0
    p_max: float = 0

    # SVG elements
    polyline: str = ""
    area_path: str = ""
    ma_polyline: str = ""
    current_price_y: float = 0
    candles: List[str] = field(default_factory=list)
    grids: str = ""
    axes: str = ""

    # Extras
    ticker_text: str = ""


def compute(event: dict, trend_color: str) -> ChartData:
    """
    Compute all chart coordinates from market event data.
    Returns ChartData with everything the templates need.
    """
    prices  = event.get("price_history", [])
    volumes = event.get("volume_history", [])

    cw = LAYOUT.chart_w
    ch = 700
    px = 88
    py = 65
    vol_h = 130     # height reserved for volume bars at bottom
    pw = cw - px * 2
    ph = ch - py * 2 - vol_h

    p_min = min(prices) if prices else 0
    p_max = max(prices) if prices else 1
    p_range = p_max - p_min or 1
    n = len(prices)

    def px_x(i: int) -> float:
        return px + (i / max(n - 1, 1)) * pw

    def px_y(price: float) -> float:
        return py + (1 - (price - p_min) / p_range) * ph

    # Price polyline
    if n > 1:
        pts = [f"{px_x(i):.1f},{px_y(p):.1f}" for i, p in enumerate(prices)]
        polyline = " ".join(pts)
        area = (
            f"M {px} {py+ph} " +
            " ".join(f"L {px_x(i):.1f} {px_y(p):.1f}" for i, p in enumerate(prices)) +
            f" L {px+pw} {py+ph} Z"
        )
    else:
        mid = py + ph / 2
        polyline = f"{px},{mid:.1f} {px+pw},{mid:.1f}"
        area = ""

    # Current price Y
    cur_y = px_y(event["current_price"])

    # Moving average (10-period)
    ma_pts = []
    for i in range(n):
        w = prices[max(0, i-9):i+1]
        ma = sum(w) / len(w)
        ma_pts.append(f"{px_x(i):.1f},{px_y(ma):.1f}")
    ma_poly = " ".join(ma_pts) if ma_pts else polyline

    # Candlesticks (group into 20 candles)
    chunk = max(1, n // 20)
    candle_els = []
    vmax = max(volumes) if volumes else 1
    bar_w = pw / max(n // chunk, 1)

    for ci in range(0, n - chunk + 1, chunk):
        seg = prices[ci:ci+chunk]
        vi  = volumes[ci] if ci < len(volumes) else 0
        o, c_, h_, l_ = seg[0], seg[-1], max(seg), min(seg)
        bull = c_ >= o
        col  = trend_color if bull else ("#FF3344" if trend_color == "#00FF88" else "#00FF88")

        cx2   = px + (ci / chunk + 0.5) * bar_w
        bt    = px_y(max(o, c_))
        bb    = px_y(min(o, c_))
        bh    = max(bb - bt, 2)
        hy    = px_y(h_)
        ly    = px_y(l_)
        hw    = bar_w * 0.36

        # Volume bar
        vh  = max((vi / vmax) * (vol_h - 10), 2)
        vx  = px + (ci // chunk) * bar_w
        vy  = ch - 15 - vh

        candle_els.append(
            f'<g class="candle" opacity="0">'
            f'<line x1="{cx2:.1f}" y1="{hy:.1f}" x2="{cx2:.1f}" y2="{ly:.1f}" '
            f'stroke="{col}" stroke-width="1.2"/>'
            f'<rect x="{cx2-hw:.1f}" y="{bt:.1f}" width="{hw*2:.1f}" '
            f'height="{bh:.1f}" fill="{col}" opacity="0.9"/>'
            f'<rect class="vbar" x="{vx:.1f}" y="{vy:.1f}" '
            f'width="{bar_w*0.7:.1f}" height="{vh:.1f}" '
            f'fill="{col}" opacity="0.35"/>'
            f'</g>'
        )

    # Grid lines
    grids = " ".join(
        f'<line stroke="var(--border-s)" stroke-width="1" '
        f'x1="{px}" y1="{py+ph*f:.0f}" x2="{px+pw}" y2="{py+ph*f:.0f}"/>'
        for f in [0, 0.25, 0.5, 0.75, 1.0]
    )

    # Axis labels
    axes = "".join([
        f'<text fill="var(--label)" font-size="12" font-family="Inter,sans-serif" '
        f'text-anchor="end" x="{px-10}" y="{py+5}">${p_max:,.0f}</text>',
        f'<text fill="var(--label)" font-size="12" font-family="Inter,sans-serif" '
        f'text-anchor="end" x="{px-10}" y="{py+ph*0.5+5:.0f}">${(p_min+p_max)/2:,.0f}</text>',
        f'<text fill="var(--label)" font-size="12" font-family="Inter,sans-serif" '
        f'text-anchor="end" x="{px-10}" y="{py+ph+5:.0f}">${p_min:,.0f}</text>',
    ])

    # Ticker
    arrow  = "▲" if event.get("change_pct", 0) >= 0 else "▼"
    chg    = abs(event.get("change_pct", 0))
    vol    = event.get("volume_multiplier", 0)
    ticker = (
        f"  {event['asset']}/USDT  "
        f"${event['current_price']:,.2f}  "
        f"{arrow}{chg:.2f}%  ●  "
        f"VOL {vol:.1f}x  ●  "
    ) * 10

    return ChartData(
        w=cw, h=ch, pad_x=px, pad_y=py, plot_w=pw, plot_h=ph,
        p_min=p_min, p_max=p_max,
        polyline=polyline, area_path=area,
        ma_polyline=ma_poly,
        current_price_y=cur_y,
        candles=candle_els,
        grids=grids, axes=axes,
        ticker_text=ticker,
    )
