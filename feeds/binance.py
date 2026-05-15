# cryptoviz/feeds/binance.py

import asyncio
import json
import websockets
from typing import Callable, List
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
PARENT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PARENT))
try:
    import cryptoviz.config as config
except ModuleNotFoundError:
    import config


class BinanceFeed:
    """
    Streams real-time price and volume data from Binance public WebSocket.
    No API key required for public market data streams.
    """

    def __init__(self, symbols: List[str] = None):
        self.symbols = [s.lower() for s in (symbols or config.WATCHED_SYMBOLS)]
        self.running = False

    def _build_url(self) -> str:
        """Build combined stream URL for all symbols."""
        streams = [f"{s}@ticker" for s in self.symbols]
        stream_str = "/".join(streams)
        return f"{config.BINANCE_WS_URL}?streams={stream_str}"

    async def stream(self, callback: Callable):
        """
        Connect to Binance WebSocket and stream ticks to callback.
        callback receives: { symbol, price, volume }
        Reconnects automatically on disconnect.
        """
        self.running = True
        url = self._build_url()
        print(f"[BinanceFeed] Connecting to: {url}")

        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    print(f"[BinanceFeed] Connected. Streaming: {self.symbols}")
                    async for raw_msg in ws:
                        try:
                            msg = json.loads(raw_msg)
                            data = msg.get("data", msg)

                            # Binance ticker format
                            symbol = data.get("s", "")       # e.g. "ETHUSDT"
                            price = float(data.get("c", 0))  # close/current price
                            volume = float(data.get("v", 0)) # 24h volume in base asset
                            quote_vol = float(data.get("q", 0))  # 24h volume in quote

                            if symbol and price > 0:
                                tick = {
                                    "symbol": symbol,
                                    "price": price,
                                    "volume": quote_vol or volume,  # prefer quote volume
                                    "change_pct": float(data.get("P", 0)),
                                    "high": float(data.get("h", price)),
                                    "low": float(data.get("l", price)),
                                }
                                await callback(tick)

                        except (json.JSONDecodeError, ValueError, KeyError):
                            continue

            except websockets.ConnectionClosed:
                if self.running:
                    print("[BinanceFeed] Connection closed. Reconnecting in 5s...")
                    await asyncio.sleep(5)
            except Exception as e:
                if self.running:
                    print(f"[BinanceFeed] Error: {e}. Reconnecting in 10s...")
                    await asyncio.sleep(10)

    def stop(self):
        self.running = False
