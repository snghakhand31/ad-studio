#!/usr/bin/env python3
"""
Break down a reference ad so it can be cloned.
  python3 analyze_ref.py <reference.mp4> <out_dir>
Writes:
  out_dir/ref_grid_XX.jpg   frame grids (1 frame / 2s, 4x3 per sheet) for visual reading
  out_dir/ref_cuts.jpg      one frame per detected shot
  out_dir/ref.json          duration, size, shot cuts (s), timed transcript
"""
import json, os, re, subprocess, sys
import numpy as np


def main(ref, out):
    os.makedirs(out, exist_ok=True)
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,codec_type",
                                    "-of", "json", ref], capture_output=True, text=True).stdout)
    dur = float(pr["format"]["duration"])
    vs = [s for s in pr["streams"] if s.get("codec_type") == "video"][0]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", ref, "-vf", "fps=1/2,scale=300:-2,tile=4x3", os.path.join(out, "ref_grid_%02d.jpg")])
    # shot cuts
    log = subprocess.run(["ffmpeg", "-i", ref, "-vf", "select='gt(scene,0.32)',showinfo", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    cuts = [round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", log)]
    sel = "+".join([f"eq(n\\,{int(c*30)+3})" for c in [0.0] + cuts][:16]) or "eq(n\\,3)"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", ref, "-vf", f"select='{sel}',scale=240:-2,tile=8x2", "-vsync", "0",
                    "-frames:v", "1", os.path.join(out, "ref_cuts.jpg")])
    # transcript
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", ref, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    segs = []
    if raw:
        from faster_whisper import WhisperModel
        a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        m = WhisperModel(os.environ.get("QA_WHISPER", "small"), device="cpu", compute_type="int8")
        s, info = m.transcribe(a, vad_filter=True)
        segs = [{"start": round(x.start, 2), "end": round(x.end, 2), "text": x.text.strip()} for x in s]
    res = {"duration": round(dur, 2), "width": vs["width"], "height": vs["height"], "cuts": cuts, "transcript": segs}
    json.dump(res, open(os.path.join(out, "ref.json"), "w"), ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
