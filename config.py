"""
CryptoViz config — reads from environment variables.
Set these in Railway dashboard under Variables.
"""
import os

# Claude / TokenRouter
CLAUDE_API_KEY  = os.environ.get("CLAUDE_API_KEY", "")
CLAUDE_BASE_URL = os.environ.get("CLAUDE_BASE_URL", "https://api.tokenrouter.com/v1")
CLAUDE_MODEL    = os.environ.get("CLAUDE_MODEL",    "anthropic/claude-opus-4.7")

# Telegram
TELEGRAM_BOT_TOKEN       = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_DEFAULT_CHAT_ID = os.environ.get("TELEGRAM_DEFAULT_CHAT_ID", "")

# Binance (public — no key needed)
BINANCE_WS_URL  = "wss://stream.binance.com:9443/stream"
WATCHED_SYMBOLS = ["ethusdt", "btcusdt", "solusdt"]

# Thresholds
VOLUME_SPIKE_MULTIPLIER = float(os.environ.get("VOLUME_SPIKE_MULTIPLIER", "3.0"))
PRICE_CHANGE_THRESHOLD  = float(os.environ.get("PRICE_CHANGE_THRESHOLD",  "2.0"))

# Paths
COMPOSITIONS_DIR = "compositions"
RENDERS_DIR      = "renders"
TTS_VOICE        = "af_nova"

# PostHog (optional)
POSTHOG_API_KEY = os.environ.get("POSTHOG_API_KEY", "")
POSTHOG_HOST    = "https://app.posthog.com"
