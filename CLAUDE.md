# Ad Studio — operating manual for Claude

This repo turns a brief (reference ad + rough script + product) into a finished 9:16 video ad of ANY format.
Generation runs on the operator's Google AI subscription in Google Flow (Veo 3.1, Nano Banana) via Claude in Chrome;
planning, QA, fixing and editing run here.

## Non-negotiables
1. **Read `LESSONS.md` in full before starting or revising any job.** Every rule there exists because a mistake already happened. Re-check the plan against it before generating, and the output against it before delivering.
2. **Every piece of feedback becomes a lesson** (`learn` skill) — client comments, operator comments, and every QA failure you had to fix. Generalise it ("listener characters lip-sync → …"), not "job 3 anchor bad".
3. **QA every generated asset** (`engine/qa.py`) and look at every contact sheet yourself. Fix failures before anyone sees them (see `make-ad` skill fix table). Only show the client things that passed.
4. Freedom over templates: pick or invent the format that fits the reference/brief (`docs/formats.md`); build with the `custom` layer layout (`docs/scene-spec.md`) whenever presets don't fit. Write custom HTML graphics per ad.
5. Talk to the operator in Hinglish, short and structured. Never type passwords; the operator signs in to Flow.

## Map
| path | what |
|---|---|
| `engine/assemble.py` | scenes.json → MP4 (layers, presets, captions, voice FX, loudness) |
| `engine/qa.py` | clip QA: `speaker` / `listener` / `broll` / `batch` / `fix-listener` |
| `engine/analyze_ref.py` | reference ad → shot cuts, frame grids, transcript |
| `templates/layers.html` | HTML renderer for overlays, captions, tickers, custom graphics |
| `assets/library/` | reusable QA-passed assets (silent news anchor loop + still) — reuse before generating |
| `docs/` | `formats.md`, `scene-spec.md`, `prompt-library.md`, `flow-playbook.md` |
| `jobs/<job-id>/` | one folder per ad: `brief.json`, `plan.md`, `gen.json`, `clips/`, `qa_plan.json`, `qa_report.json`, `scenes.json`, `final_vN.mp4`, `feedback.md` |
| `studio/` | client-facing Studio page source (`studio.html`) + `config.json` (one Studio URL per client) |
| `examples/` | `news/` and `ugc/` scenes.json references |

## Skills
- `make-ad` — the full job: brief → plan → generate → QA/fix → assemble → deliver.
- `studio-sync` — pull new jobs/feedback from the client Studio page, push previews/finals/status back.
- `learn` — turn feedback or a fixed failure into a `LESSONS.md` rule (and the Studio's Learnings list).

## First run in a workspace
`bash setup.sh` (ffmpeg, faster-whisper, mediapipe, playwright). Whisper model downloads on first QA.
