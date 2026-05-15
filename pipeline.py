"""
AlertPipeline — market event → video → Telegram
Full flow:
  1. Send immediate text alert
  2. Write narration script (Claude)
  3. Normalize numbers for TTS (Claude)
  4. Generate audio (Kokoro local TTS)
  5. Transcribe for captions (Whisper local)
  6. Build project folder + render (Hyperframes)
  7. Composite audio + video (ffmpeg)
  8. Send video to all Telegram subscribers
"""

import asyncio
import time
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

from composer.generator  import CompositionGenerator
from composer.renderer   import HyperframesRenderer
from composer.transcriber import Transcriber
from audio.narrator      import Narrator
from delivery.telegram   import TelegramDelivery
from analytics.posthog   import Analytics
from detection.triggers  import MarketEvent


class AlertPipeline:
    def __init__(self):
        self.gen         = CompositionGenerator()
        self.renderer    = HyperframesRenderer()
        self.narrator    = Narrator()
        self.transcriber = Transcriber()
        self.delivery    = TelegramDelivery()
        self.analytics   = Analytics()
        self._busy       = False

    async def process(self, event: MarketEvent):
        """Full pipeline: event → video → Telegram."""
        if self._busy:
            print(f"[Pipeline] Busy — skipping: {event.summary}")
            return

        self._busy = True
        t0 = time.time()

        print(f"\n{'='*60}")
        print(f"[Pipeline] 🚨 {event.summary}")
        print(f"{'='*60}")

        try:
            ed = event.to_dict()

            # 1. Immediate text alert
            await self.delivery.send_alert_text(ed)
            self.analytics.track_alert_generated(event.type, event.asset)

            # 2. Script
            print("[Pipeline] 1/6 Writing script...")
            script = self.gen.write_script(ed)

            # 3. Normalize + TTS
            print("[Pipeline] 2/6 Generating audio...")
            audio_wav, normalized = await asyncio.get_event_loop().run_in_executor(
                None, self.narrator.speak, script
            )

            # 4. Transcribe
            print("[Pipeline] 3/6 Transcribing...")
            words = await asyncio.get_event_loop().run_in_executor(
                None, self.transcriber.transcribe, audio_wav
            )
            print(f"           {len(words)} word timestamps")

            # 5. Build project + render
            print("[Pipeline] 4/6 Building & rendering...")
            project_dir = self.gen.build_project(ed, words=words)
            silent_mp4  = await asyncio.get_event_loop().run_in_executor(
                None, self.renderer.render, project_dir
            )

            # 6. Composite
            print("[Pipeline] 5/6 Compositing audio...")
            final_mp4 = await asyncio.get_event_loop().run_in_executor(
                None, self.renderer.composite, silent_mp4, audio_wav
            )

            # 7. Deliver
            elapsed = time.time() - t0
            caption = (
                f"⚡ <b>{event.asset} {event.type.replace('_',' ').upper()}</b>\n"
                f"${event.current_price:,.2f} · "
                f"{'+' if event.change_pct >= 0 else ''}{event.change_pct:.1f}% · "
                f"{event.volume_multiplier:.1f}x vol\n"
                f"<i>Generated in {elapsed:.0f}s</i>"
            )
            print(f"[Pipeline] 6/6 Sending ({elapsed:.0f}s total)...")
            await self.delivery.send_video(final_mp4, caption=caption)
            self.analytics.track_video_sent(event.asset, elapsed)
            print(f"[Pipeline] ✅ Done in {elapsed:.1f}s")

            # Cleanup temp audio
            self.narrator.cleanup(audio_wav)
            self.transcriber.cleanup(audio_wav)

        except Exception as e:
            print(f"[Pipeline] ❌ Error: {e}")
            import traceback; traceback.print_exc()
            self.analytics.track_pipeline_error("pipeline", str(e))
            try:
                await self.delivery.send_text(
                    f"⚠️ Alert for {event.asset}: {event.summary}\n"
                    f"<i>(Video generation failed — check logs)</i>"
                )
            except Exception:
                pass
        finally:
            self._busy = False
