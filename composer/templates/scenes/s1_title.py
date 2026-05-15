"""
s1-title.html — Title card scene
Standalone Hyperframes sub-composition.
Duration: 6.5s
Techniques: LED dot matrix bg, animated gradient mesh blobs, HUD corner labels, particles
"""
import math
from composer.templates.styles.design_system import css_vars, get_trend_colors, LAYOUT, TYPE


def _particles(tc: str, count: int = 55) -> str:
    seed = 42
    def rng():
        nonlocal seed
        seed = (seed + 0x6D2B79F5) & 0xFFFFFFFF
        t = seed ^ (seed >> 15)
        t = (t * (1 | (seed >> 7))) & 0xFFFFFFFF
        t = (t + ((t ^ (t >> 7)) * (61 | (t >> 14)))) & 0xFFFFFFFF
        return (t ^ (t >> 14)) / 4294967296
    els = []
    for i in range(count):
        x, y = rng()*1920, rng()*1080
        r    = 0.8 + rng()*2.5
        rng()  # spd — consumed but used in gsap
        op   = min(0.05 + r*0.03, 0.16)
        els.append(f'<circle id="p{i}" cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{tc}" opacity="{op:.2f}"/>')
    return "\n      ".join(els)


def _particle_gsap(count: int = 55) -> str:
    seed = 42
    def rng():
        nonlocal seed
        seed = (seed + 0x6D2B79F5) & 0xFFFFFFFF
        t = seed ^ (seed >> 15)
        t = (t * (1 | (seed >> 7))) & 0xFFFFFFFF
        t = (t + ((t ^ (t >> 7)) * (61 | (t >> 14)))) & 0xFFFFFFFF
        return (t ^ (t >> 14)) / 4294967296
    lines = []
    for i in range(count):
        rng(); rng()          # x, y
        r   = 0.8 + rng()*2.5
        spd = 0.3 + rng()*0.7
        dur = 3 + spd * 2
        rep = max(math.ceil(6.5 / dur) - 1, 0)
        t   = (i / count) * 0.9
        lines.append(
            f'  tl.to("#p{i}", {{y:-{40+spd*60:.0f}, opacity:0, '
            f'duration:{dur:.1f}, ease:"none", repeat:{rep}}}, {t:.2f});'
        )
    return "\n".join(lines)


def build(event: dict) -> str:
    is_pos = event.get("change_pct", 0) >= 0
    tc, _  = get_trend_colors(is_pos)
    cv     = css_vars(tc)
    arrow  = "▲" if is_pos else "▼"
    chg    = abs(event.get("change_pct", 0))
    vol    = event.get("volume_multiplier", 0)
    asset  = event["asset"]
    price  = event["current_price"]
    etype  = event["type"].replace("_", " ").upper()
    ptcls  = _particles(tc)
    p_gsap = _particle_gsap()

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
:root {{ {cv} --fw-bold:{TYPE.weight_bold}; --fw-medium:{TYPE.weight_medium}; --fw-regular:{TYPE.weight_regular}; --sz-label:{TYPE.label}px; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); overflow:hidden; font-family:var(--font); }}

[data-composition-id="s1-title"] {{
  position:relative; width:{LAYOUT.canvas_w}px; height:{LAYOUT.canvas_h}px;
  background:var(--bg); overflow:hidden;
}}

/* LED dot matrix */
#s1-led {{
  position:absolute; inset:0; z-index:0;
  background-image:radial-gradient(circle, rgba(255,255,255,0.055) 1px, transparent 1px);
  background-size:24px 24px;
}}

/* Animated gradient mesh */
#s1-mesh {{ position:absolute; inset:0; z-index:1; overflow:hidden; }}
.blob {{ position:absolute; border-radius:50%; filter:blur(80px); opacity:0; }}
#blob1 {{
  width:900px; height:700px; top:-150px; left:-200px;
  background:radial-gradient(circle, color-mix(in srgb, var(--tc) 28%, transparent), transparent 70%);
  animation:blob1d 8s ease-in-out infinite alternate;
}}
#blob2 {{
  width:700px; height:600px; bottom:-100px; right:-100px;
  background:radial-gradient(circle, color-mix(in srgb, var(--blue) 22%, transparent), transparent 70%);
  animation:blob2d 11s ease-in-out infinite alternate;
}}
#blob3 {{
  width:500px; height:400px; top:45%; left:55%;
  background:radial-gradient(circle, color-mix(in srgb, var(--tc) 14%, transparent), transparent 70%);
  animation:blob3d 13s ease-in-out infinite alternate;
}}
@keyframes blob1d {{ from {{ transform:translate(0,0) scale(1); }} to {{ transform:translate(70px,55px) scale(1.1); }} }}
@keyframes blob2d {{ from {{ transform:translate(0,0) scale(1); }} to {{ transform:translate(-55px,-40px) scale(1.15); }} }}
@keyframes blob3d {{ from {{ transform:translate(-50%,-50%) scale(1); }} to {{ transform:translate(-50%,-50%) scale(1.22) rotate(18deg); }} }}

/* Vignette */
#s1-vig {{
  position:absolute; inset:0; z-index:3; pointer-events:none;
  background:radial-gradient(ellipse at 50% 50%, transparent 30%, rgba(5,5,5,0.72) 100%);
}}

/* Grain */
@keyframes hf-grain {{
  0%,100% {{ transform:translate(0,0); }} 10% {{ transform:translate(-5%,-5%); }}
  20% {{ transform:translate(-10%,5%); }} 30% {{ transform:translate(5%,-10%); }}
  40% {{ transform:translate(-5%,15%); }} 50% {{ transform:translate(-10%,5%); }}
  60% {{ transform:translate(15%,0); }} 70% {{ transform:translate(0,10%); }}
  80% {{ transform:translate(-15%,0); }} 90% {{ transform:translate(10%,5%); }}
}}
#s1-grain {{ position:absolute; inset:0; z-index:4; pointer-events:none; overflow:hidden; }}
#s1-grain::after {{
  content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%;
  background:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  opacity:0.1; animation:hf-grain 0.5s steps(1) infinite;
}}

/* Particles */
#s1-ptcl {{ position:absolute; inset:0; z-index:2; pointer-events:none; overflow:hidden; }}

/* HUD corners */
.hud {{ position:absolute; z-index:6; opacity:0; display:flex; align-items:center; gap:10px; }}
#hud-tl {{ top:48px; left:60px; }}
#hud-tr {{ top:48px; right:60px; }}
#hud-bl {{ bottom:48px; left:60px; }}
#hud-br {{ bottom:48px; right:60px; }}
.hud-t {{
  font-size:11px; font-weight:var(--fw-medium);
  color:var(--text-2); letter-spacing:0.2em; text-transform:uppercase;
  font-family:var(--font);
}}
.hud-sep {{ color:var(--text-3); font-size:11px; }}

/* Main content */
#s1-content {{
  position:absolute; inset:0; z-index:5;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:22px;
}}
#s1-overline {{
  font-size:13px; color:var(--blue); letter-spacing:0.3em;
  text-transform:uppercase; font-family:var(--font);
}}
#s1-asset {{
  font-size:158px; font-weight:var(--fw-bold); color:var(--text);
  letter-spacing:-0.04em; line-height:1; font-family:var(--font);
  position:relative; display:inline-block;
}}
/* Shimmer on asset */
#s1-asset .shimmer-mask {{
  position:absolute; top:0; left:0; width:100%; height:100%;
  pointer-events:none;
  background:linear-gradient(120deg,
    transparent 0%,
    transparent calc(var(--sp,-20%) - 10%),
    rgba(255,255,255,0.5) var(--sp,-20%),
    transparent calc(var(--sp,-20%) + 10%),
    transparent 100%);
  mix-blend-mode:overlay;
}}
#s1-type {{
  font-size:20px; color:var(--text-3); letter-spacing:0.22em;
  text-transform:uppercase; font-family:var(--font);
}}
#s1-price {{
  font-size:78px; font-weight:var(--fw-bold); color:var(--tc);
  font-variant-numeric:tabular-nums; font-family:var(--font);
  position:relative; display:inline-block;
}}
#s1-price .shimmer-mask {{
  position:absolute; top:0; left:0; width:100%; height:100%;
  pointer-events:none;
  background:linear-gradient(120deg,
    transparent 0%,
    transparent calc(var(--sp,-20%) - 10%),
    rgba(255,255,255,0.45) var(--sp,-20%),
    transparent calc(var(--sp,-20%) + 10%),
    transparent 100%);
  mix-blend-mode:overlay;
}}
#s1-bar {{ display:flex; align-items:center; }}
#s1-ll, #s1-rl {{ width:0; height:2px; background:var(--tc); }}
#s1-dot {{
  width:10px; height:10px; border-radius:50%; background:var(--tc);
  margin:0 14px; opacity:0; box-shadow:0 0 20px var(--tc);
}}
</style>
</head>
<body>
<div data-composition-id="s1-title"
     data-start="0" data-duration="6.5"
     data-width="{LAYOUT.canvas_w}" data-height="{LAYOUT.canvas_h}">

  <div id="s1-led"></div>
  <div id="s1-mesh">
    <div class="blob" id="blob1"></div>
    <div class="blob" id="blob2"></div>
    <div class="blob" id="blob3"></div>
  </div>
  <div id="s1-vig"></div>
  <div id="s1-grain"></div>

  <div id="s1-ptcl">
    <svg width="{LAYOUT.canvas_w}" height="{LAYOUT.canvas_h}" style="position:absolute;inset:0;">
      {ptcls}
    </svg>
  </div>

  <!-- HUD -->
  <div class="hud" id="hud-tl"><span class="hud-t">CryptoViz · Live Alert</span></div>
  <div class="hud" id="hud-tr">
    <span class="hud-t">{asset}/USDT</span>
    <span class="hud-sep">·</span>
    <span class="hud-t">VOL {vol:.1f}x</span>
  </div>
  <div class="hud" id="hud-bl"><span class="hud-t">{etype}</span></div>
  <div class="hud" id="hud-br"><span class="hud-t">{arrow} {chg:.2f}%</span></div>

  <!-- Content -->
  <div id="s1-content">
    <div id="s1-overline">CryptoViz · Live Alert</div>
    <div id="s1-asset">{asset}<div class="shimmer-mask"></div></div>
    <div id="s1-type">{etype}</div>
    <div id="s1-price">{arrow} ${price:,.2f}<div class="shimmer-mask"></div></div>
    <div id="s1-bar">
      <div id="s1-ll"></div>
      <div id="s1-dot"></div>
      <div id="s1-rl"></div>
    </div>
  </div>

</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});

// Mesh blobs
tl.to(".blob", {{ opacity:1, duration:1.2, ease:"power2.out", stagger:0.18 }}, 0);
// HUD
tl.to("#hud-tl", {{ opacity:1, duration:0.35 }}, 0.1);
tl.to("#hud-tr", {{ opacity:1, duration:0.35 }}, 0.2);
tl.to("#hud-bl", {{ opacity:1, duration:0.35 }}, 0.3);
tl.to("#hud-br", {{ opacity:1, duration:0.35 }}, 0.4);
// Particles
{p_gsap}
// Content
tl.from("#s1-overline", {{ y:18, opacity:0, duration:0.4, ease:"expo.out" }}, 0.1);
tl.from("#s1-asset",    {{ y:80, opacity:0, skewY:2, duration:0.55, ease:"expo.out" }}, 0.25);
tl.to("#s1-asset", {{ textShadow:"0 0 110px var(--tc)", duration:0.3, yoyo:true, repeat:1 }}, 0.6);
// Shimmer sweeps
tl.fromTo("#s1-asset",  {{"--sp":"-20%"}}, {{"--sp":"120%", duration:0.7, ease:"power2.inOut"}}, 0.55);
tl.from("#s1-type",  {{ y:18, opacity:0, duration:0.4, ease:"power3.out" }}, 0.55);
tl.from("#s1-price", {{ y:28, opacity:0, duration:0.45, ease:"power2.out" }}, 0.72);
tl.fromTo("#s1-price", {{"--sp":"-20%"}}, {{"--sp":"120%", duration:0.65, ease:"power2.inOut"}}, 0.78);
// Expanding bar
tl.to("#s1-ll",  {{ width:300, duration:0.55, ease:"expo.out" }}, 0.95);
tl.to("#s1-dot", {{ opacity:1, duration:0.2, ease:"back.out(2)" }}, 1.38);
tl.to("#s1-rl",  {{ width:300, duration:0.55, ease:"expo.out" }}, 1.42);

window.__timelines["s1-title"] = tl;
</script>
</body>
</html>"""
