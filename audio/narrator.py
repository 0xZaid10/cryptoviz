# cryptoviz/audio/narrator.py

import subprocess
import uuid
import re
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent.parent
PARENT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PARENT))
try:
    import cryptoviz.config as config
except ModuleNotFoundError:
    import config

from openai import OpenAI


class Narrator:
    """
    Generates spoken narration using Hyperframes local TTS (Kokoro-82M).
    Makes one Claude call to normalize all numbers before sending to TTS.
    Splits on sentences and adds natural pauses between them.
    Returns both the audio path and the normalized script.
    """

    def __init__(self):
        self.voice = config.TTS_VOICE
        self.tmp_dir = Path("/tmp/cryptoviz_audio")
        self.tmp_dir.mkdir(exist_ok=True)
        self.client = OpenAI(
            api_key=config.CLAUDE_API_KEY,
            base_url=config.CLAUDE_BASE_URL
        )

    def speak(self, script: str) -> tuple:
        """
        Full pipeline: normalize → split → TTS → pause → combine.
        Returns (audio_path, normalized_script) tuple.
        """
        # Step 1: normalize all numbers with one Claude call
        normalized = self._normalize_for_tts(script)
        print(f"  [Narrator] Normalized: {normalized[:120]}...")

        # Step 2: split into sentences
        sentences = self._split_sentences(normalized)
        print(f"  [Narrator] {len(sentences)} sentences — generating with pauses...")

        if len(sentences) <= 1:
            path = self._speak_raw(normalized)
            return path, normalized

        silence_file = self._generate_silence(0.45)
        segment_files = []

        try:
            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue
                seg = self._speak_raw(sentence.strip(), label=f"seg{i}")
                segment_files.append(seg)

            interleaved = []
            for i, seg in enumerate(segment_files):
                interleaved.append(seg)
                if i < len(segment_files) - 1:
                    interleaved.append(silence_file)

            path = self._concatenate(interleaved)
            return path, normalized

        finally:
            for f in segment_files:
                try: f.unlink()
                except: pass
            try: silence_file.unlink()
            except: pass

    def _normalize_for_tts(self, script: str) -> str:
        """Single Claude call to rewrite all numbers/symbols as spoken words."""
        response = self.client.chat.completions.create(
            model=config.CLAUDE_MODEL,
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": f"""Rewrite this script so every number and symbol is written exactly as it should be SPOKEN ALOUD by a text-to-speech engine.

Rules:
- Decimal numbers: "4.2" → "four point two", "2.3" → "two point three"
- Prices: "$3,421" or "3421" → "three thousand four hundred and twenty one dollars"
- Percentages: "2.3%" → "two point three percent"
- Multipliers: "4.2x" or "4.2 times" → "four point two times normal volume"
- Large numbers: "1,500" → "one thousand five hundred"
- Arrows: "▲" → "up", "▼" → "down"
- Remove dollar signs, spell out "dollars" at end of price
- Keep ALL punctuation — periods create natural pauses
- Do NOT change any words — only fix numbers and symbols
- Output ONLY the rewritten script, nothing else

Script:
{script}"""
            }]
        )
        return response.choices[0].message.content.strip()

    def _split_sentences(self, text: str) -> list:
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]

    def _speak_raw(self, text: str, label: str = "full") -> Path:
        output_path = self.tmp_dir / f"{uuid.uuid4().hex[:8]}_{label}.wav"
        result = subprocess.run([
            "npx", "hyperframes", "tts",
            text,
            "--voice", self.voice,
            "--output", str(output_path)
        ], capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            raise RuntimeError(f"TTS failed: {result.stderr}")
        if not output_path.exists():
            raise RuntimeError(f"TTS produced no output at {output_path}")
        return output_path

    def _generate_silence(self, duration: float) -> Path:
        path = self.tmp_dir / f"silence_{uuid.uuid4().hex[:6]}.wav"
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=24000:cl=mono",
            "-t", str(duration),
            "-acodec", "pcm_s16le",
            str(path)
        ], capture_output=True, check=True)
        return path

    def _concatenate(self, audio_files: list) -> Path:
        output = self.tmp_dir / f"{uuid.uuid4().hex[:8]}_combined.wav"
        inputs = []
        for f in audio_files:
            inputs += ["-i", str(f)]
        filter_complex = "".join(f"[{i}:a]" for i in range(len(audio_files)))
        filter_complex += f"concat=n={len(audio_files)}:v=0:a=1[out]"
        result = subprocess.run([
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            str(output)
        ], capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"Audio concat failed: {result.stderr}")
        print(f"  [Narrator] ✓ Audio ready: {output}")
        return output

    def cleanup(self, audio_path: Path):
        try: audio_path.unlink()
        except: pass
