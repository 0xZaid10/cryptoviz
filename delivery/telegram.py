# cryptoviz/delivery/telegram.py

from telegram import Bot, InputFile
from telegram.error import TelegramError
from pathlib import Path
import sys
import json

ROOT   = Path(__file__).parent.parent.parent
PARENT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PARENT))
try:
    import cryptoviz_v3.config as config
except ModuleNotFoundError:
    try:    import config
    except: sys.path.insert(0, str(PARENT.parent)); import config


class TelegramDelivery:
    """Delivers alert videos via Telegram. Multi-user subscriber list."""

    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        self.subscribers: set = {str(config.TELEGRAM_DEFAULT_CHAT_ID)}

    def add_subscriber(self, chat_id: str):
        self.subscribers.add(str(chat_id))
        print(f"[Telegram] +subscriber {chat_id} (total: {len(self.subscribers)})")

    def remove_subscriber(self, chat_id: str):
        self.subscribers.discard(str(chat_id))
        print(f"[Telegram] -subscriber {chat_id} (total: {len(self.subscribers)})")

    async def send_video(self, video_path: Path, caption: str = ""):
        if not video_path.exists():
            print(f"[Telegram] Video not found: {video_path}")
            return

        size_mb = video_path.stat().st_size / 1024 / 1024
        print(f"[Telegram] Sending {size_mb:.1f}MB to {len(self.subscribers)} subscriber(s)...")

        for chat_id in list(self.subscribers):
            try:
                with open(video_path, "rb") as f:
                    await self.bot.send_video(
                        chat_id=chat_id,
                        video=f,
                        caption=caption,
                        parse_mode="HTML",
                        supports_streaming=True,
                        read_timeout=120,
                        write_timeout=120,
                        connect_timeout=30,
                    )
                print(f"[Telegram] ✓ Sent to {chat_id}")
            except TelegramError as e:
                print(f"[Telegram] Failed {chat_id}: {e}")
                # Retry once with longer timeout
                try:
                    with open(video_path, "rb") as f:
                        await self.bot.send_video(
                            chat_id=chat_id,
                            video=f,
                            caption=caption,
                            parse_mode="HTML",
                            supports_streaming=True,
                            read_timeout=300,
                            write_timeout=300,
                        )
                    print(f"[Telegram] ✓ Sent to {chat_id} (retry)")
                except TelegramError as e2:
                    print(f"[Telegram] Retry failed {chat_id}: {e2}")

    async def send_text(self, message: str, chat_id: str = None):
        targets = [str(chat_id)] if chat_id else list(self.subscribers)
        for cid in targets:
            try:
                await self.bot.send_message(
                    chat_id=cid, text=message, parse_mode="HTML"
                )
            except TelegramError as e:
                print(f"[Telegram] Text failed {cid}: {e}")

    async def send_alert_text(self, event_dict: dict):
        """Quick text alert sent immediately while video generates."""
        asset   = event_dict.get("asset", "")
        price   = event_dict.get("current_price", 0)
        change  = event_dict.get("change_pct", 0)
        vol     = event_dict.get("volume_multiplier", 0)
        etype   = event_dict.get("type", "").replace("_", " ").upper()
        icon    = "📈" if change >= 0 else "📉"
        sign    = "+" if change >= 0 else ""

        msg = (
            f"⚡ <b>CryptoViz Alert</b>\n\n"
            f"{icon} <b>{asset}</b> — {etype}\n"
            f"Price: <b>${price:,.2f}</b> ({sign}{change:.1f}%)\n"
            f"Volume: <b>{vol:.1f}x</b> normal\n\n"
            f"<i>Generating video analysis...</i>"
        )
        await self.send_text(msg)


class TelegramBot:
    """
    Handles incoming Telegram commands.
    Commands:
      /start              — subscribe
      /stop               — unsubscribe
      /status             — system status + live prices
      /briefing [symbol]  — generate on-demand video briefing
      /watch SYMBOL PRICE — set a price level alert
      /unwatch SYMBOL PRICE — remove a price level alert
      /help               — list commands
    """

    def __init__(self, delivery: TelegramDelivery,
                 pipeline_callback=None, detector=None):
        self.delivery          = delivery
        self.pipeline_callback = pipeline_callback
        self.detector          = detector   # for price level commands
        self.application       = None

    async def setup(self):
        from telegram.ext import Application, CommandHandler

        self.application = (
            Application.builder()
            .token(config.TELEGRAM_BOT_TOKEN)
            .build()
        )

        cmds = [
            ("start",    self._start),
            ("stop",     self._stop),
            ("status",   self._status),
            ("briefing", self._briefing),
            ("watch",    self._watch),
            ("unwatch",  self._unwatch),
            ("help",     self._help),
        ]
        for name, handler in cmds:
            self.application.add_handler(
                CommandHandler(name, handler)
            )

        await self.application.initialize()
        await self.application.start()
        print("[TelegramBot] Bot started. Listening for commands...")

    async def run_polling(self):
        if self.application:
            await self.application.updater.start_polling()

    async def _start(self, update, context):
        chat_id = str(update.effective_chat.id)
        self.delivery.add_subscriber(chat_id)
        await update.message.reply_text(
            "🚀 <b>CryptoViz activated!</b>\n\n"
            "You'll receive animated video alerts for:\n"
            "• Volume spikes (3x+ normal)\n"
            "• Price surges/drops (2%+ move)\n"
            "• Price levels you set\n\n"
            "<b>Commands:</b>\n"
            "/stop — unsubscribe\n"
            "/status — live prices + system status\n"
            "/briefing [BTC|ETH|SOL] — generate market briefing video\n"
            "/watch ETHUSDT 3500 — alert when ETH crosses $3,500\n"
            "/unwatch ETHUSDT 3500 — remove that alert\n"
            "/help — show all commands\n\n"
            "<i>Watching: ETH, BTC, SOL</i>",
            parse_mode="HTML"
        )

    async def _stop(self, update, context):
        self.delivery.remove_subscriber(str(update.effective_chat.id))
        await update.message.reply_text(
            "✅ Unsubscribed. Send /start anytime to reactivate."
        )

    async def _status(self, update, context):
        # Fetch live prices
        try:
            import aiohttp
            prices = {}
            async with aiohttp.ClientSession() as session:
                for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
                    async with session.get(
                        f"https://api.binance.com/api/v3/ticker/price?symbol={sym}"
                    ) as r:
                        d = await r.json()
                        prices[sym.replace("USDT","")] = float(d["price"])

            price_lines = "\n".join(
                f"  <b>{asset}</b>: ${price:,.2f}"
                for asset, price in prices.items()
            )
        except Exception:
            price_lines = "  <i>(could not fetch live prices)</i>"

        subs = len(self.delivery.subscribers)
        await update.message.reply_text(
            f"📊 <b>CryptoViz Status</b>\n\n"
            f"🟢 Active | {subs} subscriber(s)\n\n"
            f"<b>Live Prices:</b>\n{price_lines}\n\n"
            f"<b>Monitoring:</b> ETH, BTC, SOL\n"
            f"<b>Thresholds:</b> {config.VOLUME_SPIKE_MULTIPLIER}x vol | "
            f"{config.PRICE_CHANGE_THRESHOLD}% price",
            parse_mode="HTML"
        )

    async def _briefing(self, update, context):
        # Parse optional symbol argument: /briefing ETH
        symbol = "BTCUSDT"
        if context.args:
            arg = context.args[0].upper()
            if not arg.endswith("USDT"):
                arg += "USDT"
            if arg in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
                symbol = arg
            else:
                await update.message.reply_text(
                    "⚠️ Supported: /briefing BTC | /briefing ETH | /briefing SOL"
                )
                return

        asset = symbol.replace("USDT", "")
        await update.message.reply_text(
            f"🎬 Generating <b>{asset}</b> market briefing... (~2 min)",
            parse_mode="HTML"
        )
        if self.pipeline_callback:
            await self.pipeline_callback(symbol=symbol)

    async def _watch(self, update, context):
        """Set a price level alert: /watch ETHUSDT 3500"""
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /watch ETHUSDT 3500\n"
                "Fires when ETH crosses $3,500"
            )
            return

        symbol = context.args[0].upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        try:
            price = float(context.args[1].replace(",", ""))
        except ValueError:
            await update.message.reply_text("⚠️ Invalid price. Example: /watch ETHUSDT 3500")
            return

        if self.detector:
            self.detector.set_price_level(symbol, price)

        asset = symbol.replace("USDT", "")
        await update.message.reply_text(
            f"✅ <b>Price alert set</b>\n"
            f"{asset} @ <b>${price:,.2f}</b>\n"
            f"You'll be notified when price crosses this level.",
            parse_mode="HTML"
        )

    async def _unwatch(self, update, context):
        """Remove a price level: /unwatch ETHUSDT 3500"""
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Usage: /unwatch ETHUSDT 3500")
            return

        symbol = context.args[0].upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        try:
            price = float(context.args[1].replace(",", ""))
        except ValueError:
            await update.message.reply_text("⚠️ Invalid price.")
            return

        if self.detector:
            self.detector.remove_price_level(symbol, price)

        asset = symbol.replace("USDT", "")
        await update.message.reply_text(
            f"✅ Removed price alert: {asset} @ ${price:,.2f}"
        )

    async def _help(self, update, context):
        await update.message.reply_text(
            "<b>CryptoViz Commands</b>\n\n"
            "/start — subscribe to alerts\n"
            "/stop — unsubscribe\n"
            "/status — live prices + system info\n"
            "/briefing [BTC|ETH|SOL] — generate video briefing\n"
            "/watch SYMBOL PRICE — set price level alert\n"
            "/unwatch SYMBOL PRICE — remove price alert\n"
            "/help — this message\n\n"
            "<i>Alerts fire automatically on volume spikes and price moves.</i>",
            parse_mode="HTML"
        )