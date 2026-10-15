"""Narrate the demo video from its WebVTT captions with macOS text-to-speech.

    python3 scripts/narrate.py ../../phase2/phase2_demo.mp4 ../../phase2/phase2_demo.vtt [--voice "Ava (Premium)"]

Each cue is spoken at its start time; a clip longer than its cue window is sped up (at most 1.35x).
Writes <video>_narrated.mp4 (video copied, AAC audio) and <video>_narration.m4a.
"""

import argparse
import re
import subprocess
import tempfile
from pathlib import Path

MAX_TEMPO = 1.35


def parse_vtt(path: Path):
    cues = []
    for block in re.split(r"\n\s*\n", path.read_text().strip()):
        m = re.search(r"(\d\d):(\d\d):(\d\d\.\d+) --> (\d\d):(\d\d):(\d\d\.\d+)\n(.+)", block, re.S)
        if not m:
            continue
        h1, m1, s1, h2, m2, s2, text = m.groups()
        cues.append((int(h1) * 3600 + int(m1) * 60 + float(s1), int(h2) * 3600 + int(m2) * 60 + float(s2), " ".join(text.split())))
    return cues


def duration(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).decode().strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("vtt"); ap.add_argument("--voice", default="Karen (Premium)"); ap.add_argument("--rate", type=int, default=205)
    a = ap.parse_args()
    video, cues = Path(a.video), parse_vtt(Path(a.vtt))
    total = duration(video)
    tmp = Path(tempfile.mkdtemp(prefix="narrate-"))
    inputs, filters, mix = [], [], []
    tail = 0.0  # extra seconds the video must be extended (last frame frozen) so the final cue is not cut
    for i, (start, end, text) in enumerate(cues):
        aiff = tmp / f"{i:02d}.aiff"
        subprocess.run(["say", "-v", a.voice, "-r", str(a.rate), "-o", str(aiff), text], check=True)
        # a cue may speak until the next cue starts (captions often leave gaps); the last one may run past the video
        limit = cues[i + 1][0] if i + 1 < len(cues) else total
        window = max(1.0, limit - start - 0.25)
        tempo = min(MAX_TEMPO, max(1.0, duration(aiff) / window))
        if i + 1 == len(cues):
            tail = max(0.0, duration(aiff) / tempo - window + 0.5)
        inputs += ["-i", str(aiff)]
        filters.append(f"[{i}:a]atempo={tempo:.3f},aresample=48000,adelay={int(start * 1000)}|{int(start * 1000)}[a{i}]")
        mix.append(f"[a{i}]")
        print(f"cue {i + 1:>2} {start:7.1f}s  spoken {duration(aiff):5.1f}s / window {window:5.1f}s  tempo {tempo:.2f}")
    n = len(cues)
    total += tail
    graph = ";".join(filters) + f";{''.join(mix)}amix=inputs={n}:normalize=0:dropout_transition=0,apad=whole_dur={total:.3f}[out]"
    narration = video.with_name(video.stem + "_narration.m4a")
    subprocess.run(["ffmpeg", "-v", "warning", "-y", *inputs, "-filter_complex", graph, "-map", "[out]", "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", "128k", str(narration)], check=True)
    out = video.with_name(video.stem + "_narrated.mp4")
    vcodec = ["-c:v", "copy"] if tail == 0 else ["-vf", f"tpad=stop_mode=clone:stop_duration={tail:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(narration), "-map", "0:v", "-map", "1:a", *vcodec, "-c:a", "copy", "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)], check=True)
    if tail:
        print(f"video extended by {tail:.1f}s (last frame held) for the final cue")
    print("wrote", out, "and", narration)


if __name__ == "__main__":
    main()
