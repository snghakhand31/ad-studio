# Ad Studio (Claude Code)

Brief in → finished 9:16 video ad out, any format. Clients send briefs and review in a shared **Studio** page; Claude Code plans, generates (Google Flow: Veo 3.1 + Nano Banana, on your Gemini subscription, via Claude in Chrome), QA-checks, fixes, edits and delivers. Every piece of feedback becomes a permanent rule in `LESSONS.md`.

## Try it on any laptop (2 minutes)
1. Install the **Claude desktop app**, sign in, open **Claude Code**, and in Chrome add the **Claude in Chrome** extension.
2. In Claude Code, say:
   > Clone https://github.com/snghakhand31/ad-studio, open it, and run setup.sh
3. Sign in to **flow.google.com** in Chrome with a Google AI Pro/Ultra account.
4. Attach a reference ad and say:
   > Is reference jaisa ad banao. App: <Play Store link>. Script: <your script>

Claude reads `CLAUDE.md` + `LESSONS.md`, plans the ad, generates clips in Flow, checks and fixes them, and hands you the MP4.

## Setup (once)
1. Open this folder in Claude Code (desktop app or claude.ai/code with your computer linked). `bash setup.sh`.
2. Chrome with the Claude extension connected; sign in to flow.google.com with your Google AI Pro/Ultra account.
3. Share the Studio page with your client: Share → invite their email as **Editor** (Editors can send briefs, upload files and review; keep it off public links). One Studio per client — see `studio/config.json`.

## Daily use
- Client sends a brief in the Studio (script + reference video + product link).
- You tell Claude Code: **"studio sync karo"** → it plans, posts the plan/clips for review (or goes straight to the final in auto mode), applies feedback, and posts the final.
- Or skip the Studio: **"is reference jaisa ad banao <app> ke liye, script: …"** (attach the reference).
- Feedback in chat works too: "anchor bol raha hai, mat bulwao" → fixed + saved as a lesson.

## What's inside
`CLAUDE.md` (operating manual) · `LESSONS.md` (never-repeat rules) · `engine/` (assemble, QA, reference analysis) · `templates/` (overlay renderer + fonts) · `assets/library/` (reusable QA-passed clips) · `docs/` (formats, scene spec, prompt library, Flow playbook) · `.claude/skills/` (make-ad, studio-sync, learn) · `studio/` (client page source) · `examples/` (news + UGC scene files).

## Costs
Veo 3.1 Fast = 20 Flow credits per 8 s clip; a 25–30 s ad ≈ 80–120 credits (reused library clips cost 0). Edit-only revisions (text, timing, captions, order, music) cost 0.
