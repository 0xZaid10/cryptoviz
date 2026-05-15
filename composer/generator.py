"""
Generator — Claude writes script, project_builder handles everything else.
"""
import sys
from pathlib import Path
from openai import OpenAI

ROOT   = Path(__file__).parent.parent
PARENT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PARENT))
try:    import cryptoviz_v3.config as config
except:
    try:    import config
    except: sys.path.insert(0, str(PARENT.parent)); import config

from composer.project_builder import build_project


def _price_words(price: float) -> str:
    if price >= 1000:
        t = int(price // 1000); r = int(price % 1000)
        if r == 0:    return f"{t} thousand dollars"
        elif r < 100: return f"{t} thousand and {r} dollars"
        else:         return f"{t} thousand {r} dollars"
    return f"{price:.2f} dollars"


class CompositionGenerator:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.CLAUDE_API_KEY,
            base_url=config.CLAUDE_BASE_URL
        )

    def write_script(self, event: dict) -> str:
        chg = abs(event.get("change_pct", 0))
        vol = event.get("volume_multiplier", 0)
        direction = "up" if event.get("change_pct", 0) >= 0 else "down"
        price_spoken = _price_words(event["current_price"])

        resp = self.client.chat.completions.create(
            model=config.CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content":
                f"""Write a 28-35 second spoken narration for this crypto alert.
TTS reads digits literally — write ALL numbers as words:
- ${event['current_price']:,.2f} → "{price_spoken}"
- {chg}% → "{chg:.1f} percent"
- {vol:.1f}x → "{vol:.1f} times normal volume"
- Decimals: "4.2" → "four point two"
Style: calm authority, short sentences, end with one actionable insight.
Asset: {event['asset']} | Event: {event['type'].replace('_',' ')}
Price: {price_spoken} ({direction} {chg:.1f} percent) | Volume: {vol:.1f} times normal
Output ONLY the words to speak."""}]
        )
        return resp.choices[0].message.content.strip()

    def normalize_script(self, script: str) -> str:
        resp = self.client.chat.completions.create(
            model=config.CLAUDE_MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content":
                f"""Rewrite so ALL numbers/symbols are spoken aloud for TTS.
Rules: decimals→"four point two", prices→words, %→"percent", x→"times",
▲▼→"up"/"down", remove $, keep all punctuation, change nothing else.
Output ONLY the rewritten script.
Script: {script}"""}]
        )
        return resp.choices[0].message.content.strip()

    def build_project(self, event: dict, words: list = None) -> Path:
        """Build full Hyperframes project folder. Returns project dir."""
        return build_project(event=event, words=words or [])
