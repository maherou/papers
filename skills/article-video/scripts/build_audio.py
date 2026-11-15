#!/usr/bin/env python3
"""Cut, clean, level-match and assemble the narration, then normalize the final mix.

Usage:
  build_audio.py takes.json --outdir build

takes.json — one entry per scene, in scene order (the chosen take for each):
  [{"source": "recording.m4a", "start": 2.70, "end": 12.60, "text": "transcript of this take"}, ...]

Writes build/plan.json (per-scene start, lead, clip, dur, text — feed to render.py --plan),
build/voice.wav and build/mix.wav (final audio, -16 LUFS).
"""
import argparse, json, os, subprocess

CHAIN = "highpass=f=80,afftdn=nr=8:nf=-55,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=200:makeup=2"
TARGET_CLIP_LUFS = -18.0
LEAD_FIRST, LEAD, TAIL, TAIL_LAST = 2.2, 0.5, 0.8, 5.0

def ff(*a): subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", *a], check=True)
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
def lufs(f):
    o = subprocess.run(["ffmpeg", "-nostdin", "-i", f, "-af", CHAIN + ",loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    i = o.rindex("{")                         # newer ffmpeg prints more after the JSON block
    return float(json.loads(o[i:o.index("}", i) + 1])["input_i"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("takes"); ap.add_argument("--outdir", default="build")
    a = ap.parse_args()
    takes = json.load(open(a.takes)); takes = takes["takes"] if isinstance(takes, dict) else takes
    os.makedirs(a.outdir, exist_ok=True); n = len(takes)
    plan, t = [], 0.0
    for i, tk in enumerate(takes):
        raw = f"{a.outdir}/clip{i+1}.wav"; proc = f"{a.outdir}/clean{i+1}.wav"
        # cut with short fades so edits are click-free
        ff("-i", tk["source"], "-ss", str(tk["start"]), "-to", str(tk["end"]), "-ac", "1", "-ar", "48000",
           "-af", "afade=t=in:d=0.03,areverse,afade=t=in:d=0.08,areverse", raw)
        gain = TARGET_CLIP_LUFS - lufs(raw)       # level-match takes (different sessions differ by several dB)
        ff("-i", raw, "-af", f"{CHAIN},volume={gain:.2f}dB", proc)
        d = dur(proc)
        lead = LEAD_FIRST if i == 0 else LEAD; tail = TAIL_LAST if i == n - 1 else TAIL
        plan.append(dict(scene=i + 1, start=round(t, 3), lead=lead, clip=round(d, 3), dur=round(lead + d + tail, 3),
                         gain_db=round(gain, 1), text=tk.get("text", "")))
        t += lead + d + tail
    total = t
    json.dump(plan, open(f"{a.outdir}/plan.json", "w"), indent=1)
    ins = sum([["-i", f"{a.outdir}/clean{i+1}.wav"] for i in range(n)], [])
    fc = "".join(f"[{i}]adelay={int((p['start'] + p['lead']) * 1000)}:all=1[v{i}];" for i, p in enumerate(plan))
    fc += "".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,apad=whole_dur={total}[out]"
    ff(*ins, "-filter_complex", fc, "-map", "[out]", "-ar", "48000", f"{a.outdir}/voice.wav")
    ff("-i", f"{a.outdir}/voice.wav", "-af", "aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11",
       "-ar", "48000", f"{a.outdir}/mix.wav")
    print(f"total {total:.1f}s")
    for p in plan: print(f"  scene {p['scene']}: start {p['start']:.1f}s  speech {p['clip']:.1f}s  level adj {p['gain_db']:+.1f} dB")
    print(f"wrote {a.outdir}/plan.json, voice.wav, mix.wav")

if __name__ == "__main__":
    main()
