---
name: make-ad
description: Produces a finished 9:16 video ad of any format from a reference ad, a rough script and a product, generating clips in Google Flow via Claude in Chrome, auto-QA-ing and fixing them, then assembling with the repo engine. Use for "is jaisa ad banao", "make an ad for <app>", "script se video banao", or when processing a Studio job.
---

# make-ad

Work inside `jobs/<job-id>/` (id = short slug + date). Read `LESSONS.md` first — fully.

## 1. Brief
Collect into `brief.json`: product (name, Play Store/website link, tagline, what to show), script (as given), reference video path, format wishes, review mode (`auto` | `review`), language/voice notes, client constraints. Ask only for what is missing and blocking (one AskUserQuestion). Studio jobs already carry these.

## 2. Understand
- Reference: `python3 engine/analyze_ref.py <ref> jobs/<id>/ref` → read grids, `ref_cuts.jpg`, `ref.json`. Note format, beat timing, hook mechanics, text style, voice style, pacing (cuts/sec).
- Product: WebFetch the store page; pull screenshots + icon (`play-lh.googleusercontent.com/<id>=w1080-h1920`, ids via javascript_tool on the store page). Real product footage only.

## 3. Plan (`plan.md`, `gen.json`, `scenes.json` draft)
- Choose/invent the format (`docs/formats.md`). Rewrite the script into beats obeying `docs/prompt-library.md` + LESSONS (word limits, claims, names).
- `gen.json`: every image/clip: id, tool (image | i2v | t2v), aspect (16:9 panels, 9:16 full-bleed), exact prompt, QA mode (`speaker` + expected line | `listener` | `broll`), takes.
- Reuse `assets/library/` where it fits. Estimate credits (Veo 3.1 Fast = 20 / 8s clip).
- Draft `scenes.json` (`docs/scene-spec.md`); write custom `html` layers for this ad's graphics.
- Review mode: post the beat table (Studio item `plan`) and wait for approval. Auto mode: continue.

## 4. Generate (`docs/flow-playbook.md`)
Characters first (Nano Banana) → read each image (photoreal, right look, no text/logos, normal hands) → regenerate once if off → then all Veo clips in 1–2 agent messages; approve the credit card. Work on graphics/scenes while clips render. Download 720p, stage from Downloads, rename to gen.json ids (identify by transcript/sheet).

## 5. QA + fix loop (mandatory)
`qa_plan.json` from gen.json → `python3 engine/qa.py batch jobs/<id>/qa_plan.json` → read every `*.sheet.jpg`.
| Issue | Fix (max 2 regenerations, then fallback) |
|---|---|
| listener lip-moving | `qa.py fix-listener in out` → else regenerate 2 takes (listener prompt) → else still `.png` panel |
| dialogue mismatch / cut | shorten to ≤16 words, Devanagari, regenerate |
| audio failed / quiet | positive audio phrasing, regenerate |
| visual defect on sheet | regenerate naming the defect as a constraint |
| similarity 0.45–0.62 | Whisper is weak on Hindi: accept if key words present |
Every fix you had to make → `learn` skill (generalised rule). Set speaker scene durations from `speech_end` + 0.3–0.5s.
Review mode: publish passed images/clip sheets as Studio items and wait.

## 6. Assemble + check
`python3 engine/assemble.py jobs/<id>/scenes.json`. Then read a 6-frame strip (overlay alignment, captions not on faces/UI, no black frames), check loudness ≈ −14 LUFS and duration. Re-check against LESSONS. Name outputs `final_v1.mp4`, `final_v2.mp4`…

## 7. Deliver
Studio job → `studio-sync` push. Local → SendUserFile + copy to the operator's Downloads. Report ≤6 lines: what was made, credits used, fallbacks used, lessons added, one next step (e.g. hook variants: change first scene/headlines/captions only — zero credits).

## Revisions
Read all feedback (Studio items + chat). Map each comment to: plan change | regenerate specific clip | edit-only change (text, timing, captions, order, graphics, music). Prefer edit-only fixes (free). Write every comment as a lesson first, then fix, then re-QA, re-render as next version.
