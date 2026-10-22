#!/usr/bin/env python3
"""
Ad assembly engine: scenes.json  ->  9:16 MP4 (1080x1920, 30fps)

Usage:  python3 engine/assemble.py projects/<name>/scenes.json
Paths inside scenes.json are relative to the scenes.json folder.

Layouts
  news    : TV debate. top-left + top-right panels (anchor / guest), bottom B-roll,
            headline strips, BREAKING NEWS bar, scrolling ticker, LIVE bug.
  full    : one or more clips full-screen (app demo, UGC, B-roll montage).
  endcard : logo image / clip on a background + CTA line.
"""
import json, os, sys, subprocess, hashlib, math, re, shutil, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "templates", "layers.html")
W, H, FPS = 1080, 1920, 30
RECT = {  # x, y, w, h
    "left": (0, 120, 538, 640), "right": (542, 120, 538, 640), "top": (0, 120, 1080, 640),
    "bottom": (0, 900, 1080, 840), "full": (0, 0, 1080, 1920),
}
CAP_Y = {"news": 1590, "full": 1380, "endcard": 1450, "custom": 1380}
TICKER_Y, TICKER_X, TICKER_SPEED = 1840, 230, 170  # px/sec
# dialogue clean-up for AI voices: cut rumble/hiss, remove mud, add presence, even out level
VOICE_FX = ("highpass=f=90,lowpass=f=11500,afftdn=nf=-28:tn=1,"
            "equalizer=f=280:t=q:w=1.2:g=-3,equalizer=f=3200:t=q:w=1.0:g=3.5,equalizer=f=7500:t=q:w=1.5:g=-2,"
            "acompressor=threshold=-22dB:ratio=3.5:attack=4:release=90:makeup=3,alimiter=limit=0.93")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(" ".join(cmd)); print(r.stderr[-3000:]); sys.exit(1)
    return r.stdout


def probe_dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).strip())


def has_audio(p):
    return "audio" in run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", p])


# ---------------- layer rendering (HTML -> transparent PNG) ----------------
class Layers:
    def __init__(self, cache):
        from playwright.sync_api import sync_playwright
        self.cache = cache; os.makedirs(cache, exist_ok=True)
        self.pw = sync_playwright().start()
        self.br = self.pw.chromium.launch()
        self.pg = self.br.new_page(viewport={"width": 1080, "height": 1920})
        self.pg.goto("file://" + TEMPLATE)

    def png(self, kind, data):
        key = hashlib.md5(json.dumps([kind, data], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
        out = os.path.join(self.cache, f"{kind}_{key}.png")
        if os.path.exists(out): return out
        x, y, w, h = self.pg.evaluate("([k,d])=>renderLayer(k,d)", [kind, data])
        self.pg.evaluate("document.fonts.ready")
        if kind == "ticker": self.pg.set_viewport_size({"width": max(1080, w + 10), "height": 1920})
        self.pg.screenshot(path=out, omit_background=True, clip={"x": x, "y": y, "width": w, "height": h})
        if kind == "ticker": self.pg.set_viewport_size({"width": 1080, "height": 1920})
        return out

    def close(self):
        self.br.close(); self.pw.stop()


def png_size(p):
    out = run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", p]).strip()
    w, h = out.split(",")[:2]; return int(w), int(h)


# ---------------- captions ----------------
def chunk_caption(text, max_words=5):
    """Split on explicit '|' if present, else ~max_words per chunk (respects sentence ends)."""
    if "|" in text: return [c.strip() for c in text.split("|") if c.strip()]
    words, chunks, cur = text.split(), [], []
    for w_ in words:
        cur.append(w_)
        if len(cur) >= max_words or re.search(r"[।.!?,]$", w_):
            chunks.append(" ".join(cur)); cur = []
    if cur: chunks.append(" ".join(cur))
    return chunks


def caption_times(chunks, dur, lead=0.1):
    lens = [max(4, len(c.replace("*", ""))) for c in chunks]; tot = sum(lens); t = lead; out = []
    span = dur - lead - 0.15
    for c, L in zip(chunks, lens):
        d = span * L / tot; out.append((c, t, t + d)); t += d
    return out


# ---------------- scene rendering ----------------
def fit(label_in, label_out, w, h):
    return f"[{label_in}]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={FPS}[{label_out}]"


def render_scene(i, sc, cfg, base, L, tmp):
    lay = sc.get("layout", "news")
    inputs, fl = [], []

    def add_input(path, start=0.0, loop=True, image=False):
        p = os.path.join(base, path)
        if image: inputs.extend(["-loop", "1", "-i", p])
        else:
            if loop: inputs.extend(["-stream_loop", "-1"])
            if start: inputs.extend(["-ss", str(start)])
            inputs.extend(["-i", p])
        return len([x for x in inputs if x == "-i"]) - 1

    # ---- duration ----
    au = sc.get("audio", {})
    audio_src = None  # (input_index or path, start)
    clip_of = {"left": sc.get("left"), "right": sc.get("right"), "top": sc.get("top"),
               "clip": (sc.get("clips") or [None])[0] if lay == "full" else None}
    for ly in sc.get("layers", []):   # custom layout: audio {"from": "<layer id>"}
        if ly.get("id") and (ly.get("src") or ly.get("clips")):
            clip_of[ly["id"]] = {"clip": ly["src"], "start": ly.get("start", 0)} if ly.get("src") else ly["clips"][0]
    if "file" in au: audio_src = (os.path.join(base, au["file"]), au.get("start", 0))
    elif "from" in au and clip_of.get(au["from"]):
        c = clip_of[au["from"]]; audio_src = (os.path.join(base, c["clip"]), c.get("start", 0))
    dur = sc.get("duration")
    if dur is None:
        if audio_src: dur = probe_dur(audio_src[0]) - audio_src[1] - au.get("trim_end", 0)
        else: dur = 3.0
    dur = round(float(dur), 2)

    # ---- background ----
    bg = sc.get("bg", "#0b0b0b" if lay != "endcard" else "#ffffff")
    fl.append(f"color=c={bg}:s={W}x{H}:r={FPS}:d={dur}[base]")
    cur = "base"; n = 0

    def rect_of(r):
        if isinstance(r, str): return RECT[r]
        return tuple(int(v) for v in r)

    def overlay_anim(idx, x, y, anim, a0, a1, tag, size=None):
        """overlay a still layer with optional entrance animation: fade | slide-up | slide-left | blink"""
        nonlocal cur, n
        kind = anim.get("in", "none"); d = anim.get("dur", 0.3)
        pre = f"[{idx}:v]format=rgba" + (f",scale={size[0]}:{size[1]}" if size else "")
        if kind in ("fade", "slide-up", "slide-left"):
            pre += f",fade=t=in:st={a0}:d={d}:alpha=1"
        if anim.get("out_fade"):
            pre += f",fade=t=out:st={max(a0, a1 - d)}:d={d}:alpha=1"
        fl.append(pre + f"[p{tag}]")
        xe, ye = str(x), str(y)
        if kind == "slide-up": ye = f"'{y}+140*max(0\\,1-(t-{a0})/{d})'"
        if kind == "slide-left": xe = f"'{x}+220*max(0\\,1-(t-{a0})/{d})'"
        en = f"between(t\\,{a0}\\,{a1})"
        if anim.get("blink"): en += f"*lt(mod(t\\,1)\\,0.6)"
        fl.append(f"[{cur}][p{tag}]overlay=x={xe}:y={ye}:enable='{en}'[c{n}]"); cur = f"c{n}"; n += 1

    def place(spec, rect, tag, enable=None):
        """spec = {"clip": path, "start": s}; a .png/.jpg becomes a slow push-in still (listener fallback)"""
        nonlocal cur, n
        x, y, w, h = rect
        if spec["clip"].lower().endswith((".png", ".jpg", ".jpeg")):
            idx = add_input(spec["clip"], image=True); nf = int(round(dur * FPS)); z = spec.get("zoom", 1.06)
            fl.append(f"[{idx}:v]scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},setsar=1,"
                      f"zoompan=z='1+({z}-1)*on/{nf}':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':d={nf}:s={w}x{h}:fps={FPS}[v{tag}]")
        else:
            idx = add_input(spec["clip"], spec.get("start", 0))
            fl.append(fit(f"{idx}:v", f"v{tag}", w, h))
        en = f":enable='between(t\\,{enable[0]}\\,{enable[1]})'" if enable else ""
        fl.append(f"[{cur}][v{tag}]overlay={x}:{y}:shortest=0:eof_action=pass{en}[c{n}]"); cur = f"c{n}"; n += 1

    def place_seq(clips, rect, tag):
        """several clips back-to-back filling the rect for the scene duration"""
        nonlocal cur, n
        x, y, w, h = rect
        share = dur / len(clips); parts = []
        for k, c in enumerate(clips):
            idx = add_input(c["clip"], c.get("start", 0)) if not c["clip"].lower().endswith((".png", ".jpg", ".jpeg")) \
                else add_input(c["clip"], image=True)
            d = c.get("dur", share) if k < len(clips) - 1 else None
            parts.append((idx, d))
        # recompute so last fills remainder
        fixed = sum(d for _, d in parts if d); rem = max(0.1, dur - fixed)
        labs = []
        for k, (idx, d) in enumerate(parts):
            d = d or rem
            if clips[k]["clip"].lower().endswith((".png", ".jpg", ".jpeg")):
                # Ken Burns slow push-in on stills
                nf = int(round(d * FPS)); zmax = clips[k].get("zoom", 1.08)
                fl.append(f"[{idx}:v]scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},setsar=1,"
                          f"zoompan=z='1+({zmax}-1)*on/{nf}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nf}:s={w}x{h}:fps={FPS},"
                          f"trim=0:{d:.3f},setpts=PTS-STARTPTS[s{tag}{k}]")
            else:
                fl.append(f"[{idx}:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={FPS},trim=0:{d:.3f},setpts=PTS-STARTPTS[s{tag}{k}]")
            labs.append(f"[s{tag}{k}]")
        fl.append(f"{''.join(labs)}concat=n={len(labs)}:v=1:a=0[v{tag}]")
        fl.append(f"[{cur}][v{tag}]overlay={x}:{y}[c{n}]"); cur = f"c{n}"; n += 1

    if lay == "news":
        if sc.get("top"): place(sc["top"], RECT["top"], "t")
        else:
            if sc.get("left"): place(sc["left"], RECT["left"], "l")
            if sc.get("right"): place(sc["right"], RECT["right"], "r")
        if sc.get("bottom"): place_seq(sc["bottom"], RECT["bottom"], "b")
        d = dict(cfg.get("news", {})); d.update({k: sc[k] for k in (
            "headline_top", "headline_bottom", "left_name", "left_role", "right_name", "right_role") if k in sc})
        if sc.get("top"): d["split"] = False; d.pop("left_name", None); d.pop("right_name", None)
        ov = L.png("news", d)
        oi = add_input(os.path.relpath(ov, base), image=True)
        fl.append(f"[{cur}][{oi}:v]overlay=0:0[c{n}]"); cur = f"c{n}"; n += 1
        # ticker
        tk = L.png("ticker", {"items": cfg.get("ticker", ["ताज़ा खबरों के लिए देखते रहिए"])})
        tw, _ = png_size(tk)
        ti = add_input(os.path.relpath(tk, base), image=True)
        span = tw + (W - TICKER_X)
        t0 = cfg.get("_ticker_t0", 0.0)
        fl.append(f"[{ti}:v]crop=w=min(iw\\,{W - TICKER_X}):h=80:x='mod((t+{t0})*{TICKER_SPEED}\\,{span})-{W - TICKER_X}':y=0[tkr]".replace("min(iw\\,", "min(iw\\,"))
        # simpler & robust: overlay strip moving left within ticker band using a padded canvas
        fl.pop()
        fl.append(f"[{ti}:v]pad=w=iw+{2*(W - TICKER_X)}:h=80:x={W - TICKER_X}:y=0:color=white,"
                  f"crop=w={W - TICKER_X}:h=80:x='mod((t+{t0})*{TICKER_SPEED}\\,iw-{W - TICKER_X})':y=0[tkr]")
        fl.append(f"[{cur}][tkr]overlay={TICKER_X}:{TICKER_Y}[c{n}]"); cur = f"c{n}"; n += 1
        cfg["_ticker_t0"] = t0 + dur
        if cfg.get("live_bug", True):
            lv = L.png("live", {}); li = add_input(os.path.relpath(lv, base), image=True)
            fl.append(f"[{cur}][{li}:v]overlay=24:{RECT['bottom'][1] + 24}:enable='lt(mod(t\\,1)\\,0.6)'[c{n}]"); cur = f"c{n}"; n += 1

    elif lay == "full":
        place_seq(sc["clips"], RECT["full"], "f")

    elif lay == "custom":
        # free-form layer stack - any ad format. Layers draw in order (first = bottom).
        for k, ly in enumerate(sc.get("layers", [])):
            t = ly.get("type", "video"); tag = f"L{k}"
            x, y, w, h = rect_of(ly.get("rect", "full"))
            a0, a1 = ly.get("at", 0), ly.get("until", dur)
            if t in ("video", "image"):
                if ly.get("clips"):
                    place_seq(ly["clips"], (x, y, w, h), tag)
                else:
                    place({"clip": ly["src"], "start": ly.get("start", 0), "zoom": ly.get("zoom", 1.06)}, (x, y, w, h), tag,
                          enable=(a0, a1) if ("at" in ly or "until" in ly) else None)
            elif t in ("html", "png"):
                p = L.png("html", {"html": ly["html"], "w": w, "h": h, "css": cfg.get("css", "") + ly.get("css", "")}) \
                    if t == "html" else os.path.join(base, ly["src"])
                pi = add_input(os.path.relpath(p, base), image=True)
                overlay_anim(pi, x, y, ly.get("anim", {}), a0, a1, tag, size=(w, h) if t == "png" else None)
            elif t == "ticker":
                th = ly.get("h", 80)
                tk = L.png("ticker", {"items": ly["items"], "style": ly.get("style", {}), "h": th})
                ti = add_input(os.path.relpath(tk, base), image=True); key = f"_tk{k}"; t0 = cfg.get(key, 0.0)
                fl.append(f"[{ti}:v]pad=w=iw+{2*w}:h={th}:x={w}:y=0:color={ly.get('bg', 'white')},"
                          f"crop=w={w}:h={th}:x='mod((t+{t0})*{ly.get('speed', TICKER_SPEED)}\\,iw-{w})':y=0[tk{tag}]")
                fl.append(f"[{cur}][tk{tag}]overlay={x}:{y}[c{n}]"); cur = f"c{n}"; n += 1
                cfg[key] = t0 + dur
            elif t == "box":
                fl.append(f"[{cur}]drawbox=x={x}:y={y}:w={w}:h={h}:color={ly.get('color', 'black@0.5')}:t=fill"
                          f":enable='between(t\\,{a0}\\,{a1})'[c{n}]"); cur = f"c{n}"; n += 1

    elif lay == "endcard":
        if sc.get("clip"): place_seq([{"clip": sc["clip"]}], RECT["full"], "e")
        if sc.get("image"):
            ii = add_input(sc["image"], image=True); mw = sc.get("image_width", 640)
            fl.append(f"[{ii}:v]scale={mw}:-1,format=rgba[logo]")
            fl.append(f"[{cur}][logo]overlay=(W-w)/2:(H-h)/2-120[c{n}]"); cur = f"c{n}"; n += 1

    # ---- captions ----
    cap_on = sc.get("captions", cfg.get("captions", True))
    text = sc.get("caption") or (sc.get("cta") if lay == "endcard" else None)
    if cap_on and text:
        y0 = sc.get("caption_y", CAP_Y[lay])
        timed = [(text.replace("|", "\n"), 0, dur)] if lay == "endcard" else caption_times(chunk_caption(text, cfg.get("caption_words", 5)), dur)
        for k, (c, a, b) in enumerate(timed):
            p = L.png("caption", {"text": c, "style": sc.get("caption_style", cfg.get("caption_style", "box"))}); ci = add_input(os.path.relpath(p, base), image=True)
            fl.append(f"[{cur}][{ci}:v]overlay=(W-w)/2:{y0}-h/2:enable='between(t\\,{a:.2f}\\,{b:.2f})'[c{n}]"); cur = f"c{n}"; n += 1

    fx_in = f",fade=t=in:st=0:d={sc['fade_in']}" if sc.get("fade_in") else ""
    fx_out = f",fade=t=out:st={dur - sc['fade_out']:.2f}:d={sc['fade_out']}" if sc.get("fade_out") else ""
    fl.append(f"[{cur}]format=yuv420p,trim=0:{dur},setpts=PTS-STARTPTS{fx_in}{fx_out}[vout]")

    # ---- audio ----
    amix = []
    if audio_src:
        if os.path.abspath(audio_src[0]) in [os.path.abspath(os.path.join(base, x)) for x in []]: pass
        inputs.extend(["-ss", str(audio_src[1]), "-i", audio_src[0]]); ai = len([x for x in inputs if x == "-i"]) - 1
        vol = au.get("volume", 1.0)
        fx = VOICE_FX if au.get("fx", cfg.get("voice_fx", True)) else "anull"
        fl.append(f"[{ai}:a]atrim=0:{dur},asetpts=PTS-STARTPTS,aresample=48000,{fx},aformat=channel_layouts=stereo,volume={vol},"
                  f"afade=t=in:st=0:d=0.03,afade=t=out:st={max(0, dur-0.12):.2f}:d=0.12,apad=whole_dur={dur}[a0]"); amix.append("[a0]")
    for k, extra in enumerate(sc.get("sfx", [])):
        p = os.path.join(base, extra["file"]); inputs.extend(["-i", p]); ai = len([x for x in inputs if x == "-i"]) - 1
        ms = int(extra.get("at", 0) * 1000)
        fl.append(f"[{ai}:a]aresample=48000,aformat=channel_layouts=stereo,volume={extra.get('volume',0.8)},adelay={ms}|{ms},apad=whole_dur={dur},atrim=0:{dur}[sx{k}]"); amix.append(f"[sx{k}]")
    if not amix:
        fl.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{dur}[aout]")
    elif len(amix) == 1:
        fl.append(f"{amix[0]}anull[aout]")
    else:
        fl.append(f"{''.join(amix)}amix=inputs={len(amix)}:normalize=0:duration=first[aout]")

    out = os.path.join(tmp, f"scene_{i:02d}.mp4")
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fl), "-map", "[vout]", "-map", "[aout]",
           "-t", str(dur), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", out]
    run(cmd)
    print(f"  scene {i+1}: {lay:8s} {dur:5.2f}s")
    return out, dur


def main(spec_path):
    spec_path = os.path.abspath(spec_path); base = os.path.dirname(spec_path)
    cfg = json.load(open(spec_path, encoding="utf-8"))
    tmp = os.path.join(base, "_build"); os.makedirs(tmp, exist_ok=True)
    L = Layers(os.path.join(tmp, "layers"))
    try:
        parts = [render_scene(i, sc, cfg, base, L, tmp) for i, sc in enumerate(cfg["scenes"])]
    finally:
        L.close()
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p, _ in parts))
    total = sum(d for _, d in parts)
    out = os.path.join(base, cfg.get("output", "final.mp4"))
    joined = os.path.join(tmp, "joined.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    # final: optional BGM + loudness normalise
    inputs = ["-i", joined]; af = "[0:a]"
    if cfg.get("bgm"):
        inputs += ["-stream_loop", "-1", "-i", os.path.join(base, cfg["bgm"])]
        af = (f"[1:a]volume={cfg.get('bgm_volume', 0.12)},atrim=0:{total},aformat=channel_layouts=stereo[bg];"
              f"[0:a][bg]amix=inputs=2:normalize=0:duration=first")
        af += ",loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    else:
        af += "loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", af, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", out])
    print(f"done -> {out}  ({total:.1f}s)")


if __name__ == "__main__":
    main(sys.argv[1])
