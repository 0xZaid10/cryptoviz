"""
s4-summary.html — Summary + fade to black (FINAL scene)
Standalone Hyperframes sub-composition.
Duration: 5s
"""
from composer.templates.styles.design_system import css_vars, get_trend_colors, LAYOUT, TYPE


def build(event: dict) -> str:
    is_pos = event.get("change_pct", 0) >= 0
    tc, _  = get_trend_colors(is_pos)
    cv     = css_vars(tc)
    arrow  = "▲" if is_pos else "▼"
    chg    = abs(event.get("change_pct", 0))
    vol    = event.get("volume_multiplier", 0)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
:root {{ {cv} --fw-bold:{TYPE.weight_bold}; --fw-medium:{TYPE.weight_medium}; --fw-regular:{TYPE.weight_regular}; --sz-label:{TYPE.label}px; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); overflow:hidden; font-family:var(--font); }}

[data-composition-id="s4-summary"] {{
  position:relative; width:{LAYOUT.canvas_w}px; height:{LAYOUT.canvas_h}px;
  background:var(--bg); overflow:hidden;
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:36px;
}}
#s4-eye {{ font-size:var(--sz-label); color:var(--text-3); letter-spacing:0.25em; text-transform:uppercase; }}
#s4-txt {{
  font-size:56px; font-weight:var(--fw-bold); color:var(--text);
  text-align:center; max-width:1500px; line-height:1.25; letter-spacing:-0.01em;
}}
#s4-txt em {{ color:var(--tc); font-style:normal; }}
#s4-rule {{ width:0; height:1px; background:var(--border); }}
#s4-brand {{ font-size:var(--sz-label); color:var(--text-3); letter-spacing:0.12em; text-transform:uppercase; }}
#s4-ov {{ position:absolute; inset:0; background:#000; opacity:0; pointer-events:none; }}
</style>
</head>
<body>
<div data-composition-id="s4-summary"
     data-start="0" data-duration="5"
     data-width="{LAYOUT.canvas_w}" data-height="{LAYOUT.canvas_h}">
  <div id="s4-eye">CryptoViz · Market Intelligence</div>
  <div id="s4-txt">
    {event['asset']} volume alert —
    <em>{arrow} {chg:.1f}%</em> on <em>{vol:.1f}x</em> average volume
  </div>
  <div id="s4-rule"></div>
  <div id="s4-brand">Powered by HeyGen Hyperframes</div>
  <div id="s4-ov"></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
tl.from("#s4-eye",   {{ opacity:0, duration:0.4 }}, 0.3);
tl.from("#s4-txt",   {{ y:28, opacity:0, duration:0.6, ease:"power3.out" }}, 0.5);
tl.to("#s4-rule",    {{ width:480, duration:0.6, ease:"expo.out" }}, 1.3);
tl.from("#s4-brand", {{ opacity:0, duration:0.4 }}, 1.8);
tl.to("#s4-ov",      {{ opacity:1, duration:1.3, ease:"power2.in" }}, 3.5);
window.__timelines["s4-summary"] = tl;
</script>
</body>
</html>"""
