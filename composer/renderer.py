"""
Renderer — runs Hyperframes CLI on a project folder.
Renders index.html → MP4 via headless Chrome + ffmpeg.
"""
import subprocess
import sys
from pathlib import Path

ROOT   = Path(__file__).parent.parent
PARENT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PARENT))
try:    import cryptoviz_v3.config as config
except: 
    try:    import config
    except: sys.path.insert(0, str(PARENT.parent)); import config


class HyperframesRenderer:

    def render(self, project_dir: Path, quality: str = "standard") -> Path:
        """
        Render a Hyperframes project folder to MP4.
        Returns path to the rendered MP4.
        """
        output = project_dir / "render.mp4"
        print(f"  [Renderer] Rendering {project_dir.name}...")

        # First lint
        lint = subprocess.run(
            ["npx", "hyperframes", "lint", "--json", str(project_dir)],
            capture_output=True, text=True, timeout=60,
            cwd=str(project_dir)
        )
        try:
            import json
            errors = json.loads(lint.stdout).get("errors", []) if lint.stdout.strip() else []
            if errors:
                print(f"  [Renderer] {len(errors)} lint issue(s) (rendering anyway)")
                for e in errors[:3]:
                    print(f"    - {e}")
        except Exception:
            pass

        # Render
        result = subprocess.run([
            "npx", "hyperframes", "render",
            "--output", str(output),
            "--quality", quality,
        ], capture_output=True, text=True, timeout=600,
           cwd=str(project_dir))

        if result.returncode != 0:
            print(f"  [Renderer] stderr: {result.stderr[-500:]}")
            raise RuntimeError(f"Render failed (exit {result.returncode})")

        print(f"  [Renderer] ✓ {output}")
        return output

    def composite(self, video_path: Path, audio_path: Path) -> Path:
        """Combine silent MP4 with narration audio."""
        output = video_path.parent / "final.mp4"
        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(output)
        ], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"Composite failed: {result.stderr[-300:]}")
        print(f"  [Renderer] ✓ Final: {output}")
        return output
