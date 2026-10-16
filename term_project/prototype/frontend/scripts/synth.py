"""Synthesise every narration line with macOS TTS and record its duration.

    python3 scripts/synth.py scripts/narration.json <clips_dir>   -> writes <clips_dir>/timing.json
"""
import json, subprocess, sys
from pathlib import Path

spec = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
timing = {}
for key, text in spec["lines"].items():
    aiff = out / f"{key}.aiff"
    subprocess.run(["say", "-v", spec["voice"], "-r", str(spec["rate"]), "-o", str(aiff), text], check=True)
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(aiff)]).decode().strip())
    assert d > 0.5, f"{key}: empty clip"
    timing[key] = round(d, 3)
    print(f"{key:<11} {d:5.1f}s  {len(text.split()):>3} words")
(out / "timing.json").write_text(json.dumps(timing, indent=1))
print("total speech", round(sum(timing.values()), 1), "s")
