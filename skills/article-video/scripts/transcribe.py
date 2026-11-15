#!/usr/bin/env python3
"""Find the spoken segments in a narration recording and transcribe each one.

Usage:
  transcribe.py recording.m4a [--out segments.json] [--noise -38] [--min-pause 1.0]
  transcribe.py recording.m4a --pauses START END     # list quiet spots (for trimming false starts)

Speech recognition uses Whisper small.en via sherpa-onnx. The model is downloaded once from the
sherpa-onnx GitHub releases (Hugging Face is often blocked in sandboxes) into ~/.cache/article-video.
Output: JSON list of {"start","end","text"} plus a printed table, and level stats for the file.
"""
import argparse, glob, json, os, re, subprocess, sys, tarfile, wave
import numpy as np

CACHE = os.path.expanduser("~/.cache/article-video")
MODEL_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.en.tar.bz2"

def sh(*a, **k): return subprocess.run(list(a), check=True, **k)

def ensure_model():
    try:
        import sherpa_onnx  # noqa
    except ImportError:
        sh(sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "sherpa-onnx")
    d = glob.glob(CACHE + "/sherpa-onnx-whisper-*")
    if d: return d[0]
    os.makedirs(CACHE, exist_ok=True)
    tb = CACHE + "/model.tar.bz2"
    sh("curl", "-sSL", "-o", tb, MODEL_URL)
    with tarfile.open(tb) as t: t.extractall(CACHE)
    os.remove(tb)
    return glob.glob(CACHE + "/sherpa-onnx-whisper-*")[0]

def to_wav(src, dst, sr):
    sh("ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", str(sr), dst)
    w = wave.open(dst)
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

def db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)

def speech_segments(src, noise, min_pause, dur):
    o = subprocess.run(["ffmpeg", "-nostdin", "-i", src, "-af", f"silencedetect=noise={noise}dB:d={min_pause}",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", o)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", o)]
    sil = list(zip(starts, ends + [dur] * (len(starts) - len(ends))))
    segs, cur = [], 0.0
    for s, e in sil:
        if s - cur > 0.3: segs.append((max(0, cur - 0.05), s + 0.05))
        cur = e
    if dur - cur > 0.3: segs.append((max(0, cur - 0.05), dur))
    return segs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio"); ap.add_argument("--out", default="segments.json")
    ap.add_argument("--noise", type=float, default=-38); ap.add_argument("--min-pause", type=float, default=1.0)
    ap.add_argument("--pauses", nargs=2, type=float)
    a = ap.parse_args()
    work = os.path.splitext(a.out)[0] + "_work"; os.makedirs(work, exist_ok=True)
    x48 = to_wav(a.audio, work + "/mono48.wav", 48000)
    if a.pauses:
        s, e = a.pauses; f = int(0.05 * 48000); out = []
        for i in range(int(s * 48000), int(e * 48000), f):
            v = db(x48[i:i + f])
            if v < -45: out.append(f"{i / 48000:.2f}:{v:.0f}dB")
        print("quiet 50ms windows:", " ".join(out)); return
    dur = len(x48) / 48000
    peak = 20 * np.log10(np.max(np.abs(x48)) + 1e-9)
    print(f"duration {dur:.1f}s  peak {peak:.1f} dBFS  clipped samples {(np.abs(x48) > 0.99).sum()}")
    segs = speech_segments(a.audio, a.noise, a.min_pause, dur)
    pauses = [db(x48[int(e * 48000):int(s2 * 48000)]) for (_, e), (s2, _) in zip(segs, segs[1:]) if s2 - e > 0.4]
    if pauses: print(f"background level in pauses ~{np.median(pauses):.0f} dB")
    import sherpa_onnx
    d = ensure_model()
    pick = lambda pat: ([f for f in glob.glob(d + pat) if "int8" in f] or glob.glob(d + pat))[0]
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=pick("/*encoder*.onnx"), decoder=pick("/*decoder*.onnx"),
                                                     tokens=glob.glob(d + "/*tokens.txt")[0], language="en",
                                                     task="transcribe", num_threads=4)
    x16 = to_wav(a.audio, work + "/mono16.wav", 16000)
    res = []
    for s, e in segs:
        parts, t = [], s
        while t < e:
            u = min(e, t + 28)
            st = rec.create_stream(); st.accept_waveform(16000, x16[int(t * 16000):int(u * 16000)]); rec.decode_stream(st)
            parts.append(st.result.text.strip()); t = u
        txt = " ".join(p for p in parts if p)
        res.append(dict(start=round(s, 2), end=round(e, 2), text=txt))
        print(f"{s:7.2f}-{e:7.2f} ({e - s:4.1f}s) {txt}", flush=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print(f"wrote {a.out}")

if __name__ == "__main__":
    main()
