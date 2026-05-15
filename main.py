"""
CryptoViz — main entry point
"""
import asyncio
import aiohttp
import sys
from pathlib import Path

ROOT   = Path(__file__).parent
PARENT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PARENT))

try:    import cryptoviz_v3.config as config
except:
    try:    import config
    except: sys.path.insert(0, str(PARENT.parent)); import config

from feeds.binance      import BinanceFeed
from detection.triggers import TriggerDetector, MarketEvent
from pipeline           import AlertPipeline
from delivery.telegram  import TelegramBot


async def fetch_live_snapshot(symbol: str = "BTCUSDT") -> MarketEvent:
    """Fetch real Binance data and return a MarketEvent for briefing."""
    asset = symbol.replace("USDT", "")
    print(f"  [Briefing] Fetching live data for {symbol}...")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        ) as r:
            ticker = await r.json()

        async with session.get(
            f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=50"
        ) as r:
            klines = await r.json()

    price      = float(ticker["lastPrice"])
    change_pct = float(ticker["priceChangePercent"])
    prices     = [float(k[4]) for k in klines]
    volumes    = [float(k[5]) for k in klines]

    # Skip current incomplete candle (last one) when computing baseline
    # Current candle has partial volume — comparing it to complete candles
    # makes vol_mult look tiny (e.g. 0.1x instead of realistic value)
    completed  = volumes[:-1]  # all complete candles
    avg_vol    = sum(completed) / max(len(completed), 1)
    # Use 24h quote volume from ticker for current "candle" approximation
    cur_vol_24h = float(ticker.get("quoteVolume", 0))
    cur_vol_1h  = cur_vol_24h / 24  # rough hourly equivalent
    vol_mult    = cur_vol_1h / avg_vol if avg_vol > 0 else 1.0

    print(f"  [Briefing] {asset}: ${price:,.2f} ({change_pct:+.2f}%) | vol {vol_mult:.1f}x")

    return MarketEvent(
        type="briefing",
        asset=asset, symbol=symbol,
        current_price=price,
        change_pct=round(change_pct, 2),
        trigger_level=round(price * 0.99, 2),
        volume_multiplier=round(vol_mult, 1),
        price_history=prices,
        volume_history=volumes,
        summary=f"{asset} market briefing — ${price:,.2f} ({change_pct:+.2f}%)"
    )


def _briefing_handler(pipeline: AlertPipeline):
    async def handler(symbol: str = "BTCUSDT", chat_id: str = None):
        try:
            event = await fetch_live_snapshot(symbol)
            await pipeline.process(event)
        except Exception as e:
            print(f"  [Briefing] Error: {e}")
            await pipeline.delivery.send_text(f"⚠️ Briefing failed: {e}")
    return handler


async def main():
    print("=" * 60)
    print("  CryptoViz — Crypto Market Alert Video Generator")
    print(f"  Watching: {config.WATCHED_SYMBOLS}")
    print(f"  Thresholds: {config.VOLUME_SPIKE_MULTIPLIER}x vol | {config.PRICE_CHANGE_THRESHOLD}% price")
    print("=" * 60)

    pipeline = AlertPipeline()
    detector = TriggerDetector()
    feed     = BinanceFeed(symbols=config.WATCHED_SYMBOLS)

    detector.on_trigger(pipeline.process)

    tick_count = {"n": 0}

    async def on_tick(tick: dict):
        tick_count["n"] += 1
        if tick_count["n"] == 1:
            print(f"[Main] ✓ Binance connected — {tick['symbol']} ${float(tick['price']):,.2f}")
        if tick_count["n"] % 500 == 0:
            print(f"[Main] {tick_count['n']} ticks | watching for triggers...")
        await detector.ingest(tick)

    # Pass detector to bot so /watch command works
    bot = TelegramBot(
        delivery=pipeline.delivery,
        pipeline_callback=_briefing_handler(pipeline),
        detector=detector
    )
    await bot.setup()

    print("\n[Main] All services started.")
    print("[Main] Send /start to your Telegram bot to subscribe.\n")

    try:
        await asyncio.gather(
            feed.stream(on_tick),
            bot.run_polling(),
        )
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Main] Shutting down...")