"""
s0-flash.html — Alert flash scene
Standalone Hyperframes sub-composition.
Duration: 0.5s
"""
from composer.templates.styles.design_system import css_vars, get_trend_colors, LAYOUT, TYPE


def build(event: dict) -> str:
    is_pos = event.get("change_pct", 0) >= 0
    tc, _  = get_trend_colors(is_pos)
    cv     = css_vars(tc)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
:root {{ {cv} --fw-bold:{TYPE.weight_bold}; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--tc); overflow:hidden; }}
[data-composition-id="s0-flash"] {{
  position:relative; width:{LAYOUT.canvas_w}px; height:{LAYOUT.canvas_h}px;
  background:var(--tc); overflow:hidden;
}}
#scan {{
  position:absolute; top:0; left:0; width:100%; height:4px;
  background:linear-gradient(90deg, transparent, rgba(255,255,255,0.9), transparent);
}}
</style>
</head>
<body>
<div data-composition-id="s0-flash"
     data-start="0" data-duration="0.5"
     data-width="{LAYOUT.canvas_w}" data-height="{LAYOUT.canvas_h}">
  <div id="scan"></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
tl.from("#scan", {{ opacity:0, duration:0.04 }}, 0);
tl.to("#scan",   {{ y:{LAYOUT.canvas_h}, duration:0.42, ease:"power2.in" }}, 0.05);
window.__timelines["s0-flash"] = tl;
</script>
</body>
</html>"""
