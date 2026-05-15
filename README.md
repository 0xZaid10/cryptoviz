# CryptoViz

### Crypto markets just got a lot more interesting.

CryptoViz watches the market 24/7 and sends you a narrated, animated video the moment something significant happens — a volume spike, a price surge, unusual activity. Not a ping. Not a number. A proper video, with charts that move, a voice that explains what's happening, and data that actually makes sense at a glance.

Built at the **HeyGen × ElevenLabs × Fal × PostHog Hackathon, May 2026**.

---

## The Problem

Crypto never sleeps. But you have to.

Right now, staying on top of the market means:

- Switching between 5+ tabs (TradingView, CoinGecko, Etherscan, Twitter, your exchange)
- Reading raw numbers and forming your own narrative from disconnected data
- Setting up text or push notifications that tell you *something happened* — but not *what it means*
- Missing moves while you're asleep, in a meeting, or living your life

And when you *do* spot something worth sharing — a pattern, a whale move, a breakout — the best you can do is screenshot a chart and post it. Static. Low signal. Hard to understand for anyone who wasn't already watching.

**The data exists. The problem is it never becomes a story.**

### Why Not Just Use AI Video Generation?

The obvious answer is to use an AI video generation model — send a prompt, get a video back. But this breaks down immediately in a trading context:

- **Cost** — generative video models charge per second of output. At $0.10–0.50 per video, firing on every meaningful market event across ETH, BTC, and SOL adds up to hundreds of dollars a day per user before you've built anything useful
- **Latency** — cloud video generation takes 5–20 minutes. By the time the video arrives, the move is over and the insight is stale
- **Accuracy** — generative models hallucinate. You cannot have an AI invent price data or make up chart shapes when real money is involved. Every number in a CryptoViz video comes from live Binance data, precomputed in Python, rendered exactly as it is
- **Determinism** — the same market event should produce the same video, every time. Generative models are non-deterministic by nature

CryptoViz solves all of this with a different approach: use AI to write the *composition code*, not to generate the *pixels*.

---

## How HeyGen Makes This Possible

**HeyGen Hyperframes** is the core technology that makes CryptoViz viable.

Hyperframes is HeyGen's HTML-to-video rendering engine. Instead of generating video from a text prompt, you write an HTML file — with CSS for layout, SVG for charts, and GSAP animations for motion — and Hyperframes captures every frame using headless Chrome, then encodes it to MP4 with FFmpeg.

This gives CryptoViz something no generative model can offer: **mathematically accurate, pixel-perfect, data-driven video at near-zero marginal cost**.

Here's the exact pipeline:

1. **Market event detected** — Binance WebSocket fires when volume spikes 3x or price moves 2%+
2. **Claude writes the narration** — one AI call analyzes the event and writes a 30-second spoken script
3. **Python builds the composition** — all chart coordinates (candlestick positions, SVG polyline points, volume bar heights) are computed precisely from real market data, then injected into a Hyperframes HTML file
4. **Hyperframes renders it** — `npx hyperframes render` captures every frame. No cloud. No API. No per-video cost
5. **Kokoro speaks it** — HeyGen's built-in local TTS reads the narration with natural sentence pauses, completely offline
6. **Whisper transcribes it** — HeyGen's built-in local Whisper generates word timestamps
7. **FFmpeg composites** — audio and video combined in seconds
8. **Telegram delivers** — the final MP4 lands in your phone within ~2 minutes of the trigger firing

The AI's role is authoring, not generating. Claude writes code that Hyperframes executes. The video is rendered, not imagined — every data point is real, every coordinate is computed, every frame is deterministic.

**Cost per video: effectively zero.** The only billable API call is the Claude script (a few hundred tokens). Everything else — rendering, TTS, transcription — runs locally on a standard machine.

---

## The Solution

CryptoViz turns live market events into **narrated animated video alerts**, delivered to your phone the moment they happen.

When ETH spikes 4x normal volume at 3am, you don't get a notification saying "ETH volume spike". You get a 35-second video in Telegram:

- An animated candlestick chart drawing itself in real time
- The price move highlighted as it happened
- Volume bars showing the spike visually
- A calm, analytical voice explaining what happened, why it matters, and what to watch next

You press play, you understand the situation in 35 seconds, you make a decision. No tab-switching. No interpretation required.

When you want a full market check-in, send `/briefing ETH` in Telegram. CryptoViz fetches real live data from Binance, generates a complete market briefing video, and sends it within ~2 minutes. Any time, any symbol.

---

## Features

### Automatic Market Alerts
- **Volume spikes** — fires when current volume exceeds 3x the rolling baseline
- **Price surges / drops** — fires on 2%+ moves in a short window
- **Price level alerts** — set a specific price (e.g. ETH at $3,500), get notified when it crosses

### Every Alert is a Video
- Animated candlestick chart with real OHLCV data
- Moving average overlay drawing itself
- Volume bars per candle
- Right panel: current price, % change, volume multiplier, signal badge
- Scrolling ticker tape
- Context breakdown: session high, volume spike magnitude, market signal
- Narration: AI-written script, naturally spoken with pauses between sentences
- Fade to black outro

### On-Demand Briefings
Send `/briefing BTC` (or ETH or SOL) in Telegram at any time. CryptoViz fetches real live data from Binance, generates a full market briefing video, and sends it within ~2 minutes.

### Multi-User Telegram Bot
Multiple people can subscribe to the same CryptoViz instance. Each subscriber receives every alert video. Full command set:
- `/start` — subscribe
- `/stop` — unsubscribe
- `/status` — live prices + system status
- `/briefing [BTC|ETH|SOL]` — on-demand video briefing
- `/watch ETHUSDT 3500` — set a price level alert
- `/unwatch ETHUSDT 3500` — remove it
- `/help` — all commands

### Fully Local Pipeline
No ElevenLabs credits. No HeyGen video API credits. No external TTS service.
- **TTS**: Kokoro-82M, runs on your machine, 54 voices, completely free
- **Transcription**: Whisper base model, runs locally, no API key
- **Video render**: Hyperframes CLI, runs locally, no cloud
- **Audio composite**: FFmpeg, free and local

The only external calls are: Binance WebSocket (free, no key), Claude API (script generation), Telegram Bot API (delivery).

---

## Technical Architecture

```
Binance WebSocket (ETH/BTC/SOL live feed)
          │
          ▼
    TriggerDetector
    ├── Volume spike detection (rolling baseline, 3x threshold)
    ├── Price surge/drop detection (2% in 20 ticks)
    └── Price level crossing detection (user-defined)
          │
          ▼
     AlertPipeline
          │
    ┌─────┴──────────────────────────────────────────────┐
    │                                                     │
    │  1. Send immediate text alert to Telegram           │
    │  2. Claude writes narration script                  │
    │     (numbers formatted as spoken words for TTS)     │
    │  3. Claude normalizes script (single pass cleanup)  │
    │  4. Kokoro TTS → WAV (local, sentence pauses)       │
    │  5. Whisper transcribe → word timestamps            │
    │  6. Python builds Hyperframes HTML composition      │
    │     ├── SVG candlestick chart (precomputed coords)  │
    │     ├── Moving average polyline                     │
    │     ├── Volume bars                                 │
    │     ├── GSAP animations (deterministic, finite)     │
    │     ├── HUD overlays (LED grid, gradient mesh)      │
    │     └── 4 scenes: flash → title → chart → context  │
    │  7. npx hyperframes render → silent MP4             │
    │  8. ffmpeg composite → final MP4                    │
    │  9. Telegram send to all subscribers                │
    └─────────────────────────────────────────────────────┘
```

### Project Structure

```
cryptovizv2/
├── main.py                          # Entry point — starts all services
├── pipeline.py                      # AlertPipeline orchestrator
├── config.py                        # API keys, thresholds, watched symbols
├── test_trigger.py                  # Fire a test alert without market data
│
├── feeds/
│   └── binance.py                   # Binance WebSocket feed (no API key needed)
│
├── detection/
│   └── triggers.py                  # TriggerDetector — volume, price, levels
│
├── composer/
│   ├── generator.py                 # Claude writes scripts + calls project builder
│   ├── project_builder.py           # Builds full Hyperframes HTML composition
│   ├── renderer.py                  # npx hyperframes render + ffmpeg composite
│   └── transcriber.py              # Whisper word-level transcription
│
├── audio/
│   └── narrator.py                  # Kokoro TTS with sentence pauses + normalization
│
├── delivery/
│   └── telegram.py                  # TelegramDelivery + TelegramBot (multi-user)
│
├── analytics/
│   └── posthog.py                   # PostHog event tracking (optional)
│
├── compositions/                    # Installed Hyperframes catalog blocks
│   ├── glitch.html
│   ├── chromatic-radial-split.html
│   └── ...
│
└── renders/                         # Generated video projects
    └── alert_ETH_volume-spike_TIMESTAMP/
        ├── index.html               # Complete Hyperframes composition
        ├── meta.json                # Duration, fps, resolution
        ├── render.mp4               # Silent rendered video
        └── final.mp4                # Final video with audio
```

### The Hyperframes Composition

Every alert generates a self-contained Hyperframes project. The `index.html` is a single HTML file containing:

- CSS custom properties carrying the full design system (no hardcoded colors)
- Four scene divs, each with `data-start` and `data-duration` attributes
- A single root GSAP timeline registering all animations at absolute timestamps
- Precomputed SVG coordinates for charts (Python does the math, HTML just renders)
- `window.__timelines["root"]` — the Hyperframes standard for timeline registration

**Scene breakdown:**

| Scene | Time | Content |
|-------|------|---------|
| S0 — Alert Flash | 0–0.5s | Full-screen trend color + scan line sweep |
| S1 — Title Card | 0.5–7s | Asset name, event type, price, HUD labels, particle field, gradient mesh blobs |
| S2 — Chart | 7–24s | Candlestick chart, MA line, area fill, data panel, signal badge, ticker tape |
| S3 — Context | 24–33s | HUD terminal layout, 3 stat columns with scan line entrance animation |
| S4 — Summary | 33–38s | Bold statement, rule animation, brand line, fade to black |

### Design System

Swiss Pulse visual style — precision-first, data-forward, dark:

```css
--bg:      #050505   /* near-black background */
--text:    #f0f0f0   /* primary text */
--text-2:  #a0a0a0   /* secondary */
--label:   #666666   /* uppercase small labels */
--blue:    #0066FF   /* accent */
--tc:      #00FF88   /* trend color (green bullish / red bearish) */
```

All colors flow from CSS custom properties. The trend color (`--tc`) flips between `#00FF88` and `#FF3344` based on price direction and is injected once at build time — nothing is hardcoded in scene HTML.

### Why Not Use HeyGen's Video API?

HeyGen's Video Agent and avatar pipeline are powerful but designed for presenter-style videos. CryptoViz needs:
- Frame-accurate data visualization (charts, SVG paths, animated numbers)
- Deterministic output (same data → same video, every time)
- Real-time generation in under 3 minutes
- Zero per-video cloud cost at scale

Hyperframes solves all of these. It's HeyGen's local HTML-to-video renderer — think of it as a headless browser that captures every frame. We get the HeyGen ecosystem (catalog blocks, design system, CLI tooling) without the latency or cost of cloud video rendering.

---

## Setup

### Prerequisites

```bash
node --version    # v22+ required
python --version  # 3.12+ required
ffmpeg -version   # any recent version
```

### Installation

```bash
# 1. Clone / extract project
cd cryptovizv2

# 2. Python environment
python3 -m venv venv
source venv/bin/activate
pip install openai websockets aiohttp numpy python-telegram-bot \
            posthog kokoro-onnx soundfile

# 3. Node 22
nvm install 22 && nvm use 22

# 4. Hyperframes
npx hyperframes --version

# 5. Install catalog blocks (shader transitions, components)
npx hyperframes add glitch
npx hyperframes add chromatic-radial-split
npx hyperframes add cinematic-zoom
npx hyperframes add grain-overlay
npx hyperframes add vignette
```

### Configuration

Edit `config.py`:

```python
# Claude (via TokenRouter or Anthropic directly)
CLAUDE_API_KEY  = "your-key"
CLAUDE_BASE_URL = "https://api.tokenrouter.com/v1"
CLAUDE_MODEL    = "anthropic/claude-opus-4.7"

# Telegram Bot (get from @BotFather)
TELEGRAM_BOT_TOKEN       = "your-bot-token"
TELEGRAM_DEFAULT_CHAT_ID = "your-chat-id"

# Market data — Binance public WebSocket (no key needed)
WATCHED_SYMBOLS = ["ethusdt", "btcusdt", "solusdt"]

# Trigger thresholds
VOLUME_SPIKE_MULTIPLIER = 3.0   # fire on 3x+ volume
PRICE_CHANGE_THRESHOLD  = 2.0   # fire on 2%+ move
```

### Running

```bash
# Start the full system
python main.py

# Test without waiting for a real market event
python test_trigger.py
```

### Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Subscribe to alerts |
| `/stop` | Unsubscribe |
| `/status` | Live prices + system status |
| `/briefing BTC` | Generate on-demand BTC video |
| `/briefing ETH` | Generate on-demand ETH video |
| `/briefing SOL` | Generate on-demand SOL video |
| `/watch ETHUSDT 3500` | Alert when ETH crosses $3,500 |
| `/unwatch ETHUSDT 3500` | Remove that alert |
| `/help` | All commands |

---

## Hackathon Context

**Event:** HeyGen × ElevenLabs × Fal × PostHog Multi-modal AI Business Hackathon
**Date:** May 14–15, 2026
**Tracks:** Product Track + Agent Track

### Product Track

CryptoViz is a real product with a real business model:

- **B2C SaaS** — individual traders pay a monthly subscription for personalized video alerts on their watchlist
- **B2B API** — DeFi protocols and on-chain analytics platforms embed CryptoViz to send video alerts to their users
- **White-label** — crypto exchanges offer CryptoViz alerts as a premium feature

The infrastructure already scales: the Telegram bot is multi-user, the pipeline is async, and adding more symbols or users requires no architectural changes.

### Agent Track

CryptoViz demonstrates a two-layer AI pipeline:

1. **Claude as market analyst** — reads raw tick data and writes a narration script that contextualizes the event for a trader
2. **Claude as Hyperframes author** — given the Hyperframes framework rules and precomputed chart data, Claude writes the narration that drives the video composition

The pipeline is genuinely agentic: trigger detection → context analysis → script writing → number normalization → composition building → lint validation → render → delivery. Each stage is autonomous, with Claude making real interpretive decisions about what matters in the market data and how to communicate it.

---

## Built With

| Component | Technology |
|-----------|-----------|
| Market data | Binance public WebSocket |
| AI brain | Claude Opus 4.7 via TokenRouter |
| Video rendering | HeyGen Hyperframes CLI |
| Text-to-speech | Kokoro-82M (local, Hyperframes built-in) |
| Transcription | Whisper base (local, Hyperframes built-in) |
| Audio composite | FFmpeg |
| Delivery | Telegram Bot API |
| Analytics | PostHog |
| Runtime | Python 3.12 + asyncio |

---

*CryptoViz — because the market deserves better than a push notification.*
