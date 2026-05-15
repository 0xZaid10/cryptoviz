# cryptoviz/composer/transcriber.py
"""
Transcribes audio using Hyperframes' built-in Whisper (local, free).
Hyperframes writes transcript.json to CWD — we run from project dir.

Caption timing fix:
- Whisper timestamps are relative to the WAV file (start=0)
- In the final video, audio starts at a specific offset (default 7s for scene 2)
- We store raw timestamps and let the builder add the offset
- This way any scene offset change only needs updating in one place
"""

import subprocess
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))

# Hyperframes transcribe writes transcript.json to CWD
PROJECT_DIR = Path(__file__).parent.parent  # ~/heygen/cryptovizv2/


class Transcriber:
    def transcribe(self, audio_path: Path) -> list:
        """
        Transcribe audio and return word-level timestamps.
        Returns raw timestamps (relative to audio file start = 0).
        Caller adds scene offset when building captions.
        """
        audio_path      = Path(audio_path).resolve()
        transcript_path = PROJECT_DIR / "transcript.json"

        # Clean stale transcript
        if transcript_path.exists():
            transcript_path.unlink()

        print(f"  [Transcriber] Transcribing {audio_path.name}...")

        result = subprocess.run(
            ["npx", "hyperframes", "transcribe",
             str(audio_path), "--model", "base"],
            capture_output=True, text=True,
            timeout=600,
            cwd=str(PROJECT_DIR)
        )

        if result.returncode != 0:
            print(f"  [Transcriber] Warning: {result.stderr[:200]}")
            return []

        if not transcript_path.exists():
            print("  [Transcriber] Warning: transcript.json not found")
            return []

        try:
            raw   = json.loads(transcript_path.read_text())
            words = self._normalize(raw)
            if words:
                print(f"  [Transcriber] ✓ {len(words)} words | "
                      f"span: {words[0]['start']:.1f}s → {words[-1]['end']:.1f}s")
            return words
        except Exception as e:
            print(f"  [Transcriber] Parse error: {e}")
            return []

    def _normalize(self, raw) -> list:
        items = raw if isinstance(raw, list) else (
            raw.get("words") or raw.get("segments") or []
        )
        result = []
        for w in items:
            if not isinstance(w, dict) or "text" not in w:
                continue
            text = w["text"].strip()
            if not text:
                continue
            result.append({
                "text":  text,
                "start": float(w.get("start", 0)),
                "end":   float(w.get("end", w.get("start", 0) + 0.3)),
            })
        return result

    def cleanup(self, audio_path: Path = None):
        p = PROJECT_DIR / "transcript.json"
        try: p.unlink()
        except: pass
