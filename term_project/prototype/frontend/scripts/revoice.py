"""Re-voice the assembled demo with an edge-tts neural voice and shorten each scene to its line.
Run on assemble.py output (phase2_demo.mp4 + .vtt), not on an already re-voiced video.
usage: revoice.py <phase2 dir> <out dir> [voice] [rate]   (needs `pip install edge-tts` and ffmpeg)"""
import json, subprocess, sys
from pathlib import Path
src, out = Path(sys.argv[1]), Path(sys.argv[2])
voice = sys.argv[3] if len(sys.argv) > 3 else "en-US-AvaNeural"
rate = sys.argv[4] if len(sys.argv) > 4 else "+8%"
END, PAD, MAXSPEED = 248.0, 0.3, 2.5  # cut before the broken status outro
tts = Path(sys.executable).parent / "edge-tts"
(out / "clips").mkdir(parents=True, exist_ok=True); (out / "segs").mkdir(exist_ok=True)

def sec(t): h, m, s = t.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
def ts(t): return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}"
def dur(p): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))
def ff(*a): subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)

cues = []
for b in (src / "phase2_demo.vtt").read_text().strip().split("\n\n")[1:]:
    _, tl, *txt = b.split("\n")
    a = sec(tl.split(" --> ")[0])
    if a < END: cues.append((a, " ".join(txt)))
starts = [a for a, _ in cues] + [END]
assert starts[0] < 0.5, "first cue must start at the beginning"
starts[0] = 0.0

new, t = [], 0.0
for i, (_, text) in enumerate(cues):
    clip = out / "clips" / f"{i:02d}.mp3"
    if not clip.exists():
        subprocess.run([str(tts), "--voice", voice, f"--rate={rate}", "--text", text, "--write-media", str(clip)], check=True, capture_output=True)
    a, b = starts[i], starts[i + 1]
    orig, want = b - a, dur(clip) + PAD
    speed = min(max(orig / want, 1.0), MAXSPEED)  # speed up the scene, never slow it
    length = max(want, 0.1)
    seg = out / "segs" / f"{i:02d}.mp4"
    # video: speed up, then hold the last frame or trim to exactly `length`
    vf = f"setpts=PTS/{speed:.4f},tpad=stop_mode=clone:stop_duration=30,trim=0:{length:.3f},setpts=PTS-STARTPTS,fps=30,format=yuv420p"
    af = f"apad,atrim=0:{length:.3f}"
    ff("-ss", f"{a:.3f}", "-t", f"{orig:.3f}", "-i", str(src / "phase2_demo.mp4"), "-i", str(clip),
       "-filter_complex", f"[0:v]{vf}[v];[1:a]aresample=48000,{af}[a]", "-map", "[v]", "-map", "[a]",
       "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(seg))
    new.append((t, t + dur(clip), text)); t += dur(seg)
    print(f"{i:02d} {orig:5.1f}s -> {length:5.1f}s (x{speed:.2f})")

lst = out / "segs" / "list.txt"
lst.write_text("".join(f"file '{p}'\n" for p in sorted((out / "segs").glob("*.mp4"))))
ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out / "phase2_demo_narrated.mp4"))
ff("-i", str(out / "phase2_demo_narrated.mp4"), "-an", "-c:v", "copy", str(out / "phase2_demo.mp4"))
ff("-i", str(out / "phase2_demo_narrated.mp4"), "-vn", "-c:a", "copy", str(out / "phase2_demo_narration.m4a"))
total = dur(out / "phase2_demo_narrated.mp4")
vtt = ["WEBVTT", "Kind: captions", "Language: en", ""] + [f"{i}\n{ts(a)} --> {ts(z)}\n{x}\n" for i, (a, z, x) in enumerate(new, 1)]
(out / "phase2_demo.vtt").write_text("\n".join(vtt))
md = ["# Phase 2 demo video — transcript", "", f"`phase2_demo.mp4`, {int(total // 60)}:{int(total % 60):02d}. On-screen captions, spoken narration and this transcript are the same text; times are when each line appears.", ""]
(out / "phase2_demo_transcript.md").write_text("\n".join(md + [f"- **{int(a // 60)}:{int(a % 60):02d}** {x}" for a, _, x in new]) + "\n")
print(f"total {total:.1f}s")
