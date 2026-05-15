# cryptoviz/detection/triggers.py

from dataclasses import dataclass, field
from typing import List, Callable, Optional, Dict
import numpy as np
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
PARENT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PARENT))
try:
    import cryptoviz_v3.config as config
except ModuleNotFoundError:
    try:    import config
    except: sys.path.insert(0, str(PARENT.parent)); import config


@dataclass
class MarketEvent:
    type: str
    asset: str
    symbol: str
    current_price: float
    change_pct: float
    trigger_level: float
    volume_multiplier: float
    price_history: List[float]
    volume_history: List[float]
    summary: str

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "asset": self.asset,
            "symbol": self.symbol,
            "current_price": round(self.current_price, 2),
            "change_pct": round(self.change_pct, 2),
            "trigger_level": round(self.trigger_level, 2),
            "volume_multiplier": round(self.volume_multiplier, 1),
            "price_history": [round(p, 2) for p in self.price_history],
            "volume_history": [round(v, 4) for v in self.volume_history],
            "summary": self.summary,
        }


class TriggerDetector:
    """
    Monitors market ticks and fires events on significant moves.
    Hardened:
    - Per-symbol cooldown (ticks-based)
    - Minimum buffer before computing baseline
    - Deduplication: won't fire same type twice in cooldown window
    - Price level alerts: user-defined levels
    """

    BUFFER_SIZE   = 150    # ticks kept per symbol
    CHART_POINTS  = 50     # points sent in event
    BASELINE_MIN  = 50     # minimum ticks before computing baseline
    COOLDOWN_TICKS = 300   # ticks between alerts per symbol

    def __init__(self):
        self.handlers: List[Callable]         = []
        self.price_buf: Dict[str, List[float]] = {}
        self.vol_buf:   Dict[str, List[float]] = {}
        self.baseline:  Dict[str, float]       = {}
        self.cooldown:  Dict[str, int]         = {}
        self.price_levels: Dict[str, List[float]] = {}  # user-set price alerts

    def on_trigger(self, handler: Callable):
        self.handlers.append(handler)

    def set_price_level(self, symbol: str, price: float):
        """Register a user-defined price level alert."""
        sym = symbol.upper()
        self.price_levels.setdefault(sym, [])
        if price not in self.price_levels[sym]:
            self.price_levels[sym].append(price)
            print(f"[TriggerDetector] Price level set: {sym} @ ${price:,.2f}")

    def remove_price_level(self, symbol: str, price: float):
        sym = symbol.upper()
        if sym in self.price_levels:
            self.price_levels[sym] = [p for p in self.price_levels[sym] if p != price]

    async def ingest(self, tick: dict):
        symbol = tick.get("symbol", "").upper()
        price  = float(tick.get("price", 0))
        volume = float(tick.get("volume", 0))

        if not symbol or price <= 0:
            return

        # Update buffers
        self.price_buf.setdefault(symbol, [])
        self.vol_buf.setdefault(symbol, [])
        self.cooldown.setdefault(symbol, self.COOLDOWN_TICKS)

        self.price_buf[symbol].append(price)
        self.price_buf[symbol] = self.price_buf[symbol][-self.BUFFER_SIZE:]

        self.vol_buf[symbol].append(volume)
        self.vol_buf[symbol] = self.vol_buf[symbol][-self.BUFFER_SIZE:]

        # Increment cooldown
        self.cooldown[symbol] = min(self.cooldown[symbol] + 1, self.COOLDOWN_TICKS + 1)

        # Need minimum buffer
        if len(self.vol_buf[symbol]) < self.BASELINE_MIN:
            return

        # Update baseline (avg of older half of buffer)
        older = self.vol_buf[symbol][:self.BASELINE_MIN // 2]
        self.baseline[symbol] = float(np.mean(older)) if older else 0

        # Skip if in cooldown
        if self.cooldown[symbol] < self.COOLDOWN_TICKS:
            return

        # Check triggers in priority order
        event = (
            self._check_volume_spike(symbol, price, volume) or
            self._check_price_surge(symbol, price) or
            self._check_price_levels(symbol, price)
        )

        if event:
            self.cooldown[symbol] = 0
            for handler in self.handlers:
                await handler(event)

    def _check_volume_spike(self, symbol, price, volume) -> Optional[MarketEvent]:
        baseline = self.baseline.get(symbol, 0)
        if baseline <= 0:
            return None

        mult = volume / baseline
        if mult < config.VOLUME_SPIKE_MULTIPLIER:
            return None

        prices  = self.price_buf[symbol]
        chg_pct = ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] > 0 else 0
        asset   = symbol.replace("USDT", "")

        return MarketEvent(
            type="volume_spike",
            asset=asset, symbol=symbol,
            current_price=price,
            change_pct=round(chg_pct, 2),
            trigger_level=price,
            volume_multiplier=round(mult, 1),
            price_history=prices[-self.CHART_POINTS:],
            volume_history=self.vol_buf[symbol][-self.CHART_POINTS:],
            summary=f"{asset} volume spike: {mult:.1f}x normal at ${price:,.2f}"
        )

    def _check_price_surge(self, symbol, price) -> Optional[MarketEvent]:
        prices = self.price_buf[symbol]
        if len(prices) < 20:
            return None

        ref = prices[-20]
        if ref <= 0:
            return None

        chg_pct = ((price - ref) / ref) * 100
        if abs(chg_pct) < config.PRICE_CHANGE_THRESHOLD:
            return None

        asset     = symbol.replace("USDT", "")
        direction = "surge" if chg_pct > 0 else "drop"
        baseline  = self.baseline.get(symbol, 1) or 1
        cur_vol   = self.vol_buf[symbol][-1] if self.vol_buf[symbol] else 0
        vol_mult  = cur_vol / baseline

        return MarketEvent(
            type=f"price_{direction}",
            asset=asset, symbol=symbol,
            current_price=price,
            change_pct=round(chg_pct, 2),
            trigger_level=ref,
            volume_multiplier=round(vol_mult, 1),
            price_history=prices[-self.CHART_POINTS:],
            volume_history=self.vol_buf[symbol][-self.CHART_POINTS:],
            summary=f"{asset} price {direction}: {abs(chg_pct):.1f}% in 20 ticks"
        )

    def _check_price_levels(self, symbol, price) -> Optional[MarketEvent]:
        levels = self.price_levels.get(symbol, [])
        if not levels:
            return None

        prices = self.price_buf[symbol]
        if len(prices) < 2:
            return None

        prev_price = prices[-2]

        for level in levels:
            # Crossed from below
            crossed = (prev_price < level <= price) or (prev_price > level >= price)
            if not crossed:
                continue

            direction = "above" if price >= level else "below"
            asset = symbol.replace("USDT", "")
            chg   = ((price - level) / level) * 100
            baseline = self.baseline.get(symbol, 1) or 1
            cur_vol  = self.vol_buf[symbol][-1] if self.vol_buf[symbol] else 0

            return MarketEvent(
                type="price_level",
                asset=asset, symbol=symbol,
                current_price=price,
                change_pct=round(chg, 2),
                trigger_level=level,
                volume_multiplier=round(cur_vol / baseline, 1),
                price_history=prices[-self.CHART_POINTS:],
                volume_history=self.vol_buf[symbol][-self.CHART_POINTS:],
                summary=f"{asset} crossed ${level:,.2f} — now {direction} at ${price:,.2f}"
            )

        return None
