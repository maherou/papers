#!/usr/bin/env python3
"""Render an animated 1080p explainer video (portrait 1080x1920 by default, --landscape for 1920x1080) from a scenes JSON file.

Usage:
  render.py scenes.json --sheet out.png              # contact sheet, one still per scene (end state)
  render.py scenes.json --out draft.mp4              # silent draft, timing estimated from narration text
  render.py scenes.json --plan plan.json --out v.mp4 [--audio mix.wav]
                                                     # timing synced to recorded narration, optional mux
  render.py scenes.json [--plan plan.json] --frames DIR T1 T2 ...   # stills at absolute times

Scene types: title, statement, compare, cards, list, numbered, pills, closer (see references/scenes.md).
Every revealable element may carry "cue": a phrase from the narration; the element fades in when
that phrase is spoken. Elements without a cue are spread out after the previous one.
"""
import argparse, json, math, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30                 # portrait by default; --landscape for 1920x1080
PORTRAIT = True
BG = (244, 239, 230); INK = (31, 42, 54); MUTED = (110, 116, 122)
AMBER = (196, 128, 36); TEAL = (40, 104, 108); RED = (163, 62, 42); CARD = (232, 224, 210)
TONES = {"good": TEAL, "bad": RED, "accent": AMBER, "neutral": INK}
FADE = 0.45; REVEAL = 0.7; WPS = 2.5          # words per second for draft timing
LEAD_FIRST, LEAD, TAIL, TAIL_LAST = 2.2, 0.5, 0.8, 5.0

FD = "/usr/share/fonts/truetype/liberation/"
_fc = {}
def F(kind, size):
    name = {"sb": "LiberationSerif-Bold.ttf", "si": "LiberationSerif-Italic.ttf", "s": "LiberationSans-Regular.ttf",
            "b": "LiberationSans-Bold.ttf", "m": "LiberationMono-Bold.ttf"}[kind]
    k = (name, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(FD + name, int(size))
    return _fc[k]

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def mix(c, a, bg=BG): return tuple(int(bg[i] + (c[i] - bg[i]) * a) for i in range(3))

# ---------------------------------------------------------------- text helpers
def fit(d, s, kind, size, maxw, minsize=28):
    while size > minsize and d.textlength(s, font=F(kind, size)) > maxw: size -= 2
    return F(kind, size)

def wrap(d, s, f, maxw):
    lines, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def text(d, xy, s, f, c, a, anchor="la", rise=28, bg=BG):
    if a <= 0 or not s: return
    d.text((xy[0], xy[1] + (1 - a) * rise), s, font=f, fill=mix(c, a, bg), anchor=anchor)

def para(d, x, y, s, f, c, a, maxw, lh, anchor="la", bg=BG):
    lines = wrap(d, s or "", f, maxw)
    for i, ln in enumerate(lines): text(d, (x, y + i * lh), ln, f, c, a, anchor=anchor, bg=bg)
    return len(lines) * lh

# ---------------------------------------------------------------- icons
def ic_pencil(d, cx, cy, s, a, bg):
    L = s * 2.2; th = L * 0.11; ang = -0.35
    def P(px, py):
        return (cx + px * math.cos(ang) - py * math.sin(ang), cy + px * math.sin(ang) + py * math.cos(ang))
    def poly(pts, col): d.polygon([P(*p) for p in pts], fill=mix(col, a, bg))
    x0 = -L / 2
    poly([(x0, -th/2), (x0+L*.07, -th/2), (x0+L*.07, th/2), (x0, th/2)], (214, 120, 130))
    poly([(x0+L*.07, -th/2), (x0+L*.14, -th/2), (x0+L*.14, th/2), (x0+L*.07, th/2)], (170, 170, 168))
    poly([(x0+L*.14, -th/2), (L*.32, -th/2), (L*.32, th/2), (x0+L*.14, th/2)], (232, 178, 52))
    poly([(x0+L*.14, -th/6), (L*.32, -th/6), (L*.32, th/6), (x0+L*.14, th/6)], (218, 160, 40))
    poly([(L*.32, -th/2), (L/2, 0), (L*.32, th/2)], (226, 196, 150))
    poly([(L*.44, -th*.17), (L/2, 0), (L*.44, th*.17)], INK)

def ic_calculator(d, cx, cy, s, a, bg):
    w = s * 0.75; h = w * 1.45; x0, y0 = cx - w/2, cy - h/2
    d.rounded_rectangle([x0, y0, x0+w, y0+h], radius=w*.08, fill=mix((48, 56, 66), a, bg))
    d.rounded_rectangle([x0+w*.1, y0+w*.1, x0+w*.9, y0+w*.38], radius=w*.03, fill=mix((176, 196, 160), a, bg))
    d.text((x0+w*.86, y0+w*.24), "3.14159", font=F("m", w*.15), fill=mix(INK, a, bg), anchor="rm")
    bw = w * .8 / 4
    for r in range(4):
        for c in range(4):
            bx, by = x0 + w*.1 + c*bw, y0 + w*.48 + r*bw*1.05
            d.rounded_rectangle([bx+bw*.1, by+bw*.1, bx+bw*.9, by+bw*.9], radius=bw*.12,
                                fill=mix(AMBER if c == 3 else (205, 205, 200), a, bg))

def ic_slide_rule(d, cx, cy, s, a, bg, shift=0.0):
    w = s * 2.6; h = w / 7.5; x, y = cx - w/2, cy - h/2
    body, edge = (238, 230, 205), (120, 100, 70)
    st, sh = h * .32, h * .36
    d.rectangle([x, y, x+w, y+st], fill=mix(body, a, bg), outline=mix(edge, a, bg), width=2)
    d.rectangle([x, y+h-st, x+w, y+h], fill=mix(body, a, bg), outline=mix(edge, a, bg), width=2)
    sx = x + shift * w
    d.rectangle([sx, y+st, sx+w, y+st+sh], fill=mix((250, 246, 232), a, bg), outline=mix(edge, a, bg), width=2)
    sw, off = w * .86, w * .07
    def ticks(ox, ty, down):
        for i in range(10, 101):
            v = i / 10; px = ox + off + sw * math.log10(v)
            major = abs(v - round(v)) < 1e-9; half = abs(v*2 - round(v*2)) < 1e-9
            ln = h * (.12 if major else .08 if half else .045)
            d.line([(px, ty), (px, ty + (ln if down else -ln))], fill=mix(INK, a, bg), width=2 if major else 1)
    ticks(x, y+st, False); ticks(sx, y+st, True); ticks(sx, y+st+sh, False); ticks(x, y+h-st, True)
    cxp = x + off + sw * math.log10(3) + w * .12
    d.rectangle([cxp-h*.18, y-h*.06, cxp+h*.18, y+h*1.06], outline=mix((90, 90, 95), a, bg), width=3)
    d.line([(cxp, y-h*.06), (cxp, y+h*1.06)], fill=mix(RED, a, bg), width=2)

def ic_book(d, cx, cy, s, a, bg):
    w = s * 1.1; h = s * .8
    for side in (-1, 1):
        pts = [(cx, cy - h/2 + 10), (cx + side*w, cy - h/2), (cx + side*w, cy + h/2), (cx, cy + h/2 + 10)]
        d.polygon(pts, fill=mix((250, 246, 236), a, bg), outline=mix(TEAL, a, bg))
        for k in range(1, 5):
            yy = cy - h/2 + k * h/5.5
            d.line([(cx + side*w*.15, yy + 8), (cx + side*w*.85, yy)], fill=mix(MUTED, a, bg), width=2)
    d.line([(cx, cy - h/2 + 10), (cx, cy + h/2 + 10)], fill=mix(TEAL, a, bg), width=4)

def ic_lightbulb(d, cx, cy, s, a, bg):
    r = s * .45
    d.ellipse([cx-r, cy-r*1.3, cx+r, cy+r*.7], fill=mix((246, 206, 92), a, bg))
    d.rectangle([cx-r*.42, cy+r*.55, cx+r*.42, cy+r*1.15], fill=mix((150, 150, 148), a, bg))
    for k in range(3):
        d.line([(cx-r*.42, cy+r*(.7+k*.18)), (cx+r*.42, cy+r*(.7+k*.18))], fill=mix(INK, a, bg), width=2)
    for k in range(7):
        ang = math.pi * (1.1 + k * 0.133)
        d.line([(cx + math.cos(ang)*r*1.25, cy - r*.3 + math.sin(ang)*r*1.25),
                (cx + math.cos(ang)*r*1.55, cy - r*.3 + math.sin(ang)*r*1.55)], fill=mix(AMBER, a, bg), width=4)

def ic_gear(d, cx, cy, s, a, bg):
    r = s * .42; col = mix(TEAL, a, bg)
    for k in range(8):
        ang = k * math.pi / 4
        pts = []
        for da, rr in ((-.18, r*.95), (-.12, r*1.25), (.12, r*1.25), (.18, r*.95)):
            pts.append((cx + math.cos(ang+da)*rr, cy + math.sin(ang+da)*rr))
        d.polygon(pts, fill=col)
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=col)
    d.ellipse([cx-r*.38, cy-r*.38, cx+r*.38, cy+r*.38], fill=bg)

def ic_check(d, cx, cy, s, a, bg):
    r = s * .45
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=mix(TEAL, a, bg))
    d.line([(cx-r*.45, cy), (cx-r*.1, cy+r*.38), (cx+r*.5, cy-r*.35)], fill=mix((255, 255, 255), a, bg), width=int(r*.18))

def ic_cross(d, cx, cy, s, a, bg):
    r = s * .45
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=mix(RED, a, bg))
    for sx in (-1, 1):
        d.line([(cx-r*.38*sx, cy-r*.38), (cx+r*.38*sx, cy+r*.38)], fill=mix((255, 255, 255), a, bg), width=int(r*.18))

ICONS = {"pencil": ic_pencil, "calculator": ic_calculator, "slide_rule": ic_slide_rule, "book": ic_book,
         "lightbulb": ic_lightbulb, "gear": ic_gear, "check": ic_check, "cross": ic_cross}

def icon(d, name, cx, cy, s, a, bg=BG, t=0.0):
    if not name or a <= 0: return
    if name == "slide_rule": ic_slide_rule(d, cx, cy, s, a, bg, shift=0.06 * math.sin(t * 0.9))
    else: ICONS[name](d, cx, cy, s, a, bg)

def strike(d, x0, y, x1, p, col=RED, w=8):
    if p > 0: d.line([(x0, y), (x0 + (x1 - x0) * min(p, 1), y)], fill=col, width=w)

def card(d, box, a):
    if a > 0: d.rounded_rectangle(box, radius=22, fill=mix(CARD, a))

# ---------------------------------------------------------------- elements & timing
def elements(sc):
    """Ordered list of (key, cue) for every revealable element of a scene."""
    t = sc["type"]; E = []
    def add(k, o): E.append((k, (o or {}).get("cue") if isinstance(o, dict) else None))
    if t == "title":
        for k in ("icon", "title", "subtitle", "byline"):
            if sc.get(k): E.append((k, None))
    elif t == "statement":
        if sc.get("heading"): E.append(("heading", None))
        if sc.get("icon"): E.append(("icon", None))
        for i, ln in enumerate(sc["lines"]): add(f"line{i}", ln)
    elif t in ("compare", "cards", "numbered"):
        E.append(("heading", None))
        for i, it in enumerate(sc["items"]):
            add(f"item{i}", it)
            if t == "numbered" and it.get("result"): E.append((f"result{i}", it.get("result_cue")))
            if t == "cards" and it.get("strike"): E.append((f"strike{i}", it.get("strike_cue")))
        if sc.get("footer"): add("footer", sc["footer"])
    elif t == "list":
        E.append(("heading", None))
        for i, it in enumerate(sc["items"]): add(f"item{i}", it)
        if sc.get("strike"): add("strike", sc["strike"])
        for i, ln in enumerate(sc.get("footer", [])): add(f"footer{i}", ln)
    elif t == "pills":
        E.append(("heading", None)); add("left", sc["left"]); add("right", sc["right"])
        for i, p in enumerate(sc["pills"]): add(f"pill{i}", p)
    elif t == "closer":
        if sc.get("icons"): E.append(("icons", None))
        for i, ln in enumerate(sc["lines"]): add(f"line{i}", ln)
        if sc.get("footer"): E.append(("footer", None))
    return E

def toks(s): return re.findall(r"[a-z0-9']+", (s or "").lower())

def find_cue(words, cue, start):
    """Word index where the cue phrase begins (best fuzzy match at or after `start`)."""
    c = toks(cue)
    if not c or not words: return None
    best, bi = -1, None
    for i in range(len(words)):
        score = sum(1 for j, w in enumerate(c) if i + j < len(words) and words[i + j] == w)
        score -= 0.01 * max(0, start - i)          # prefer matches after the previous cue
        if score > best: best, bi = score, i
    return bi if best >= max(1, len(c) * 0.5) else None

def reveal_times(sc, lead, speech, transcript):
    """Real seconds (from scene start) at which each element appears."""
    E = elements(sc); words = toks(transcript); n = max(1, len(words))
    if sc["type"] == "title":                      # title card builds immediately, during the opening pause
        return {k: 0.2 + i * 0.6 for i, (k, _) in enumerate(E)}
    times, prev, wi = {}, None, 0
    pending = []
    for k, cue in E:
        idx = find_cue(words, cue, wi) if cue else None
        if idx is not None:
            t = lead + speech * idx / n; wi = idx
            # spread un-cued elements waiting before this one
            base = prev if prev is not None else 0.0
            step = min(0.6, (t - base) / (len(pending) + 1))
            for j, pk in enumerate(pending):
                times[pk] = base + 0.2 + j * step
            pending = []
            times[k] = max(t, (prev if prev is not None else 0) + 0.25); prev = times[k]
        else:
            pending.append(k)
    base = prev if prev is not None else 0.0
    if pending:
        # untimed tail: if nothing in the scene had a cue, spread across the speech; else follow quickly
        span = (lead + speech * 0.85 - base) if prev is None else min(1.2 * len(pending), lead + speech - base)
        step = max(0.35, span / max(1, len(pending)))
        for j, pk in enumerate(pending): times[pk] = base + 0.2 + j * step
    return times

# ---------------------------------------------------------------- scene drawing
def A(R, k, t): return ease((t - R.get(k, 0)) / REVEAL) if k in R else 0.0

def draw_title(d, sc, R, t):
    icon(d, sc.get("icon"), W/2, 325, 470 if sc.get("icon") == "slide_rule" else 180, A(R, "icon", t), t=t)
    y0 = 520 if sc.get("icon") else 430
    text(d, (W/2, y0), sc["title"], fit(d, sc["title"], "sb", 112, 1760), INK, A(R, "title", t), anchor="mm")
    h = para(d, W/2, y0 + 100, sc.get("subtitle", ""), F("si", 46), MUTED, A(R, "subtitle", t), 1600, 58, anchor="mm")
    yb = y0 + 100 + max(h, 58) + 20
    a = A(R, "byline", t)
    if a > 0: d.line([(W/2-160, yb), (W/2+160, yb)], fill=mix(AMBER, a), width=4)
    text(d, (W/2, yb + 60), sc.get("byline", ""), F("s", 38), INK, a, anchor="mm")

LINE_STYLE = {"body": ("s", 52, INK), "emph": ("sb", 88, TEAL), "accent": ("sb", 64, AMBER),
              "warn": ("si", 46, RED), "quote": ("si", 52, INK), "small": ("s", 38, MUTED)}

def draw_statement(d, sc, R, t):
    top = 150
    if sc.get("heading"):
        text(d, (W/2, 150), sc["heading"], fit(d, sc["heading"], "sb", 80, 1700), INK, A(R, "heading", t), anchor="mm"); top = 260
    wide = sc.get("icon") == "slide_rule"          # wide icons sit above centered text
    has_icon = bool(sc.get("icon")) and not wide
    if wide:
        icon(d, "slide_rule", W/2, top + 110, 460, A(R, "icon", t), t=t); top += 250
    x, maxw, anchor = (720, 1100, "la") if has_icon else (W/2, 1600, "ma")
    blocks = []
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for ln in sc["lines"]:
        k, sz, col = LINE_STYLE.get(ln.get("style", "body"), LINE_STYLE["body"])
        if ln.get("tone"): col = TONES[ln["tone"]]
        f = F(k, sz); lines = wrap(tmp, ln["text"], f, maxw)
        blocks.append((f, col, lines, int(sz * 1.25), ln.get("gap", 0.45)))
    total = sum(len(b[2]) * b[3] + b[3] * b[4] for b in blocks) - blocks[-1][3] * blocks[-1][4]
    y = max(top, (H - total) / 2 + (40 if sc.get("heading") else 0))
    if has_icon: icon(d, sc["icon"], 420, H/2 + 20, 330, A(R, "icon", t), t=t)
    for i, (f, col, lines, lh, gap) in enumerate(blocks):
        a = A(R, f"line{i}", t)
        for j, s in enumerate(lines):
            text(d, (x, y + j * lh), s, f, col, a, anchor=anchor)
        y += len(lines) * lh + lh * gap

def draw_compare(d, sc, R, t):
    text(d, (W/2, 150), sc["heading"], fit(d, sc["heading"], "sb", 80, 1700), INK, A(R, "heading", t), anchor="mm")
    xs = [560, 1360]
    for i, it in enumerate(sc["items"][:2]):
        a = A(R, f"item{i}", t)
        icon(d, it.get("icon"), xs[i], 470, 220, a, t=t)
        text(d, (xs[i], 680), it["title"], fit(d, it["title"], "sb", 52, 700), TONES.get(it.get("tone"), INK), a, anchor="mm")
        para(d, xs[i], 730, it.get("body", ""), F("s", 38), MUTED, a, 680, 48, anchor="ma")
    a = A(R, "item1", t)
    if a > 0 and sc.get("arrow", True):
        d.line([(800, 480), (800 + 320 * a, 480)], fill=mix(AMBER, a), width=6)
        if a > .95: d.polygon([(1140, 480), (1112, 464), (1112, 496)], fill=AMBER)
    if sc.get("footer"):
        text(d, (W/2, 920), sc["footer"]["text"], F("si", 50), TEAL, A(R, "footer", t), anchor="mm")

def draw_cards(d, sc, R, t):
    text(d, (W/2, 130), sc["heading"], fit(d, sc["heading"], "sb", 72, 1760), INK, A(R, "heading", t), anchor="mm")
    n = len(sc["items"]); gap = 50
    cw = min(560, (1700 - (n - 1) * gap) / n); x0 = (W - (n * cw + (n - 1) * gap)) / 2
    for i, it in enumerate(sc["items"]):
        a = A(R, f"item{i}", t); cx = x0 + i * (cw + gap) + cw / 2
        card(d, [cx - cw/2, 230, cx + cw/2, 880], a)
        dim = 0.55 if it.get("strike") and A(R, f"strike{i}", t) > 0.5 else 1
        icon(d, it.get("icon"), cx, 430, min(170, cw * .32), a * dim, CARD if a > 0 else BG, t=t)
        tf = fit(d, it["title"], "sb", 54, cw - 50)
        text(d, (cx, 640), it["title"], tf, TONES.get(it.get("tone"), INK), a, anchor="mm", bg=CARD)
        para(d, cx, 690, it.get("body", ""), F("s", 36), INK, a, cw - 70, 48, anchor="ma", bg=CARD)
        if it.get("strike"): strike(d, cx - cw/2 + 30, 430, cx + cw/2 - 30, A(R, f"strike{i}", t), w=10)
    if sc.get("footer"):
        text(d, (W/2, 960), sc["footer"]["text"], fit(d, sc["footer"]["text"], "si", 44, 1800), INK, A(R, "footer", t), anchor="mm")

def draw_list(d, sc, R, t):
    text(d, (W/2, 140), sc["heading"], fit(d, sc["heading"], "sb", 72, 1760), INK, A(R, "heading", t), anchor="mm")
    n = len(sc["items"]); rh = min(130, 560 / max(1, n)); y0 = 330 - (rh - 130) / 2 if n <= 3 else 300
    f = F("s", 46 if n <= 4 else 40)
    for i, it in enumerate(sc["items"]):
        a = A(R, f"item{i}", t); y = y0 + i * rh
        card(d, [360, y - rh * .39, 1560, y + rh * .39], a)
        s = it["text"]
        text(d, (420, y), s, fit(d, s, "s", f.size, 1100), INK, a, anchor="lm", bg=CARD)
        if sc.get("strike"):
            strike(d, 420, y, 420 + d.textlength(s, font=fit(d, s, "s", f.size, 1100)),
                   ease((t - R.get("strike", 1e9) - i * 0.25) / 0.5), col=AMBER, w=5)
    yf = y0 + n * rh + 40
    for i, ln in enumerate(sc.get("footer", [])):
        text(d, (W/2, yf + i * 66), ln["text"], fit(d, ln["text"], "si", 48, 1700), INK, A(R, f"footer{i}", t), anchor="mm")

def draw_numbered(d, sc, R, t):
    text(d, (W/2, 130), sc["heading"], fit(d, sc["heading"], "sb", 80, 1760), INK, A(R, "heading", t), anchor="mm")
    n = len(sc["items"]); gap = 60; cw = (1580 - (n - 1) * gap) / n; x00 = (W - (n * cw + (n - 1) * gap)) / 2
    for i, it in enumerate(sc["items"]):
        a = A(R, f"item{i}", t)
        if a <= 0: continue
        x0 = x00 + i * (cw + gap)
        card(d, [x0, 240, x0 + cw, 900], a)
        d.ellipse([x0+40, 280, x0+130, 370], fill=mix(RED, a, CARD))
        text(d, (x0+85, 325), str(i+1), F("sb", 60), (255, 255, 255), a, anchor="mm", bg=RED, rise=0)
        text(d, (x0+160, 325), it["title"], fit(d, it["title"], "sb", 54, cw - 190), INK, a, anchor="lm", bg=CARD)
        para(d, x0+50, 430, it.get("body", ""), F("s", 42), INK, a, cw - 100, 56, bg=CARD)
        a2 = A(R, f"result{i}", t)
        if it.get("result") and a2 > 0:
            d.line([(x0+50, 660), (x0+cw-50, 660)], fill=mix(AMBER, a2, CARD), width=3)
            para(d, x0+50, 695, "→ " + it["result"], F("si", 44), RED, a2, cw - 100, 58, bg=CARD)

def draw_pills(d, sc, R, t):
    text(d, (W/2, 150), sc["heading"], fit(d, sc["heading"], "sb", 80, 1700), INK, A(R, "heading", t), anchor="mm")
    for k, x0, col in (("left", 170, TEAL), ("right", 1000, RED)):
        it = sc[k]; a = A(R, k, t); cx = x0 + 375
        col = TONES.get(it.get("tone"), col)
        card(d, [x0, 260, x0 + 750, 720], a)
        hh = para(d, cx, 300, it["title"], F("sb", 50), col, a, 660, 60, anchor="ma", bg=CARD)
        para(d, cx, 300 + hh + 50, it.get("body", ""), F("s", 40), INK, a, 640, 54, anchor="ma", bg=CARD)
    n = len(sc["pills"]); pw = min(460, (1700 - (n - 1) * 60) / max(1, n)); xs0 = W/2 - (n - 1) * (pw + 60) / 2
    for i, p in enumerate(sc["pills"]):
        a = A(R, f"pill{i}", t); x = xs0 + i * (pw + 60)
        if a <= 0: continue
        d.rounded_rectangle([x - pw/2, 790, x + pw/2, 880], radius=45, fill=mix(TEAL, a))
        text(d, (x, 835), p["text"], fit(d, p["text"], "b", 42, pw - 40), (255, 255, 255), a, anchor="mm", bg=TEAL, rise=0)

def draw_closer(d, sc, R, t):
    ics = sc.get("icons", []); a = A(R, "icons", t)
    if ics:
        xs = [W/2 + (i - (len(ics) - 1) / 2) * 400 for i in range(len(ics))]
        for i, ic in enumerate(ics):
            name = ic["icon"] if isinstance(ic, dict) else ic
            struck = isinstance(ic, dict) and ic.get("strike")
            ai = ease((t - R.get("icons", 0) - i * 0.3) / REVEAL) if "icons" in R else 0
            icon(d, name, xs[i], 270, 150, ai * (0.5 if struck else 1), t=t)
            if struck: strike(d, xs[i] - 180, 270, xs[i] + 180, ease((t - R.get("icons", 0) - len(ics) * 0.3) / 0.5))
    n = len(sc["lines"]); y0 = 600 - (n - 1) * 50 if ics else 540 - (n - 1) * 50
    for i, ln in enumerate(sc["lines"]):
        s = ln["text"]
        text(d, (W/2, y0 + i * 100), s, fit(d, s, "sb", 80, 1760), TONES.get(ln.get("tone", "good"), TEAL),
             A(R, f"line{i}", t), anchor="mm")
    if sc.get("footer"):
        text(d, (W/2, 960), sc["footer"], fit(d, sc["footer"], "s", 34, 1700), MUTED, A(R, "footer", t), anchor="mm")

DRAW = {"title": draw_title, "statement": draw_statement, "compare": draw_compare, "cards": draw_cards,
        "list": draw_list, "numbered": draw_numbered, "pills": draw_pills, "closer": draw_closer}


# ---------------------------------------------------------------- portrait (1080x1920) layouts
PM = 80; PW = 1080 - 2 * PM                       # side margin and content width

def p_heading(d, sc, R, t, y=250, size=76):
    s = sc.get("heading")
    if not s: return y - 60
    h = para(d, W/2, y, s, F("sb", size), INK, A(R, "heading", t), PW, int(size * 1.15), anchor="ma")
    return y + h

def p_title(d, sc, R, t):
    has = bool(sc.get("icon"))
    icon(d, sc.get("icon"), W/2, 600, 420 if sc.get("icon") == "slide_rule" else 220, A(R, "icon", t), t=t)
    y = 800 if has else 700
    h = para(d, W/2, y, sc["title"], F("sb", 104), INK, A(R, "title", t), PW, 118, anchor="ma")
    y += h + 30
    h = para(d, W/2, y, sc.get("subtitle", ""), F("si", 48), MUTED, A(R, "subtitle", t), PW - 40, 62, anchor="ma")
    yb = y + h + 50; a = A(R, "byline", t)
    if a > 0: d.line([(W/2-140, yb), (W/2+140, yb)], fill=mix(AMBER, a), width=4)
    para(d, W/2, yb + 40, sc.get("byline", ""), F("s", 40), INK, a, PW, 52, anchor="ma")

def p_statement(d, sc, R, t):
    top = p_heading(d, sc, R, t) + 80
    if sc.get("icon"):
        icon(d, sc["icon"], W/2, top + 150, 420 if sc["icon"] == "slide_rule" else 240, A(R, "icon", t), t=t); top += 330
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10))); blocks = []
    for ln in sc["lines"]:
        k, sz, col = LINE_STYLE.get(ln.get("style", "body"), LINE_STYLE["body"])
        if ln.get("tone"): col = TONES[ln["tone"]]
        f = F(k, sz); blocks.append((f, col, wrap(tmp, ln["text"], f, PW), int(sz * 1.25), max(ln.get("gap", 0.45), 0.1) + 0.25))
    total = sum(len(b[2]) * b[3] + b[3] * b[4] for b in blocks) - blocks[-1][3] * blocks[-1][4]
    y = max(top, (H - total) / 2 + 60)
    for i, (f, col, lines, lh, gap) in enumerate(blocks):
        a = A(R, f"line{i}", t)
        for j, s in enumerate(lines): text(d, (W/2, y + j * lh), s, f, col, a, anchor="ma")
        y += len(lines) * lh + lh * gap

def p_compare(d, sc, R, t):
    top = p_heading(d, sc, R, t)
    ys = [top + 240, top + 900]
    for i, it in enumerate(sc["items"][:2]):
        a = A(R, f"item{i}", t); y = ys[i]
        icon(d, it.get("icon"), W/2, y, 190, a, t=t)
        text(d, (W/2, y + 170), it["title"], fit(d, it["title"], "sb", 62, PW), TONES.get(it.get("tone"), INK), a, anchor="mm")
        para(d, W/2, y + 225, it.get("body", ""), F("s", 44), MUTED, a, PW - 60, 56, anchor="ma")
    a = A(R, "item1", t)
    if a > 0 and sc.get("arrow", True):
        y0 = ys[0] + 370; y1 = ys[1] - 130
        d.line([(W/2, y0), (W/2, y0 + (y1 - y0) * a)], fill=mix(AMBER, a), width=6)
        if a > .95: d.polygon([(W/2, y1 + 6), (W/2 - 18, y1 - 24), (W/2 + 18, y1 - 24)], fill=AMBER)
    if sc.get("footer"):
        para(d, W/2, ys[1] + 400, sc["footer"]["text"], F("si", 52), TEAL, A(R, "footer", t), PW, 66, anchor="ma")

def p_cards(d, sc, R, t):
    top = p_heading(d, sc, R, t) + 70
    n = len(sc["items"]); gap = 40; ch = min(400, (1200 - (n - 1) * gap) / n)
    top = max(top, (H - (n * ch + (n - 1) * gap + 160)) / 2 + 60)
    for i, it in enumerate(sc["items"]):
        a = A(R, f"item{i}", t); y0 = top + i * (ch + gap)
        card(d, [PM, y0, W - PM, y0 + ch], a)
        dim = 0.55 if it.get("strike") and A(R, f"strike{i}", t) > 0.5 else 1
        has = bool(it.get("icon")); tx = PM + 290 if has else PM + 50; tw = W - PM - 40 - tx
        icon(d, it.get("icon"), PM + 150, y0 + ch / 2, min(110, ch * .35), a * dim, CARD if a > 0 else BG, t=t)
        tf = fit(d, it["title"], "sb", 56, tw)
        bl = wrap(d, it.get("body", ""), F("s", 42), tw); bh = 70 + len(bl) * 54
        yt = y0 + (ch - bh) / 2
        text(d, (tx, yt), it["title"], tf, TONES.get(it.get("tone"), INK), a, bg=CARD)
        para(d, tx, yt + 74, it.get("body", ""), F("s", 42), INK, a, tw, 54, bg=CARD)
        if it.get("strike"): strike(d, PM + 30, y0 + ch / 2, W - PM - 30, A(R, f"strike{i}", t), w=10)
    if sc.get("footer"):
        para(d, W/2, top + n * (ch + gap) + 40, sc["footer"]["text"], F("si", 48), INK, A(R, "footer", t), PW, 62, anchor="ma")

def p_list(d, sc, R, t):
    top = p_heading(d, sc, R, t) + 90
    n = len(sc["items"]); f = F("s", 46)
    est = sum(50 + len(wrap(d, it["text"], f, PW - 100)) * 60 + 34 for it in sc["items"]) + 50 \
        + sum(len(wrap(d, ln["text"], F("si", 50), PW)) * 64 + 10 for ln in sc.get("footer", []))
    y = max(top, (H - est) / 2 + 60)
    for i, it in enumerate(sc["items"]):
        a = A(R, f"item{i}", t); lines = wrap(d, it["text"], f, PW - 100); rh = 50 + len(lines) * 60
        card(d, [PM, y, W - PM, y + rh], a)
        for j, s in enumerate(lines):
            text(d, (PM + 50, y + 25 + j * 60), s, f, INK, a, bg=CARD)
            if sc.get("strike"):
                strike(d, PM + 50, y + 25 + j * 60 + 30, PM + 50 + d.textlength(s, font=f),
                       ease((t - R.get("strike", 1e9) - i * 0.25) / 0.5), col=AMBER, w=5)
        y += rh + 34
    y += 50
    for i, ln in enumerate(sc.get("footer", [])):
        y += para(d, W/2, y, ln["text"], F("si", 50), INK, A(R, f"footer{i}", t), PW, 64, anchor="ma") + 10

def p_numbered(d, sc, R, t):
    top = p_heading(d, sc, R, t) + 70
    n = len(sc["items"]); gap = 44; ch = min(460, (1250 - (n - 1) * gap) / n)
    top = max(top, (H - (n * ch + (n - 1) * gap)) / 2 + 60)
    for i, it in enumerate(sc["items"]):
        a = A(R, f"item{i}", t)
        if a <= 0: continue
        y0 = top + i * (ch + gap); x0 = PM; cw = PW
        card(d, [x0, y0, x0 + cw, y0 + ch], a)
        d.ellipse([x0+40, y0+40, x0+130, y0+130], fill=mix(RED, a, CARD))
        text(d, (x0+85, y0+85), str(i+1), F("sb", 60), (255, 255, 255), a, anchor="mm", bg=RED, rise=0)
        th = para(d, x0+160, y0+52, it["title"], F("sb", 54), INK, a, cw - 200, 62, bg=CARD)
        yb = y0 + max(150, 52 + th + 30)
        yb += para(d, x0+50, yb, it.get("body", ""), F("s", 44), INK, a, cw - 100, 56, bg=CARD)
        a2 = A(R, f"result{i}", t)
        if it.get("result") and a2 > 0:
            d.line([(x0+50, yb + 30), (x0+cw-50, yb + 30)], fill=mix(AMBER, a2, CARD), width=3)
            para(d, x0+50, yb + 60, "→ " + it["result"], F("si", 46), RED, a2, cw - 100, 58, bg=CARD)

def p_pills(d, sc, R, t):
    top = p_heading(d, sc, R, t) + 70
    y = top
    for k, col in (("left", TEAL), ("right", RED)):
        it = sc[k]; a = A(R, k, t); col = TONES.get(it.get("tone"), col)
        tl_ = wrap(d, it["title"], F("sb", 56), PW - 80); bl = wrap(d, it.get("body", ""), F("s", 44), PW - 100)
        ch = 60 + len(tl_) * 66 + 30 + len(bl) * 56 + 50
        card(d, [PM, y, W - PM, y + ch], a)
        hh = para(d, W/2, y + 50, it["title"], F("sb", 56), col, a, PW - 80, 66, anchor="ma", bg=CARD)
        para(d, W/2, y + 50 + hh + 30, it.get("body", ""), F("s", 44), INK, a, PW - 100, 56, anchor="ma", bg=CARD)
        y += ch + 40
    y += 50; pw = 620
    for i, p in enumerate(sc["pills"]):
        a = A(R, f"pill{i}", t); yc = y + i * 125 + 50
        if a <= 0: continue
        d.rounded_rectangle([W/2 - pw/2, yc - 48, W/2 + pw/2, yc + 48], radius=48, fill=mix(TEAL, a))
        text(d, (W/2, yc), p["text"], fit(d, p["text"], "b", 46, pw - 60), (255, 255, 255), a, anchor="mm", bg=TEAL, rise=0)

def p_closer(d, sc, R, t):
    ics = sc.get("icons", [])
    if ics:
        xs = [W/2 + (i - (len(ics) - 1) / 2) * 290 for i in range(len(ics))]
        for i, ic in enumerate(ics):
            name = ic["icon"] if isinstance(ic, dict) else ic
            struck = isinstance(ic, dict) and ic.get("strike")
            ai = ease((t - R.get("icons", 0) - i * 0.3) / REVEAL) if "icons" in R else 0
            icon(d, name, xs[i], 620, 150, ai * (0.5 if struck else 1), t=t)
            if struck: strike(d, xs[i] - 130, 620, xs[i] + 130, ease((t - R.get("icons", 0) - len(ics) * 0.3) / 0.5))
    y = 900 if ics else 760
    for i, ln in enumerate(sc["lines"]):
        y += para(d, W/2, y, ln["text"], F("sb", 84), TONES.get(ln.get("tone", "good"), TEAL), A(R, f"line{i}", t), PW, 100, anchor="ma") + 30
    if sc.get("footer"):
        para(d, W/2, 1660, sc["footer"], F("s", 36), MUTED, A(R, "footer", t), PW, 48, anchor="ma")

PDRAW = {"title": p_title, "statement": p_statement, "compare": p_compare, "cards": p_cards,
         "list": p_list, "numbered": p_numbered, "pills": p_pills, "closer": p_closer}

# ---------------------------------------------------------------- timeline
def build_timeline(spec, plan):
    scenes = spec["scenes"]; tl = []; start = 0.0
    for i, sc in enumerate(scenes):
        if plan:
            p = plan[i]; lead, speech, tail = p["lead"], p["clip"], p["dur"] - p["lead"] - p["clip"]
            transcript = p.get("text") or sc.get("narration", "")
        else:
            transcript = sc.get("narration", "")
            speech = max(3.0, len(toks(transcript)) / WPS) if transcript else sc.get("duration", 6.0)
            lead = LEAD_FIRST if i == 0 else LEAD
            tail = TAIL_LAST if i == len(scenes) - 1 else TAIL
        dur = lead + speech + tail
        tl.append(dict(sc=sc, start=start, dur=dur, R=reveal_times(sc, lead, speech, transcript)))
        start += dur
    return tl, start

def frame(tl, total, si, t):
    e = tl[si]; img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    (PDRAW if PORTRAIT else DRAW)[e["sc"]["type"]](d, e["sc"], e["R"], t)
    d.rectangle([0, H - 8, W * (e["start"] + t) / total, H], fill=AMBER)
    a = 1.0
    if si > 0 and t < FADE: a = t / FADE
    if si < len(tl) - 1 and t > e["dur"] - FADE: a = (e["dur"] - t) / FADE
    if a < 1: img = Image.blend(Image.new("RGB", (W, H), BG), img, max(0.0, a))
    return img

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes"); ap.add_argument("--plan"); ap.add_argument("--out"); ap.add_argument("--audio")
    ap.add_argument("--sheet"); ap.add_argument("--frames", nargs="+")
    ap.add_argument("--landscape", action="store_true", help="1920x1080 instead of the default 1080x1920 portrait")
    a = ap.parse_args()
    global W, H, PORTRAIT
    if a.landscape: W, H, PORTRAIT = 1920, 1080, False
    spec = json.load(open(a.scenes)); plan = json.load(open(a.plan)) if a.plan else None
    for sc in spec["scenes"]:
        if sc["type"] not in DRAW: sys.exit(f"unknown scene type {sc['type']}")
    tl, total = build_timeline(spec, plan)
    if a.sheet:
        n = len(tl); cols = 5 if PORTRAIT else 3; rows = math.ceil(n / cols); tw, th = W // 3, H // 3
        sheet = Image.new("RGB", (tw * cols, th * rows), (255, 255, 255))
        for i, e in enumerate(tl):
            sheet.paste(frame(tl, total, i, e["dur"] - 0.6).resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
        sheet.save(a.sheet); print(f"sheet: {a.sheet}  total {total:.1f}s"); return
    if a.frames:
        outdir, times = a.frames[0], a.frames[1:]
        for ts in times:
            T = float(ts); si = max(i for i, e in enumerate(tl) if e["start"] <= T)
            frame(tl, total, si, T - tl[si]["start"]).save(f"{outdir}/t{ts}.png")
        return
    out = a.out; vid = out if not a.audio else out + ".video.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", vid], stdin=subprocess.PIPE)
    n = 0
    for si, e in enumerate(tl):
        end = round((e["start"] + e["dur"]) * FPS)
        while n < end:
            p.stdin.write(frame(tl, total, si, n / FPS - e["start"]).tobytes()); n += 1
    p.stdin.close(); p.wait()
    if a.audio:
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", vid, "-i", a.audio, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
        import os; os.remove(vid)
    print(f"wrote {out}  ({total:.1f}s)")

if __name__ == "__main__":
    main()
