"""
s2-chart.html — Live chart scene
Standalone Hyperframes sub-composition.
Duration: 17s
"""
from composer.templates.styles.design_system import css_vars, get_trend_colors, LAYOUT, TYPE


def build(event: dict, chart) -> str:
    is_pos = event.get("change_pct", 0) >= 0
    tc, _  = get_trend_colors(is_pos)
    cv     = css_vars(tc)
    arrow  = "▲" if is_pos else "▼"
    chg    = abs(event.get("change_pct", 0))
    vol    = event.get("volume_multiplier", 0)
    price  = event["current_price"]
    asset  = event["asset"]
    signal = "BULLISH" if is_pos else "BEARISH"
    pw     = LAYOUT.canvas_w - chart.w
    candles = "\n      ".join(chart.candles)
    pulse_cycles = int(17 / 1.2) - 1

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
:root {{ {cv} --fw-bold:{TYPE.weight_bold}; --fw-medium:{TYPE.weight_medium}; --fw-regular:{TYPE.weight_regular}; --sz-label:{TYPE.label}px; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); overflow:hidden; font-family:var(--font); }}

[data-composition-id="s2-chart"] {{
  position:relative; width:{LAYOUT.canvas_w}px; height:{LAYOUT.canvas_h}px;
  background:var(--bg); overflow:hidden;
}}

/* Grain */
@keyframes hf-grain {{
  0%,100% {{ transform:translate(0,0); }} 10% {{ transform:translate(-5%,-5%); }}
  20% {{ transform:translate(-10%,5%); }} 30% {{ transform:translate(5%,-10%); }}
  40% {{ transform:translate(-5%,15%); }} 50% {{ transform:translate(-10%,5%); }}
  60% {{ transform:translate(15%,0); }} 70% {{ transform:translate(0,10%); }}
  80% {{ transform:translate(-15%,0); }} 90% {{ transform:translate(10%,5%); }}
}}
#s2-grain {{ position:absolute; inset:0; z-index:50; pointer-events:none; overflow:hidden; }}
#s2-grain::after {{
  content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%;
  background:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  opacity:0.07; animation:hf-grain 0.5s steps(1) infinite;
}}

/* Chart header */
#s2-hdr {{ position:absolute; left:88px; top:55px; display:flex; flex-direction:column; gap:10px; }}
#s2-htag {{ font-size:var(--sz-label); color:var(--label); letter-spacing:0.18em; text-transform:uppercase; }}
#s2-hrow {{ display:flex; align-items:baseline; gap:20px; }}
#s2-hprice {{ font-size:50px; font-weight:var(--fw-bold); font-variant-numeric:tabular-nums; color:var(--text); }}
#s2-hchg   {{ font-size:22px; font-weight:var(--fw-bold); color:var(--tc); }}

/* Vertical divider */
#s2-div {{ position:absolute; left:{chart.w}px; top:40px; width:1px; height:1000px; background:var(--border); }}

/* Data panel */
#s2-panel {{
  position:absolute; right:0; top:0; width:{pw}px; height:{LAYOUT.canvas_h}px;
  padding:80px 52px; display:flex; flex-direction:column; justify-content:center; gap:0;
  clip-path:inset(0 100% 0 0);
}}
.s2-tag {{ font-size:var(--sz-label); color:var(--label); letter-spacing:0.18em; text-transform:uppercase; margin-bottom:32px; }}
.s2-stat {{ padding:26px 0; }}
.s2-lbl {{ font-size:var(--sz-label); color:var(--label); letter-spacing:0.2em; text-transform:uppercase; margin-bottom:10px; }}
.s2-val {{ font-size:56px; font-weight:var(--fw-bold); font-variant-numeric:tabular-nums; line-height:1; }}
.s2-rule {{ height:1px; background:var(--border-s); }}
#s2-badge {{
  margin-top:32px; padding:13px 20px;
  border:1px solid color-mix(in srgb, var(--tc) 25%, transparent);
  display:flex; align-items:center; gap:12px;
}}
#s2-bdot {{ width:8px; height:8px; border-radius:50%; background:var(--tc); flex-shrink:0; }}
#s2-btxt {{ font-size:var(--sz-label); color:var(--tc); letter-spacing:0.15em; text-transform:uppercase; }}

/* Ticker */
#s2-ticker {{
  position:absolute; bottom:0; left:0; width:{LAYOUT.canvas_w}px; height:42px;
  background:var(--surface); border-top:1px solid var(--border);
  overflow:hidden; display:flex; align-items:center;
}}
#s2-ticker-i {{ white-space:nowrap; font-size:12px; color:var(--text-3); letter-spacing:0.08em; font-variant-numeric:tabular-nums; }}
</style>
</head>
<body>
<div data-composition-id="s2-chart"
     data-start="0" data-duration="17"
     data-width="{LAYOUT.canvas_w}" data-height="{LAYOUT.canvas_h}">

  <div id="s2-grain"></div>

  <!-- Chart header -->
  <div id="s2-hdr">
    <div id="s2-htag">{asset} / USDT · 1H Candlestick</div>
    <div id="s2-hrow">
      <div id="s2-hprice">${price:,.2f}</div>
      <div id="s2-hchg">{arrow} {chg:.2f}%</div>
    </div>
  </div>

  <!-- SVG Chart -->
  <svg width="{chart.w}" height="{chart.h}"
       viewBox="0 0 {chart.w} {chart.h}"
       style="position:absolute;left:0;top:155px;">
    <defs>
      <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"   stop-color="{tc}" stop-opacity="0.16"/>
        <stop offset="100%" stop-color="{tc}" stop-opacity="0.01"/>
      </linearGradient>
    </defs>
    {chart.grids}
    {chart.axes}
    <path id="s2-area" d="{chart.area_path}" fill="url(#ag)" opacity="0"/>
    <polyline id="s2-ma" fill="none" stroke="var(--blue)" stroke-width="1.2"
              stroke-dasharray="4,3" opacity="0.5" points="{chart.ma_polyline}"/>
    {candles}
    <line stroke="var(--blue)" stroke-width="1" stroke-dasharray="5,4"
          x1="{chart.pad_x}" y1="{chart.current_price_y:.1f}"
          x2="{chart.pad_x+chart.plot_w}" y2="{chart.current_price_y:.1f}"/>
    <rect fill="var(--blue)" rx="2"
          x="{chart.pad_x+chart.plot_w+2}" y="{chart.current_price_y-11:.0f}"
          width="108" height="22"/>
    <text fill="var(--text)" font-size="13" font-weight="700"
          font-family="Inter,sans-serif"
          x="{chart.pad_x+chart.plot_w+8}" y="{chart.current_price_y+5:.0f}">
      ${price:,.0f}
    </text>
  </svg>

  <div id="s2-div"></div>

  <!-- Panel -->
  <div id="s2-panel">
    <div class="s2-tag">{asset}/USDT · 1H</div>
    <div class="s2-stat" id="sp1">
      <div class="s2-lbl">Current Price</div>
      <div class="s2-val" style="color:var(--text);">${price:,.2f}</div>
    </div>
    <div class="s2-rule"></div>
    <div class="s2-stat" id="sp2">
      <div class="s2-lbl">Price Change</div>
      <div class="s2-val" style="color:var(--tc);">{arrow} {chg:.2f}%</div>
    </div>
    <div class="s2-rule"></div>
    <div class="s2-stat" id="sp3">
      <div class="s2-lbl">Volume Spike</div>
      <div class="s2-val" style="color:var(--blue);">{vol:.1f}x</div>
    </div>
    <div id="s2-badge">
      <div id="s2-bdot"></div>
      <div id="s2-btxt">{signal} SIGNAL</div>
    </div>
  </div>

  <!-- Ticker -->
  <div id="s2-ticker">
    <div id="s2-ticker-i">{chart.ticker_text}</div>
  </div>

</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});

tl.to("#s2-panel", {{ clipPath:"inset(0 0% 0 0)", duration:0.6, ease:"expo.out" }}, 0.2);
tl.from("#s2-hprice", {{ y:18, opacity:0, duration:0.5, ease:"expo.out" }}, 0.3);
tl.from("#s2-hchg",   {{ x:16, opacity:0, duration:0.4, ease:"expo.out" }}, 0.5);
tl.from("#s2-htag",   {{ opacity:0, duration:0.4 }}, 0.2);
tl.from("#sp1", {{ x:28, opacity:0, duration:0.45, ease:"expo.out" }}, 0.55);
tl.from("#sp2", {{ x:28, opacity:0, duration:0.45, ease:"expo.out" }}, 0.78);
tl.from("#sp3", {{ x:28, opacity:0, duration:0.45, ease:"expo.out" }}, 1.01);
tl.from("#s2-badge", {{ x:28, opacity:0, duration:0.4, ease:"power2.out" }}, 1.28);
tl.to("#s2-bdot", {{ scale:1.9, opacity:0.35, duration:0.55,
  ease:"power2.out", yoyo:true, repeat:{pulse_cycles} }}, 1.6);
tl.to(".candle", {{ opacity:1, stagger:0.055, duration:0.22, ease:"power2.out" }}, 1.0);
tl.to("#s2-area", {{ opacity:1, duration:2.5, ease:"power2.out" }}, 2.5);
const maEl = document.getElementById("s2-ma");
if (maEl && maEl.getTotalLength) {{
  const ml = maEl.getTotalLength();
  gsap.set(maEl, {{ strokeDasharray:ml, strokeDashoffset:ml }});
  tl.to(maEl, {{ strokeDashoffset:0, duration:3.8, ease:"power2.inOut" }}, 1.4);
}}
const tkEl = document.getElementById("s2-ticker-i");
if (tkEl) {{
  const tw = tkEl.scrollWidth / 2;
  tl.to(tkEl, {{ x:-tw, duration:22, ease:"none" }}, 0);
}}

window.__timelines["s2-chart"] = tl;
</script>
</body>
</html>"""
