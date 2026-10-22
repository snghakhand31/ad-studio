#!/usr/bin/env python3
"""
Clip QA for generated ad footage.

  python3 engine/qa.py speaker  <clip.mp4> "<expected dialogue>"   # must speak this line, lips moving
  python3 engine/qa.py listener <clip.mp4>                         # must NOT speak / lip-move
  python3 engine/qa.py broll    <clip.mp4>                         # just contact sheet + basic checks
  python3 engine/qa.py batch    <qa_plan.json>                     # many clips -> qa_report.json

Every mode writes <clip>.sheet.jpg (8-frame contact sheet) for visual review and prints a JSON verdict:
  {"clip":..., "verdict":"pass|warn|fail", "issues":[...], "metrics":{...}}
"""
import json, os, re, subprocess, sys, unicodedata, difflib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FACE_MODEL = os.path.join(HERE, "models", "face_landmarker.task")
_whisper = None


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=False).stdout


def duration(p):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode().strip())


def audio16k(p):
    raw = sh(["ffmpeg", "-v", "error", "-i", p, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"])
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def transcribe(p):
    global _whisper
    from faster_whisper import WhisperModel
    if _whisper is None:
        _whisper = WhisperModel(os.environ.get("QA_WHISPER", "small"), device="cpu", compute_type="int8")
    segs, _ = _whisper.transcribe(audio16k(p), language="hi", vad_filter=True)
    segs = list(segs)
    return " ".join(s.text.strip() for s in segs), (segs[0].start if segs else None), (segs[-1].end if segs else None)


def norm_hi(t):
    """normalise Hindi text so whisper spelling noise doesn't dominate the score"""
    t = unicodedata.normalize("NFC", t)
    t = t.replace("़", "")                       # nukta
    t = re.sub(r"[ँं]", "ं", t)        # chandrabindu -> anusvara
    t = re.sub(r"[ीि]", "ि", t); t = re.sub(r"[ूु]", "ु", t)   # long/short i,u
    t = re.sub(r"[^ऀ-ॿa-zA-Z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def similarity(a, b):
    a, b = norm_hi(a), norm_hi(b)
    return round(difflib.SequenceMatcher(None, a, b).ratio(), 3)


def loudness_stats(p):
    out = subprocess.run(["ffmpeg", "-i", p, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    mean = re.search(r"mean_volume: ([-\d.]+)", out); mx = re.search(r"max_volume: ([-\d.]+)", out)
    return (float(mean.group(1)) if mean else None, float(mx.group(1)) if mx else None)


def mouth_series(p, fps=10):
    """inner-lip gap / face height per sampled frame, for the largest face"""
    import cv2, mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=FACE_MODEL), num_faces=3, running_mode=vision.RunningMode.IMAGE))
    cap = cv2.VideoCapture(p); src_fps = cap.get(cv2.CAP_PROP_FPS) or 24; step = max(1, round(src_fps / fps))
    vals, i, faces_seen = [], 0, 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        if i % step == 0:
            res = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)))
            if res.face_landmarks:
                faces_seen += 1
                f = max(res.face_landmarks, key=lambda L: abs(L[152].y - L[10].y))
                fh = abs(f[152].y - f[10].y) or 1e-6
                vals.append(abs(f[14].y - f[13].y) / fh)
            else:
                vals.append(None)
        i += 1
    cap.release(); lm.close()
    return vals, faces_seen


def mouth_metrics(p):
    vals, faces = mouth_series(p)
    v = np.array([x for x in vals if x is not None])
    if len(v) < 5: return {"faces_frames": faces, "mouth_activity": None}
    # activity = how much the lip gap moves (speech = rapid open/close)
    diffs = np.abs(np.diff(v))
    return {"faces_frames": int(faces), "sampled": len(vals),
            "mouth_open_mean": round(float(v.mean()), 4), "mouth_open_p90": round(float(np.percentile(v, 90)), 4),
            "mouth_activity": round(float(diffs.mean()), 4),
            "open_frac": round(float((v > 0.035).mean()), 3)}


def contact_sheet(p, n=8):
    d = duration(p); out = p.rsplit(".", 1)[0] + ".sheet.jpg"
    rate = n / d
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-vf",
                    f"fps={rate:.4f},scale=320:-2,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,tile={n//2}x2",
                    "-frames:v", "1", out])
    return out


# thresholds (calibrated on Veo 3.1 Fast 720p clips, Oct 2026):
#   real speech p90 0.11-0.12 | mumbling listener 0.08-0.10 | closed/pursed listener ~0.055
LISTENER_FAIL_P90, LISTENER_WARN_P90 = 0.07, 0.062
SPEAKER_MIN_ACTIVITY = 0.010
SIM_PASS, SIM_WARN = 0.62, 0.45


def check(mode, clip, expected=None):
    issues, m = [], {}
    m["duration"] = round(duration(clip), 2)
    mean_db, max_db = loudness_stats(clip); m["mean_db"], m["max_db"] = mean_db, max_db
    sheet = contact_sheet(clip)
    if mode in ("speaker", "listener"):
        m.update(mouth_metrics(clip))
        if not m.get("faces_frames"):
            issues.append(("fail", "no face detected"))
    if mode == "speaker":
        text, s0, s1 = transcribe(clip); m["transcript"], m["speech_start"], m["speech_end"] = text, s0, s1
        if expected:
            sim = similarity(text, expected); m["similarity"] = sim
            if sim < SIM_WARN: issues.append(("fail", f"dialogue does not match script (similarity {sim})"))
            elif sim < SIM_PASS: issues.append(("warn", f"dialogue partly off (similarity {sim}) - listen"))
        if s1 is not None and m["duration"] - s1 < 0.15: issues.append(("warn", "speech may be cut at the end"))
        if (m.get("mouth_activity") or 0) < SPEAKER_MIN_ACTIVITY: issues.append(("warn", "speaker lips barely move"))
        if max_db is not None and max_db > -0.5: issues.append(("warn", "audio clipping"))
        if mean_db is not None and mean_db < -35: issues.append(("fail", "voice too quiet / missing"))
    if mode == "listener":
        text, s0, s1 = transcribe(clip); m["transcript"] = text
        p90 = m.get("mouth_open_p90")
        if p90 is not None and p90 > LISTENER_FAIL_P90:
            issues.append(("fail", f"listener is lip-moving / talking (mouth p90 {p90}) -> run fix-listener or regenerate"))
        elif p90 is not None and p90 > LISTENER_WARN_P90:
            issues.append(("warn", f"listener mouth opens a bit (p90 {p90}) - check sheet"))
        if len(norm_hi(text)) > 6:
            issues.append(("warn", f"speech heard in listener clip: '{text[:60]}' (audio is muted in edit anyway)"))
    verdict = "fail" if any(s == "fail" for s, _ in issues) else "warn" if issues else "pass"
    return {"clip": clip, "mode": mode, "verdict": verdict, "issues": [i for _, i in issues], "metrics": m, "sheet": sheet}


def fix_listener(clip, out, min_len=4.0, max_len=7.0):
    """Auto-fix for a mumbling listener: find the window with the most-closed mouth and build a
    forward+reverse (ping-pong) loop from it. Reversed listening footage reads as natural micro-motion."""
    import cv2
    vals, _ = mouth_series(clip, fps=12)
    fps = cv2.VideoCapture(clip).get(5) or 24; dt = max(1, round(fps / 12)) / fps
    v = np.array([x if x is not None else 0.2 for x in vals]); n = len(v)
    best = None
    for L in range(int(min_len / dt), int(max_len / dt) + 1):
        for s in range(0, n - L + 1):
            w = v[s:s + L]; score = np.percentile(w, 90) + 0.3 * w.mean() - 0.002 * L * dt
            if best is None or score < best[0]: best = (score, s * dt, (s + L) * dt)
    _, a, b = best
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-filter_complex",
                    f"[0:v]trim={a:.2f}:{b:.2f},setpts=PTS-STARTPTS,split[f][r0];[r0]reverse[r];[f][r]concat=n=2:v=1:a=0[v]",
                    "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", out])
    r = check("listener", out)
    r["window"] = [round(a, 2), round(b, 2)]
    return r


def main():
    mode = sys.argv[1]
    if mode == "fix-listener":
        print(json.dumps(fix_listener(sys.argv[2], sys.argv[3]), ensure_ascii=False, indent=2)); return
    if mode == "batch":
        plan = json.load(open(sys.argv[2], encoding="utf-8")); base = os.path.dirname(os.path.abspath(sys.argv[2]))
        rep = [check(it["mode"], os.path.join(base, it["clip"]), it.get("expected")) for it in plan]
        out = os.path.join(base, "qa_report.json")
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=2)
        for r in rep: print(f"{r['verdict'].upper():5s} {os.path.basename(r['clip'])}: {'; '.join(r['issues']) or 'ok'}")
        print("report ->", out)
    else:
        print(json.dumps(check(mode, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
