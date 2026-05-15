"""
Project builder — single index.html approach.
All scenes inline in one file. No sub-compositions.
This is the pattern that actually works with Hyperframes CLI.
"""

import json, math, sys
from datetime import datetime
from pathlib import Path

ROOT   = Path(__file__).parent.parent
PARENT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PARENT))
try:    import cryptoviz_v3.config as config
except:
    try:    import config
    except: sys.path.insert(0, str(PARENT.parent)); import config

CW, CH = 1920, 1080
GSAP   = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"


def trend_color(event):
    return "#00FF88" if event.get("change_pct", 0) >= 0 else "#FF3344"

def _name(event):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"alert_{event.get('asset','X')}_{event.get('type','').replace('_','-')}_{ts}"


def compute_chart(event, tc):
    prices  = event.get("price_history", [])
    volumes = event.get("volume_history", [])
    cw,ch   = 1200, 700
    px,py   = 88, 65
    vol_h   = 130
    pw = cw-px*2; ph = ch-py*2-vol_h
    pmin = min(prices) if prices else 0
    pmax = max(prices) if prices else 1
    pr   = pmax-pmin or 1
    n    = len(prices)
    def xx(i): return px+(i/max(n-1,1))*pw
    def yy(p): return py+(1-(p-pmin)/pr)*ph
    if n > 1:
        pts    = " ".join(f"{xx(i):.1f},{yy(p):.1f}" for i,p in enumerate(prices))
        area   = f"M {px} {py+ph} " + " ".join(f"L {xx(i):.1f} {yy(p):.1f}" for i,p in enumerate(prices)) + f" L {px+pw} {py+ph} Z"
        ma_pts = []
        for i in range(n):
            w=prices[max(0,i-9):i+1]; ma_pts.append(f"{xx(i):.1f},{yy(sum(w)/len(w)):.1f}")
        ma = " ".join(ma_pts)
    else:
        mid=py+ph/2; pts=ma=f"{px},{mid:.1f} {px+pw},{mid:.1f}"; area=""
    cur_y = yy(event["current_price"])
    chunk=max(1,n//20); candles=[]; vmax=max(volumes) if volumes else 1; bw=pw/max(n//chunk,1)
    for ci in range(0,n-chunk+1,chunk):
        seg=prices[ci:ci+chunk]; vi=volumes[ci] if ci<len(volumes) else 0
        o,c_,h_,l_=seg[0],seg[-1],max(seg),min(seg); bull=c_>=o
        col=tc if bull else ("#FF3344" if tc=="#00FF88" else "#00FF88")
        cx2=px+(ci//chunk+0.5)*bw; bt=yy(max(o,c_)); bb=yy(min(o,c_)); bh=max(bb-bt,2)
        hy=yy(h_); ly=yy(l_); hw=bw*0.36; vh=max((vi/vmax)*(vol_h-10),2)
        vx=px+(ci//chunk)*bw; vy=ch-15-vh
        candles.append(
            f'<g class="candle" style="opacity:0">'
            f'<line x1="{cx2:.1f}" y1="{hy:.1f}" x2="{cx2:.1f}" y2="{ly:.1f}" stroke="{col}" stroke-width="1.2"/>'
            f'<rect x="{cx2-hw:.1f}" y="{bt:.1f}" width="{hw*2:.1f}" height="{bh:.1f}" fill="{col}" opacity="0.9"/>'
            f'<rect x="{vx:.1f}" y="{vy:.1f}" width="{bw*0.7:.1f}" height="{vh:.1f}" fill="{col}" opacity="0.35" class="vbar"/>'
            f'</g>'
        )
    grids = " ".join(f'<line stroke="#0a0a0a" stroke-width="1" x1="{px}" y1="{py+ph*f:.0f}" x2="{px+pw}" y2="{py+ph*f:.0f}"/>' for f in [0,.25,.5,.75,1])
    axes  = (f'<text fill="#555" font-size="12" font-family="Inter" text-anchor="end" x="{px-10}" y="{py+5}">${pmax:,.0f}</text>'
             f'<text fill="#555" font-size="12" font-family="Inter" text-anchor="end" x="{px-10}" y="{py+ph*.5+5:.0f}">${(pmin+pmax)/2:,.0f}</text>'
             f'<text fill="#555" font-size="12" font-family="Inter" text-anchor="end" x="{px-10}" y="{py+ph+5:.0f}">${pmin:,.0f}</text>')
    arrow="▲" if event.get("change_pct",0)>=0 else "▼"
    ticker=(f"  {event['asset']}/USDT  ${event['current_price']:,.2f}  {arrow}{abs(event.get('change_pct',0)):.2f}%  ●  VOL {event.get('volume_multiplier',0):.1f}x  ●  ")*10
    return dict(w=cw,h=ch,px=px,py=py,pw=pw,ph=ph,pmin=pmin,pmax=pmax,
                pts=pts,area=area,ma=ma,cur_y=cur_y,
                candles="\n    ".join(candles),grids=grids,axes=axes,ticker=ticker)


def _particles_svg(tc, count=55):
    seed=42
    def rng():
        nonlocal seed
        seed=(seed+0x6D2B79F5)&0xFFFFFFFF; t=seed^(seed>>15)
        t=(t*(1|(seed>>7)))&0xFFFFFFFF; t=(t+((t^(t>>7))*(61|(t>>14))))&0xFFFFFFFF
        return (t^(t>>14))/4294967296
    els=[]
    for i in range(count):
        x,y=rng()*1920,rng()*1080; r=0.8+rng()*2.5; rng(); op=min(0.05+r*0.03,0.16)
        els.append(f'<circle id="p{i}" cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{tc}" opacity="{op:.2f}"/>')
    return "\n    ".join(els)

def _particle_gsap(count=55):
    seed=42
    def rng():
        nonlocal seed
        seed=(seed+0x6D2B79F5)&0xFFFFFFFF; t=seed^(seed>>15)
        t=(t*(1|(seed>>7)))&0xFFFFFFFF; t=(t+((t^(t>>7))*(61|(t>>14))))&0xFFFFFFFF
        return (t^(t>>14))/4294967296
    lines=[]
    for i in range(count):
        rng();rng(); r=0.8+rng()*2.5; spd=0.3+rng()*0.7
        dur=3+spd*2; rep=max(math.ceil(6.5/dur)-1,0); t=0.5+(i/count)*0.9
        lines.append(f'  tl.to("#p{i}",{{y:-{40+spd*60:.0f},opacity:0,duration:{dur:.1f},ease:"none",repeat:{rep}}},{t:.2f});')
    return "\n".join(lines)


def build_html(event, words=None):
    is_pos = event.get("change_pct",0) >= 0
    tc     = trend_color(event)
    arrow  = "▲" if is_pos else "▼"
    chg    = abs(event.get("change_pct",0))
    vol    = event.get("volume_multiplier",0)
    price  = event["current_price"]
    asset  = event["asset"]
    signal = "BULLISH" if is_pos else "BEARISH"
    etype  = event["type"].replace("_"," ").upper()
    ch     = compute_chart(event, tc)
    pw     = CW - ch["w"]
    ptcls  = _particles_svg(tc)
    pgsap  = _particle_gsap()
    pc     = int(17/1.2)-1

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
:root{{
  --bg:#050505; --surface:#0d0d0d; --text:#f0f0f0;
  --text-2:#a0a0a0; --text-3:#555; --label:#666;
  --border:#1a1a1a; --border-s:#0f0f0f;
  --blue:#0066FF; --tc:{tc};
  --font:'Inter',-apple-system,sans-serif;
}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--bg);overflow:hidden;font-family:var(--font);color:var(--text);}}

/* Scene containers — position:absolute, full canvas */
.scene{{position:absolute;top:0;left:0;width:{CW}px;height:{CH}px;}}

/* ── S0 ── */
#s0{{background:var(--tc);}}
#s0-scan{{position:absolute;top:0;left:0;width:100%;height:4px;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.9),transparent);}}

/* ── S1 ── */
#s1{{background:var(--bg);}}
#s1-led{{position:absolute;inset:0;
  background-image:radial-gradient(circle,rgba(255,255,255,0.055) 1px,transparent 1px);
  background-size:24px 24px;}}
#b1{{position:absolute;width:900px;height:700px;top:-150px;left:-200px;
  border-radius:50%;filter:blur(80px);opacity:0;
  background:radial-gradient(circle,color-mix(in srgb,var(--tc) 28%,transparent),transparent 70%);}}
#b2{{position:absolute;width:700px;height:600px;bottom:-100px;right:-100px;
  border-radius:50%;filter:blur(80px);opacity:0;
  background:radial-gradient(circle,color-mix(in srgb,var(--blue) 22%,transparent),transparent 70%);}}
#b3{{position:absolute;width:500px;height:400px;top:45%;left:55%;
  border-radius:50%;filter:blur(80px);opacity:0;
  background:radial-gradient(circle,color-mix(in srgb,var(--tc) 14%,transparent),transparent 70%);}}
#s1-vig{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse at 50% 50%,transparent 30%,rgba(5,5,5,0.72) 100%);}}
.hud{{position:absolute;opacity:0;display:flex;align-items:center;gap:10px;z-index:5;}}
#hud-tl{{top:48px;left:60px;}} #hud-tr{{top:48px;right:60px;}}
#hud-bl{{bottom:48px;left:60px;}} #hud-br{{bottom:48px;right:60px;}}
.hud-t{{font-size:11px;font-weight:500;color:var(--text-2);letter-spacing:0.2em;text-transform:uppercase;}}
.hud-sep{{color:var(--text-3);font-size:11px;}}
#s1-c{{position:absolute;inset:0;z-index:4;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;}}
#s1-over{{font-size:13px;color:var(--blue);letter-spacing:0.3em;text-transform:uppercase;}}
#s1-asset{{font-size:158px;font-weight:700;color:var(--text);letter-spacing:-0.04em;line-height:1;}}
#s1-type{{font-size:20px;color:var(--text-3);letter-spacing:0.22em;text-transform:uppercase;}}
#s1-price{{font-size:78px;font-weight:700;color:var(--tc);font-variant-numeric:tabular-nums;}}
#s1-bar{{display:flex;align-items:center;}}
#s1-ll,#s1-rl{{width:0;height:2px;background:var(--tc);}}
#s1-dot{{width:10px;height:10px;border-radius:50%;background:var(--tc);margin:0 14px;opacity:0;box-shadow:0 0 20px var(--tc);}}

/* ── S2 ── */
#s2{{background:var(--bg);}}
#s2-hdr{{position:absolute;left:88px;top:55px;}}
#s2-htag{{font-size:11px;color:var(--label);letter-spacing:0.18em;text-transform:uppercase;margin-bottom:10px;}}
#s2-hrow{{display:flex;align-items:baseline;gap:20px;}}
#s2-hp{{font-size:50px;font-weight:700;font-variant-numeric:tabular-nums;color:var(--text);}}
#s2-hc{{font-size:22px;font-weight:700;color:var(--tc);}}
#s2-div{{position:absolute;left:{ch["w"]}px;top:40px;width:1px;height:1000px;background:var(--border);}}
#s2-panel{{position:absolute;right:0;top:0;width:{pw}px;height:{CH}px;
  padding:80px 52px;display:flex;flex-direction:column;justify-content:center;gap:0;
  clip-path:inset(0 100% 0 0);}}
.s2-tag{{font-size:11px;color:var(--label);letter-spacing:0.18em;text-transform:uppercase;margin-bottom:32px;}}
.s2-st{{padding:26px 0;}}
.s2-lb{{font-size:11px;color:var(--label);letter-spacing:0.2em;text-transform:uppercase;margin-bottom:10px;}}
.s2-vl{{font-size:56px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1;}}
.s2-ru{{height:1px;background:var(--border-s);}}
#s2-bdg{{margin-top:32px;padding:13px 20px;
  border:1px solid color-mix(in srgb,var(--tc) 25%,transparent);
  display:flex;align-items:center;gap:12px;}}
#s2-bdt{{width:8px;height:8px;border-radius:50%;background:var(--tc);}}
#s2-btx{{font-size:11px;color:var(--tc);letter-spacing:0.15em;text-transform:uppercase;}}
#s2-tk{{position:absolute;bottom:0;left:0;width:{CW}px;height:42px;
  background:var(--surface);border-top:1px solid var(--border);
  overflow:hidden;display:flex;align-items:center;}}
#s2-ti{{white-space:nowrap;font-size:12px;color:var(--text-3);
  letter-spacing:0.08em;font-variant-numeric:tabular-nums;}}

/* ── S3 ── */
#s3{{background:var(--bg);}}
#s3b1{{position:absolute;width:900px;height:700px;top:-200px;left:-150px;
  border-radius:50%;filter:blur(100px);opacity:0.1;
  background:radial-gradient(circle,var(--tc),transparent 70%);}}
#s3b2{{position:absolute;width:700px;height:600px;bottom:-150px;right:-100px;
  border-radius:50%;filter:blur(100px);opacity:0.1;
  background:radial-gradient(circle,var(--blue),transparent 70%);}}
#s3-scan{{position:absolute;left:0;top:-4px;width:{CW}px;height:3px;
  background:linear-gradient(90deg,transparent,var(--tc),transparent);opacity:0;z-index:10;}}
#s3-top,#s3-bot{{position:absolute;left:0;width:{CW}px;padding:0 60px;height:52px;
  display:flex;align-items:center;justify-content:space-between;
  border-color:var(--border);border-style:solid;z-index:5;opacity:0;}}
#s3-top{{top:0;border-width:0 0 1px 0;}} #s3-bot{{bottom:0;border-width:1px 0 0 0;}}
.s3h{{font-size:11px;font-weight:500;color:var(--label);letter-spacing:0.2em;text-transform:uppercase;}}
#s3-inner{{position:absolute;top:52px;bottom:52px;left:0;right:0;display:flex;align-items:stretch;}}
.s3c{{flex:1;padding:60px 72px;display:flex;flex-direction:column;gap:16px;opacity:0;}}
.s3dv{{width:1px;background:var(--border);margin:60px 0;flex-shrink:0;}}
.s3n{{font-size:11px;font-weight:700;color:var(--tc);letter-spacing:0.15em;}}
.s3l{{font-size:11px;font-weight:500;color:var(--label);letter-spacing:0.2em;text-transform:uppercase;}}
.s3hd{{display:flex;align-items:center;gap:16px;}}
.s3r{{height:1px;background:var(--border);width:100%;}}
.s3v{{font-size:88px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1;letter-spacing:-0.02em;}}
.s3u{{font-size:11px;color:var(--label);letter-spacing:0.2em;text-transform:uppercase;margin-top:-8px;}}
.s3s{{font-size:14px;color:var(--text-3);letter-spacing:0.04em;margin-top:8px;}}

/* ── S4 ── */
#s4{{background:var(--bg);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:36px;}}
#s4-eye{{font-size:11px;color:var(--text-3);letter-spacing:0.25em;text-transform:uppercase;}}
#s4-txt{{font-size:56px;font-weight:700;text-align:center;max-width:1500px;line-height:1.25;letter-spacing:-0.01em;}}
#s4-txt em{{color:var(--tc);font-style:normal;}}
#s4-rule{{width:0;height:1px;background:var(--border);}}
#s4-brand{{font-size:11px;color:var(--text-3);letter-spacing:0.12em;text-transform:uppercase;}}
#s4-ov{{position:absolute;inset:0;background:#000;opacity:0;pointer-events:none;}}
</style>
</head>
<body>
<div data-composition-id="root"
     data-start="0" data-duration="38"
     data-width="{CW}" data-height="{CH}"
     style="position:relative;width:{CW}px;height:{CH}px;overflow:hidden;background:var(--bg);">

<!-- S0: Alert flash (0–0.5s) -->
<div id="s0" class="scene clip" data-start="0" data-duration="0.5" data-track-index="1">
  <div id="s0-scan"></div>
</div>

<!-- S1: Title card (0.5–7s) -->
<div id="s1" class="scene clip" data-start="0.5" data-duration="6.5" data-track-index="2">
  <div id="s1-led"></div>
  <div id="b1"></div><div id="b2"></div><div id="b3"></div>
  <div id="s1-vig"></div>
  <div style="position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:2;">
    <svg width="{CW}" height="{CH}" style="position:absolute;inset:0;">{ptcls}</svg>
  </div>
  <div class="hud" id="hud-tl"><span class="hud-t">CryptoViz · Live Alert</span></div>
  <div class="hud" id="hud-tr"><span class="hud-t">{asset}/USDT</span><span class="hud-sep">·</span><span class="hud-t">VOL {vol:.1f}x</span></div>
  <div class="hud" id="hud-bl"><span class="hud-t">{etype}</span></div>
  <div class="hud" id="hud-br"><span class="hud-t">{arrow} {chg:.2f}%</span></div>
  <div id="s1-c">
    <div id="s1-over">CryptoViz · Live Alert</div>
    <div id="s1-asset">{asset}</div>
    <div id="s1-type">{etype}</div>
    <div id="s1-price">{arrow} ${price:,.2f}</div>
    <div id="s1-bar"><div id="s1-ll"></div><div id="s1-dot"></div><div id="s1-rl"></div></div>
  </div>
</div>

<!-- S2: Chart (7–24s) -->
<div id="s2" class="scene clip" data-start="7" data-duration="17" data-track-index="3">
  <div id="s2-hdr">
    <div id="s2-htag">{asset} / USDT · 1H Candlestick</div>
    <div id="s2-hrow"><div id="s2-hp">${price:,.2f}</div><div id="s2-hc">{arrow} {chg:.2f}%</div></div>
  </div>
  <svg width="{ch['w']}" height="{ch['h']}" viewBox="0 0 {ch['w']} {ch['h']}" style="position:absolute;left:0;top:155px;">
    <defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{tc}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{tc}" stop-opacity="0.01"/>
    </linearGradient></defs>
    {ch['grids']}{ch['axes']}
    <path id="s2-area" d="{ch['area']}" fill="url(#ag)" opacity="0"/>
    <polyline id="s2-ma" fill="none" stroke="var(--blue)" stroke-width="1.2" stroke-dasharray="4,3" opacity="0.5" points="{ch['ma']}"/>
    {ch['candles']}
    <line stroke="var(--blue)" stroke-width="1" stroke-dasharray="5,4" x1="{ch['px']}" y1="{ch['cur_y']:.1f}" x2="{ch['px']+ch['pw']}" y2="{ch['cur_y']:.1f}"/>
    <rect fill="var(--blue)" rx="2" x="{ch['px']+ch['pw']+2}" y="{ch['cur_y']-11:.0f}" width="108" height="22"/>
    <text fill="var(--text)" font-size="13" font-weight="700" font-family="Inter" x="{ch['px']+ch['pw']+8}" y="{ch['cur_y']+5:.0f}">${price:,.0f}</text>
  </svg>
  <div id="s2-div"></div>
  <div id="s2-panel">
    <div class="s2-tag">{asset}/USDT · 1H</div>
    <div class="s2-st" id="sp1"><div class="s2-lb">Current Price</div><div class="s2-vl" style="color:var(--text);">${price:,.2f}</div></div>
    <div class="s2-ru"></div>
    <div class="s2-st" id="sp2"><div class="s2-lb">Price Change</div><div class="s2-vl" style="color:var(--tc);">{arrow} {chg:.2f}%</div></div>
    <div class="s2-ru"></div>
    <div class="s2-st" id="sp3"><div class="s2-lb">Volume Spike</div><div class="s2-vl" style="color:var(--blue);">{vol:.1f}x</div></div>
    <div id="s2-bdg"><div id="s2-bdt"></div><div id="s2-btx">{signal} SIGNAL</div></div>
  </div>
  <div id="s2-tk"><div id="s2-ti">{ch['ticker']}</div></div>
</div>

<!-- S3: Context (24–33s) -->
<div id="s3" class="scene clip" data-start="24" data-duration="9" data-track-index="4">
  <div id="s3b1"></div><div id="s3b2"></div>
  <div id="s3-scan"></div>
  <div id="s3-top"><span class="s3h">CRYPTOVIZ // MARKET ANALYSIS</span><span class="s3h">{asset}/USDT · 1H · LIVE</span></div>
  <div id="s3-inner">
    <div class="s3c" id="c1">
      <div class="s3hd"><span class="s3n">01</span><span class="s3l">Session High</span></div>
      <div class="s3r"></div>
      <div class="s3v" style="color:var(--tc);">${ch['pmax']:,.0f}</div>
      <div class="s3u">USD</div>
      <div class="s3s">{arrow} {chg:.2f}% confirmed move</div>
    </div>
    <div class="s3dv"></div>
    <div class="s3c" id="c2">
      <div class="s3hd"><span class="s3n">02</span><span class="s3l">Volume Spike</span></div>
      <div class="s3r"></div>
      <div class="s3v" style="color:var(--blue);">{vol:.1f}x</div>
      <div class="s3u">Above Baseline</div>
      <div class="s3s">abnormal accumulation detected</div>
    </div>
    <div class="s3dv"></div>
    <div class="s3c" id="c3">
      <div class="s3hd"><span class="s3n">03</span><span class="s3l">Signal</span></div>
      <div class="s3r"></div>
      <div class="s3v" style="color:var(--tc);font-size:60px;">{signal}</div>
      <div class="s3u">Market Condition</div>
      <div class="s3s">{asset} · volume-confirmed</div>
    </div>
  </div>
  <div id="s3-bot"><span class="s3h">RANGE ${ch['pmin']:,.0f} – ${ch['pmax']:,.0f}</span><span class="s3h">MOVE {chg:.2f}% · SPIKE {vol:.1f}x AVG</span></div>
</div>

<!-- S4: Summary (33–38s) -->
<div id="s4" class="scene clip" data-start="33" data-duration="5" data-track-index="5">
  <div id="s4-eye">CryptoViz · Market Intelligence</div>
  <div id="s4-txt">{asset} volume alert — <em>{arrow} {chg:.1f}%</em> on <em>{vol:.1f}x</em> average volume</div>
  <div id="s4-rule"></div>
  <div id="s4-brand">Powered by HeyGen Hyperframes</div>
  <div id="s4-ov"></div>
</div>

</div>
<script src="{GSAP}"></script>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});

// S0
tl.from("#s0-scan", {{opacity:0, duration:0.04}}, 0);
tl.to("#s0-scan",   {{y:{CH}, duration:0.42, ease:"power2.in"}}, 0.05);

// S1 blobs
tl.to("#b1", {{opacity:1, x:70, y:55, scale:1.1, duration:4, ease:"sine.inOut", yoyo:true, repeat:1}}, 0.5);
tl.to("#b2", {{opacity:1, x:-55, y:-40, scale:1.15, duration:5, ease:"sine.inOut", yoyo:true, repeat:1}}, 0.5);
tl.to("#b3", {{opacity:1, scale:1.2, duration:6, ease:"sine.inOut", yoyo:true, repeat:1}}, 0.5);
// S1 HUD
tl.to("#hud-tl", {{opacity:1, duration:0.35}}, 0.6);
tl.to("#hud-tr", {{opacity:1, duration:0.35}}, 0.72);
tl.to("#hud-bl", {{opacity:1, duration:0.35}}, 0.84);
tl.to("#hud-br", {{opacity:1, duration:0.35}}, 0.96);
// S1 particles
{pgsap}
// S1 content
tl.from("#s1-over",  {{y:18, opacity:0, duration:0.4, ease:"expo.out"}}, 0.6);
tl.from("#s1-asset", {{y:80, opacity:0, skewY:2, duration:0.55, ease:"expo.out"}}, 0.75);
tl.to("#s1-asset",   {{textShadow:"0 0 110px var(--tc)", duration:0.3, yoyo:true, repeat:1}}, 1.1);
tl.from("#s1-type",  {{y:18, opacity:0, duration:0.4, ease:"power3.out"}}, 1.05);
tl.from("#s1-price", {{y:28, opacity:0, duration:0.45, ease:"power2.out"}}, 1.22);
tl.to("#s1-ll",  {{width:300, duration:0.55, ease:"expo.out"}}, 1.42);
tl.to("#s1-dot", {{opacity:1, duration:0.2, ease:"back.out(2)"}}, 1.86);
tl.to("#s1-rl",  {{width:300, duration:0.55, ease:"expo.out"}}, 1.9);

// S2 panel + chart
tl.to("#s2-panel", {{clipPath:"inset(0 0% 0 0)", duration:0.6, ease:"expo.out"}}, 7.2);
tl.from("#s2-hp",   {{y:18, opacity:0, duration:0.5, ease:"expo.out"}}, 7.3);
tl.from("#s2-hc",   {{x:16, opacity:0, duration:0.4, ease:"expo.out"}}, 7.5);
tl.from("#s2-htag", {{opacity:0, duration:0.4}}, 7.2);
tl.from("#sp1", {{x:28, opacity:0, duration:0.45, ease:"expo.out"}}, 7.55);
tl.from("#sp2", {{x:28, opacity:0, duration:0.45, ease:"expo.out"}}, 7.78);
tl.from("#sp3", {{x:28, opacity:0, duration:0.45, ease:"expo.out"}}, 8.01);
tl.from("#s2-bdg", {{x:28, opacity:0, duration:0.4, ease:"power2.out"}}, 8.28);
tl.to("#s2-bdt", {{scale:1.9, opacity:0.35, duration:0.55, ease:"power2.out", yoyo:true, repeat:{pc}}}, 8.6);
tl.to(".candle", {{opacity:1, stagger:0.055, duration:0.22, ease:"power2.out"}}, 8.0);
tl.to("#s2-area", {{opacity:1, duration:2.5, ease:"power2.out"}}, 9.5);
const maEl = document.getElementById("s2-ma");
if (maEl && maEl.getTotalLength) {{
  const ml = maEl.getTotalLength();
  gsap.set(maEl, {{strokeDasharray:ml, strokeDashoffset:ml}});
  tl.to(maEl, {{strokeDashoffset:0, duration:3.8, ease:"power2.inOut"}}, 8.4);
}}
const tkEl = document.getElementById("s2-ti");
if (tkEl) {{ const tw = tkEl.scrollWidth/2; tl.to(tkEl, {{x:-tw, duration:22, ease:"none"}}, 7); }}

// S3
tl.to("#s3-scan", {{opacity:1, y:{CH}, duration:0.55, ease:"power2.in"}}, 24.1);
tl.set("#s3-scan", {{opacity:0}}, 24.65);
tl.to("#s3-top", {{opacity:1, duration:0.3}}, 24.2);
tl.to("#s3-bot", {{opacity:1, duration:0.3}}, 24.3);
tl.fromTo("#c1", {{y:40, opacity:0}}, {{y:0, opacity:1, duration:0.5, ease:"expo.out"}}, 24.4);
tl.fromTo("#c2", {{y:40, opacity:0}}, {{y:0, opacity:1, duration:0.5, ease:"expo.out"}}, 24.62);
tl.fromTo("#c3", {{y:40, opacity:0}}, {{y:0, opacity:1, duration:0.5, ease:"expo.out"}}, 24.84);

// S4
tl.from("#s4-eye",   {{opacity:0, duration:0.4}}, 33.3);
tl.from("#s4-txt",   {{y:28, opacity:0, duration:0.6, ease:"power3.out"}}, 33.5);
tl.to("#s4-rule",    {{width:480, duration:0.6, ease:"expo.out"}}, 34.3);
tl.from("#s4-brand", {{opacity:0, duration:0.4}}, 34.8);
tl.to("#s4-ov",      {{opacity:1, duration:1.3, ease:"power2.in"}}, 36.5);
// Pad timeline to full 38s duration so renderer captures all frames
tl.to({{}}, {{duration:0.1}}, 37.9);

window.__timelines["root"] = tl;
</script>
</body>
</html>"""


def build_project(event, words=None, project_root=None, installed_blocks_dir=None):
    if project_root is None:
        project_root = Path(__file__).parent.parent / "renders"
    project_root.mkdir(parents=True, exist_ok=True)

    name = _name(event)
    proj = project_root / name
    proj.mkdir(parents=True, exist_ok=True)

    print(f"  [Project] Building: {proj.name}")

    # meta.json
    (proj / "meta.json").write_text(
        json.dumps({"duration":38,"fps":30,"width":CW,"height":CH}, indent=2)
    )

    # Single index.html — all scenes inline
    html = build_html(event, words or [])
    (proj / "index.html").write_text(html, encoding="utf-8")
    print(f"  [Project]   wrote index.html ({len(html):,} chars)")
    print(f"  [Project] ✓ {proj}")
    return proj
