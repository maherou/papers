---
name: "article-video"
description: "Turn an article, essay, paper, blog post or any text into a short narrated explainer video (animated 1080p MP4, portrait by default, roughly 1–3 minutes) highlighting its key ideas — storyboard, narration script, the user's own voice recording cleaned up and synced to animated scenes. Use whenever the user wants a video, short video, explainer, animated summary, narrated slides, or \"something to post\" made from an article, PDF, URL, or pasted text, or wants to record narration for such a video, or sends a recording of a script to sync — even if they don't say \"skill\"."
---

# Article → short narrated video

This skill reproduces a workflow developed with Mike for "The Slide Rule Guide": Claude drafts a
storyboard and script from the article, renders an animated draft, Mike records the narration on his
phone, and Claude cleans the recording, picks the right takes, and syncs the animation to his voice. The user stays in the loop at every decision that is costly to redo.

Everything heavy is done by three scripts in `scripts/`:

- `render.py` — draws the animated scenes from a `scenes.json` file (contact sheet, silent draft, or
  synced video with audio muxed in). **Portrait 1080×1920 is the default** (Mike's preference for all
  videos); pass `--landscape` for 1920×1080. In portrait, headings wrap at ~25 characters and list
  items at ~35, so keep on-screen text short.
- `transcribe.py` — finds the spoken segments in a recording and transcribes each (Whisper via
  sherpa-onnx, model fetched from GitHub on first use).
- `build_audio.py` — cuts the chosen takes, cleans and level-matches them, assembles the narration
  with standard pauses, and normalizes the final mix. Writes `plan.json` for `render.py`.

Read `references/scenes.md` before writing a scenes file; `references/example-slide-rule.json` is a
complete worked example.

## Workflow

Keep a task list; this runs across several turns with the user away while recording.

### 1. Read the article

Fetch or read the source (URL, PDF, attachment, pasted text). Identify the thesis, the central
analogy or framework if there is one, the 3–6 supporting ideas, and the closing aphorism. If the
user wrote the article, the video should sound like them presenting their own ideas, not like a
review of the piece.

### 2. Storyboard and script — get approval

Propose 7–10 scenes for a 1.5–2.5 minute video: a title, the ideas in the article's own order, and
a closer built on its most quotable line. Map each idea to the scene type that fits its shape
(contrast → `compare`, framework → `cards`, examples → `list`, risks/lessons → `numbered`, keep vs.
change → `pills`, thesis → `statement`). Write the narration for each scene in the first person,
short sentences, 15–50 words per scene. If a writing-voice skill for the user is available (for Mike:
`heroux-writing-voice`), load it and draft the narration in that voice.

Show the user the storyboard with the narration text, one block per scene, and ask for changes
before rendering. Recording is the expensive step for them, so the script should be settled first.

### 3. Draft render

Write `scenes.json` (narration in each scene, cues on the elements). Then:

```bash
python3 scripts/render.py scenes.json --sheet sheet.png    # look at it: overlaps, overflow, empty space
python3 scripts/render.py scenes.json --out draft.mp4      # silent draft, timing estimated from the script
```

Inspect the contact sheet image yourself and fix layout problems before sending anything. Send the
draft video, and give the user the final narration script with recording tips:

- record it all in one go, in scene order, with a ~2 second pause between scenes;
- retakes are fine — just pause and say the scene again; the last complete take is used;
- small rewording while speaking is fine; the sync follows what is actually said;
- any format works (an iPhone Voice Memo .m4a is ideal).

### 4. Analyze the recording — advise before acting

When the recording arrives (attachment, or a file on the user's computer via the device bridge —
see Practical notes), run:

```bash
python3 scripts/transcribe.py recording.m4a --out segments.json
```

Match segments to scenes and pick the last complete take of each. Look for: false starts at the
end of a segment (find a cut point with `transcribe.py recording.m4a --pauses START END` and end the
take in the quiet gap before the false start), incomplete takes, noise at the very start, clipping,
and places where the spoken words differ from the on-screen text (e.g. the narration says "creative"
where a label says "critical" — the transcriber can also mishear, so ask rather than assume).

Then tell the user, briefly: what you found (quality, which takes you'll use, what you'll trim), the
proposed cleanup, and the resulting length — and wait for a go-ahead before
building. Mike asked for this explicitly; it is cheap for him to answer and expensive to redo.

If the user sends re-recordings for some scenes, transcribe the new file the same way and swap in
those takes; `build_audio.py` level-matches clips from different sessions automatically.

### 5. Build audio and the synced video

Write `takes.json` — one entry per scene in order, `{"source", "start", "end", "text"}` where
`text` is the transcript of that take (it drives the cue timing). Widen each segment from
`segments.json` by about 0.1 s on each side so word onsets and tails aren't clipped. Then:

```bash
python3 scripts/build_audio.py takes.json --outdir build
python3 scripts/render.py scenes.json --plan build/plan.json --frames chk T1 T2 ...   # spot-check
python3 scripts/render.py scenes.json --plan build/plan.json --audio build/mix.wav --out "<Title>.mp4"
```

Audio decisions baked into `build_audio.py` (change only if the user asks): high-pass at 80 Hz,
light denoise, gentle compression, every take matched to -18 LUFS, 2.2 s of silence before the first
scene's speech, 0.5 s before and 0.8 s after each later scene's speech, 5 s at the end; final mix
normalized to -16 LUFS / -1.5 dBTP.

Before delivering, check a few frames at moments where a cue should have just fired (an element
should be visible right after its phrase starts and absent just before), and that nothing on screen
contradicts the narration. If a cue fired in the wrong place, adjust the cue phrase rather than the
timing code.

### 6. Deliver

Send the MP4 with a one-line caption, and also save it to the user's Downloads folder when the
device bridge is available. Summarize in a few lines: which takes were used, and what was cleaned. Offer one natural next step (e.g. a 9:16 vertical cut, or
a caption file).

## Practical notes

- **Files on the user's Mac** are reached through the device bridge tools (request folder access,
  list, stage). macOS blocks some locations — notably `~/Library/Messages/Attachments`; if access is
  denied, ask the user to drag the file to Downloads or attach it in the chat rather than retrying.
- **Network**: Hugging Face is usually blocked in the workspace; `transcribe.py` fetches the Whisper
  model from the sherpa-onnx GitHub releases instead (≈640 MB, cached in `~/.cache/article-video`).
  There is no text-to-speech here — narration is always the user's own recording.
- **ffmpeg in shell loops** must use `-nostdin`, or it swallows the loop's input.
- **Render time** is about 40 s per minute of video; long renders are fine in the foreground with a
  generous timeout.
- **Fonts** are Liberation Serif/Sans (always present in the workspace). The palette is warm paper
  background, ink text, teal for good/keep, red for bad/retire, amber accents — keep it consistent
  across videos so they read as a series.
- **Revisions** are cheap after the first build: edit `scenes.json` (wording, cues, scene types) and
  re-run only `render.py`; re-run `build_audio.py` only if takes change.