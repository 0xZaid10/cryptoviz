"""
Composition builder — V3.
Assembles scene modules + catalog blocks into a complete Hyperframes HTML composition.
Components (grain, vignette, shimmer) are inlined directly from their source.
Shader transitions are wired as sub-compositions using data-composition-src.
"""

import subprocess
import json
import sys
from pathlib import Path

TMPL = Path(__file__).parent / "templates"
sys.path.insert(0, str(TMPL))

from styles.design_system import css_vars, get_trend_colors, TYPE, LAYOUT
from chart_data import compute as compute_chart
from scenes import s0_flash, s1_title, s2_chart, s3_context, s4_summary

COMPOSITIONS_DIR = Path(__file__).parent.parent / "compositions"


# ── Inlined component snippets ──────────────────────────────────────────────
# Copied from npx hyperframes add grain-overlay / vignette / shimmer-sweep
# Inlined here so builder has no file dependency on the components dir.

GRAIN_OVERLAY = """
<div id="grain-overlay" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:98;">
  <div class="grain-texture"></div>
</div>
<style>
  @keyframes hf-grain-noise {
    0%,100% { transform:translate(0,0); }
    10%  { transform:translate(-5%,-5%); }
    20%  { transform:translate(-10%,5%); }
    30%  { transform:translate(5%,-10%); }
    40%  { transform:translate(-5%,15%); }
    50%  { transform:translate(-10%,5%); }
    60%  { transform:translate(15%,0); }
    70%  { transform:translate(0,10%); }
    80%  { transform:translate(-15%,0); }
    90%  { transform:translate(10%,5%); }
  }
  #grain-overlay .grain-texture {
    position:absolute; top:-50%; left:-50%; width:200%; height:200%;
    background:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity:0.12;
    animation:hf-grain-noise 0.5s steps(1) infinite;
  }
</style>"""

VIGNETTE = """
<div id="hf-vignette" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:90;
  background:radial-gradient(ellipse at center, transparent 38%, rgba(0,0,0,0.72) 100%);"></div>"""

SHIMMER_CSS = """
  .shimmer-sweep-target { position:relative; display:inline-block; }
  .shimmer-sweep-target .shimmer-mask {
    position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none;
    background:linear-gradient(120deg,
      transparent 0%,
      transparent calc(var(--shimmer-pos,-20%) - 10%),
      rgba(255,255,255,0.55) var(--shimmer-pos,-20%),
      transparent calc(var(--shimmer-pos,-20%) + 10%),
      transparent 100%);
    mix-blend-mode:overlay;
  }"""

SHIMMER_JS = """
  // Auto-inject shimmer masks
  document.querySelectorAll(".shimmer-sweep-target").forEach(el => {
    if (!el.querySelector(".shimmer-mask")) {
      const m = document.createElement("div");
      m.className = "shimmer-mask";
      el.appendChild(m);
    }
  });
  // Shimmer sweep on price text during S1 (t=1.2 → 1.8s)
  tl.fromTo("#s1-price", {"--shimmer-pos":"-20%"}, {"--shimmer-pos":"120%",
    duration:0.8, ease:"power2.inOut"}, 1.2);
  // Shimmer on asset name (t=1.0 → 1.6s)
  tl.fromTo("#s1-asset", {"--shimmer-pos":"-20%"}, {"--shimmer-pos":"120%",
    duration:0.7, ease:"power2.inOut"}, 1.0);"""


# ── Helpers ─────────────────────────────────────────────────────────────────

def get_audio_duration(audio_path: Path) -> float:
    try:
        r = subprocess.run(
            ["ffprobe","-v","quiet","-print_format","json","-show_format",str(audio_path)],
            capture_output=True, text=True, timeout=10
        )
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return None


def transition_block(src: str, start: float, duration: float, track: int) -> str:
    """Shader transition sub-composition div."""
    if not (COMPOSITIONS_DIR / src).exists():
        return f"<!-- transition {src} not installed -->"
    return (
        f'<div class="clip" '
        f'data-composition-src="compositions/{src}" '
        f'data-start="{start}" data-duration="{duration}" '
        f'data-track-index="{track}" '
        f'data-width="{LAYOUT.canvas_w}" data-height="{LAYOUT.canvas_h}">'
        f'</div>'
    )


def build_captions(words: list, audio_path: Path = None,
                   scene_start: float = 7.0) -> str:
    """Timed caption divs — launch-video pattern."""
    if not words:
        return "<!-- no transcript -->"

    if audio_path and audio_path.exists():
        dur = get_audio_duration(audio_path)
        if dur and words[-1]["end"] > dur * 1.1:
            print(f"  [Builder] Warning: caption timestamps may drift")

    result = []
    for gi, grp in enumerate([words[i:i+7] for i in range(0, len(words), 7)]):
        if not grp:
            continue
        gs  = grp[0]["start"] + scene_start
        ge  = grp[-1]["end"]  + scene_start
        dur = max(ge - gs, 0.3)
        text = " ".join(w["text"] for w in grp)
        result.append(
            f'<div class="cap clip" '
            f'data-start="{gs:.3f}" data-duration="{dur:.3f}" '
            f'data-track-index="{50 + gi}">{text}</div>'
        )
    return "\n  ".join(result)


# ── Main build ───────────────────────────────────────────────────────────────

def build(event: dict, script: str, words: list = None,
          audio_path: Path = None) -> str:
    """
    Build a complete Hyperframes HTML composition.

    Timeline (38s):
      0.0–0.5s   S0 alert flash
      0.5–7.0s   S1 title (LED bg + mesh + HUD + particles)
      6.2–7.0s   glitch transition (S1→S2)
      7.0–24.0s  S2 chart
      23.2–24.0s chromatic-radial-split (S2→S3)
      24.0–33.0s S3 context (HUD terminal)
      32.2–33.0s cinematic-zoom (S3→S4)
      33.0–38.0s S4 summary + fade to black
    """
    is_positive = event.get("change_pct", 0) >= 0
    trend_color, _ = get_trend_colors(is_positive)
    cv    = css_vars(trend_color)
    chart = compute_chart(event, trend_color)

    # Scenes
    s0 = s0_flash.html()
    s1 = s1_title.html(event, trend_color)
    s2 = s2_chart.html(event, chart, trend_color)
    s3 = s3_context.html(event, chart, trend_color)
    s4 = s4_summary.html(event)

    # Shader transitions
    t12 = transition_block("glitch.html",                 6.2, 0.8, 10)
    t23 = transition_block("chromatic-radial-split.html", 23.2, 0.8, 11)
    t34 = transition_block("cinematic-zoom.html",         32.2, 0.8, 12)

    # Captions
    caps = build_captions(words or [], audio_path=audio_path, scene_start=7.0)

    # CSS
    css_all = "\n".join([
        s1_title.css(), s2_chart.css(),
        s3_context.css(), s4_summary.css(),
        SHIMMER_CSS,
    ])

    # GSAP
    gsap_all = "\n".join([
        s0_flash.gsap(), s1_title.gsap(),
        s2_chart.gsap(), s3_context.gsap(),
        s4_summary.gsap(),
        SHIMMER_JS,
    ])

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
:root {{
  {cv}
  --fw-bold:{TYPE.weight_bold};
  --fw-medium:{TYPE.weight_medium};
  --fw-regular:{TYPE.weight_regular};
  --sz-label:{TYPE.label}px;
  --sz-micro:{TYPE.micro}px;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg); overflow:hidden; font-family:var(--font); color:var(--text); }}
.scene {{ position:absolute; top:0; left:0; width:{LAYOUT.canvas_w}px; height:{LAYOUT.canvas_h}px; }}
.cap {{
  position:absolute; bottom:68px; left:50%;
  transform:translateX(-50%); text-align:center;
  font-family:var(--font); font-weight:{TYPE.weight_medium}; font-size:30px;
  color:rgba(240,235,220,0.94); letter-spacing:-0.005em;
  background:rgba(5,5,5,0.75); padding:11px 30px; border-radius:100px;
  backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
  z-index:9999; pointer-events:none; white-space:nowrap; max-width:1600px;
  border:1px solid rgba(255,255,255,0.06);
}}
{css_all}
</style>
</head>
<body>
<div data-composition-id="root"
     data-start="0" data-duration="38"
     data-width="{LAYOUT.canvas_w}" data-height="{LAYOUT.canvas_h}"
     style="position:relative;width:{LAYOUT.canvas_w}px;height:{LAYOUT.canvas_h}px;
            overflow:hidden;background:var(--bg);">

  {s0}
  {s1}
  {t12}
  {s2}
  {t23}
  {s3}
  {t34}
  {s4}

  <!-- Global overlays (on top of everything except captions) -->
  {VIGNETTE}
  {GRAIN_OVERLAY}

  <!-- Captions -->
  {caps}

</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{gsap_all}
window.__timelines["root"] = tl;
</script>
</body>
</html>"""
