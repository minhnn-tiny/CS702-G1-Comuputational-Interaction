"""Synthesise every narration line and record its duration.

    python3 scripts/synth.py scripts/<narration>.json <clips_dir>   -> writes <clips_dir>/<key>.aiff + timing.json

`voice` is either a macOS `say` voice ("Karen (Premium)") or an edge-tts neural voice ("en-US-AvaNeural", needs the
prototype venv's `edge-tts` and network); `rate` is words per minute for `say` or a percentage string for edge-tts.
"""
import json, subprocess, sys
from pathlib import Path

spec = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
voice, rate = spec["voice"], spec.get("rate", 190)
edge = "Neural" in voice
tts = Path(__file__).resolve().parents[2] / ".venv" / "bin" / "edge-tts"
timing = {}
for key, text in spec["lines"].items():
    aiff = out / f"{key}.aiff"
    if edge:
        mp3 = out / f"{key}.mp3"
        subprocess.run([str(tts), "--voice", voice, f"--rate={rate}", "--text", text, "--write-media", str(mp3)], check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ar", "48000", str(aiff)], check=True)
    else:
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff), text], check=True)
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(aiff)]).decode().strip())
    assert d > 0.5, f"{key}: empty clip"
    timing[key] = round(d, 3)
    print(f"{key:<11} {d:5.1f}s  {len(text.split()):>3} words")
(out / "timing.json").write_text(json.dumps(timing, indent=1))
print("total speech", round(sum(timing.values()), 1), "s")
