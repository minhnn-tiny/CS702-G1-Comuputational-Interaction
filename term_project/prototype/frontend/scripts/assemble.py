"""Lay the narration clips and WebVTT captions on the recorded video's timeline.

    python3 scripts/assemble.py scripts/demo.config.json

Reads <out>/cues.json written by demo.mjs (caption id + seconds since its segment started), measures each segment's
webm duration to turn those into absolute times, then writes next to the mp4:
  <stem>.vtt              captions (identical text to the on-screen captions and the audio)
  <stem>_narrated.mp4     video + spoken narration (each clip starts exactly when its caption appears)
  <stem>_transcript.md    the same lines with timestamps
"""
import json
import subprocess
import sys
from pathlib import Path

cfg_path = Path(sys.argv[1]).resolve()
cfg = json.loads(cfg_path.read_text())
here = cfg_path.parent.parent  # config paths are relative to the frontend directory, where demo.mjs runs
lines = json.loads((cfg_path.parent / "narration.json").read_text())["lines"]
out = (here / cfg["out"]).resolve()
clips = (here / cfg["clips"]).resolve()
timing = json.loads((clips / "timing.json").read_text())
mp4 = (here / cfg["mp4"]).resolve()
log = json.loads((out / "cues.json").read_text())


def dur(p: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).decode().strip())


offset, starts = 0.0, {}
for f in log["files"]:
    starts[f.split("-", 1)[1].rsplit(".", 1)[0]] = offset
    offset += dur(out / f)
total = dur(mp4)
cues = [(starts[c["segment"]] + c["t"], c["id"]) for c in log["cues"]]


def ts(t: float) -> str:
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}"


vtt = ["WEBVTT", "Kind: captions", "Language: en", ""]
md = ["# Phase 2 demo video — transcript", "", f"`{mp4.name}`, {int(total // 60)}:{int(total % 60):02d}. On-screen captions, spoken narration and this transcript are the same text; times are when each line appears.", ""]
for i, (t, cid) in enumerate(cues):
    end = min(t + timing[cid], cues[i + 1][0] if i + 1 < len(cues) else total)
    vtt += [str(i + 1), f"{ts(t)} --> {ts(end)}", lines[cid], ""]
    md.append(f"- **{int(t // 60)}:{int(t % 60):02d}** {lines[cid]}")
(mp4.with_suffix(".vtt")).write_text("\n".join(vtt))
(mp4.with_name(mp4.stem + "_transcript.md")).write_text("\n".join(md) + "\n")

inputs, filters, mix = [], [], []
for i, (t, cid) in enumerate(cues):
    inputs += ["-i", str(clips / f"{cid}.aiff")]
    ms = int(t * 1000)
    filters.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms}[a{i}]")
    mix.append(f"[a{i}]")
graph = ";".join(filters) + f";{''.join(mix)}amix=inputs={len(cues)}:normalize=0:dropout_transition=0,apad=whole_dur={total:.3f}[out]"
narration = mp4.with_name(mp4.stem + "_narration.m4a")
subprocess.run(["ffmpeg", "-v", "warning", "-y", *inputs, "-filter_complex", graph, "-map", "[out]", "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", "128k", str(narration)], check=True)
narrated = mp4.with_name(mp4.stem + "_narrated.mp4")
subprocess.run(["ffmpeg", "-v", "warning", "-y", "-i", str(mp4), "-i", str(narration), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", str(narrated)], check=True)
peak = subprocess.run(["ffmpeg", "-i", str(narration), "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
assert "max_volume" in peak and "-91.0 dB" not in peak, "narration track is silent"
print(f"{len(cues)} cues over {total:.1f}s; wrote {narrated.name}, {mp4.with_suffix('.vtt').name}, transcript")
print(peak[peak.index("max_volume"):].splitlines()[0])
