"""
s3-context.html — Context breakdown scene
Standalone Hyperframes sub-composition.
Duration: 9s — HUD terminal style
"""
from composer.templates.styles.design_system import css_vars, get_trend_colors, LAYOUT, TYPE


def build(event: dict, chart) -> str:
    is_pos = event.get("change_pct", 0) >= 0
    tc, _  = get_trend_colors(is_pos)
    cv     = css_vars(tc)
    arrow  = "▲" if is_pos else "▼"
    chg    = abs(event.get("change_pct", 0))
    vol    = event.get("volume_multiplier", 0)
    signal = "BULLISH" if is_pos else "BEARISH"
    asset  = event["asset"]

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
:root {{ {cv} --fw-bold:{TYPE.weight_bold}; --fw-medium:{TYPE.weight_medium}; --fw-regular:{TYPE.weight_regular}; --sz-label:{TYPE.label}px; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); overflow:hidden; font-family:var(--font); }}

[data-composition-id="s3-context"] {{
  position:relative; width:{LAYOUT.canvas_w}px; height:{LAYOUT.canvas_h}px;
  background:var(--bg); overflow:hidden;
}}

/* Background blobs */
#s3-b1 {{
  position:absolute; width:900px; height:700px; top:-200px; left:-150px;
  border-radius:50%; filter:blur(100px); opacity:0.1;
  background:radial-gradient(circle, var(--tc), transparent 70%);
}}
#s3-b2 {{
  position:absolute; width:700px; height:600px; bottom:-150px; right:-100px;
  border-radius:50%; filter:blur(100px); opacity:0.1;
  background:radial-gradient(circle, var(--blue), transparent 70%);
}}

/* Scan line */
#s3-scan {{
  position:absolute; left:0; top:-4px; width:{LAYOUT.canvas_w}px; height:3px;
  background:linear-gradient(90deg, transparent, var(--tc), transparent);
  opacity:0; z-index:10;
}}

/* HUD bars */
#s3-topbar, #s3-botbar {{
  position:absolute; left:0; width:{LAYOUT.canvas_w}px; padding:0 60px;
  height:52px; display:flex; align-items:center; justify-content:space-between;
  border-color:var(--border); border-style:solid; z-index:5; opacity:0;
}}
#s3-topbar {{ top:0; border-width:0 0 1px 0; }}
#s3-botbar {{ bottom:0; border-width:1px 0 0 0; }}
.s3-hud {{ font-size:11px; font-weight:var(--fw-medium); color:var(--label); letter-spacing:0.2em; text-transform:uppercase; }}

/* Stat columns */
#s3-inner {{
  position:absolute; top:52px; bottom:52px; left:0; right:0;
  display:flex; align-items:stretch;
}}
.s3-col {{
  flex:1; padding:60px 72px;
  display:flex; flex-direction:column; gap:16px;
  opacity:0; transform:translateY(40px);
}}
.s3-div {{ width:1px; background:var(--border); margin:60px 0; flex-shrink:0; }}
.s3-num {{ font-size:11px; font-weight:var(--fw-bold); color:var(--tc); letter-spacing:0.15em; }}
.s3-lbl {{ font-size:11px; font-weight:var(--fw-medium); color:var(--label); letter-spacing:0.2em; text-transform:uppercase; }}
.s3-header {{ display:flex; align-items:center; gap:16px; }}
.s3-rule {{ height:1px; background:var(--border); width:100%; }}
.s3-val {{ font-size:88px; font-weight:var(--fw-bold); font-variant-numeric:tabular-nums; line-height:1; letter-spacing:-0.02em; }}
.s3-unit {{ font-size:11px; color:var(--label); letter-spacing:0.2em; text-transform:uppercase; margin-top:-8px; }}
.s3-sub {{ font-size:14px; color:var(--text-3); letter-spacing:0.04em; margin-top:8px; }}

/* Grain */
@keyframes hf-grain {{
  0%,100% {{ transform:translate(0,0); }} 10% {{ transform:translate(-5%,-5%); }}
  20% {{ transform:translate(-10%,5%); }} 30% {{ transform:translate(5%,-10%); }}
  40% {{ transform:translate(-5%,15%); }} 50% {{ transform:translate(-10%,5%); }}
  60% {{ transform:translate(15%,0); }} 70% {{ transform:translate(0,10%); }}
  80% {{ transform:translate(-15%,0); }} 90% {{ transform:translate(10%,5%); }}
}}
#s3-grain {{ position:absolute; inset:0; z-index:50; pointer-events:none; overflow:hidden; }}
#s3-grain::after {{
  content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%;
  background:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  opacity:0.08; animation:hf-grain 0.5s steps(1) infinite;
}}
</style>
</head>
<body>
<div data-composition-id="s3-context"
     data-start="0" data-duration="9"
     data-width="{LAYOUT.canvas_w}" data-height="{LAYOUT.canvas_h}">

  <div id="s3-b1"></div>
  <div id="s3-b2"></div>
  <div id="s3-scan"></div>
  <div id="s3-grain"></div>

  <div id="s3-topbar">
    <span class="s3-hud">CRYPTOVIZ // MARKET ANALYSIS</span>
    <span class="s3-hud">{asset}/USDT · 1H · LIVE</span>
  </div>

  <div id="s3-inner">
    <div class="s3-col" id="c1">
      <div class="s3-header">
        <span class="s3-num">01</span>
        <span class="s3-lbl">Session High</span>
      </div>
      <div class="s3-rule"></div>
      <div class="s3-val" style="color:var(--tc);">${chart.p_max:,.0f}</div>
      <div class="s3-unit">USD</div>
      <div class="s3-sub">{arrow} {chg:.2f}% confirmed move</div>
    </div>
    <div class="s3-div"></div>
    <div class="s3-col" id="c2">
      <div class="s3-header">
        <span class="s3-num">02</span>
        <span class="s3-lbl">Volume Spike</span>
      </div>
      <div class="s3-rule"></div>
      <div class="s3-val" style="color:var(--blue);">{vol:.1f}x</div>
      <div class="s3-unit">Above Baseline</div>
      <div class="s3-sub">abnormal accumulation detected</div>
    </div>
    <div class="s3-div"></div>
    <div class="s3-col" id="c3">
      <div class="s3-header">
        <span class="s3-num">03</span>
        <span class="s3-lbl">Signal</span>
      </div>
      <div class="s3-rule"></div>
      <div class="s3-val" style="color:var(--tc);font-size:60px;">{signal}</div>
      <div class="s3-unit">Market Condition</div>
      <div class="s3-sub">{asset} · volume-confirmed</div>
    </div>
  </div>

  <div id="s3-botbar">
    <span class="s3-hud">RANGE ${chart.p_min:,.0f} – ${chart.p_max:,.0f}</span>
    <span class="s3-hud">MOVE {chg:.2f}% · SPIKE {vol:.1f}x AVG</span>
  </div>

</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});

tl.to("#s3-scan", {{ opacity:1, y:{LAYOUT.canvas_h}, duration:0.55, ease:"power2.in" }}, 0.1);
tl.set("#s3-scan", {{ opacity:0 }}, 0.65);
tl.to("#s3-topbar", {{ opacity:1, duration:0.3 }}, 0.2);
tl.to("#s3-botbar", {{ opacity:1, duration:0.3 }}, 0.3);
tl.to("#c1", {{ opacity:1, y:0, duration:0.5, ease:"expo.out" }}, 0.4);
tl.to("#c2", {{ opacity:1, y:0, duration:0.5, ease:"expo.out" }}, 0.62);
tl.to("#c3", {{ opacity:1, y:0, duration:0.5, ease:"expo.out" }}, 0.84);

window.__timelines["s3-context"] = tl;
</script>
</body>
</html>"""
