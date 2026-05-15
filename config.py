# cryptoviz/config.py

# TokenRouter / Claude
CLAUDE_API_KEY = "token_router_api_key"
CLAUDE_BASE_URL = "https://api.tokenrouter.com/v1"
CLAUDE_MODEL = "anthropic/claude-opus-4.7"

# Telegram
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_DEFAULT_CHAT_ID = ""  

# Binance WebSocket (no key needed for public streams)
BINANCE_WS_URL = "wss://stream.binance.com:9443/stream"
WATCHED_SYMBOLS = ["ethusdt", "btcusdt", "solusdt"]

# Trigger thresholds
VOLUME_SPIKE_MULTIPLIER = 1.5   # 3x normal volume triggers alert
PRICE_CHANGE_THRESHOLD = 2.0    # 2% price move in short window

# Watched wallets (add ETH addresses for wallet monitoring)
WATCHED_WALLETS = []

# Paths
COMPOSITIONS_DIR = "compositions"
RENDERS_DIR = "renders"
TTS_VOICE = "af_nova"

POSTHOG_API_KEY = ""
POSTHOG_HOST = "https://app.posthog.com"
HEYGEN_API_KEY = ""
