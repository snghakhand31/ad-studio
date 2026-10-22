# Google Flow playbook (Claude in Chrome)

Tested on flow.google.com, Oct 2026 (PRO plan). The UI changes often: screenshot before clicking by coordinates and prefer `find` + `ref` clicks.

## Facts
- Flow is an agent chat inside a project. Left nav: All media / Images / Videos / Characters / Scenes.
- Costs: Veo 3.1 Fast = 20 credits per 8s clip. Nano Banana images are cheap. PRO plan gets +50 credits daily. Failed generations are refunded.
- Agent settings (sliders icon next to the prompt box): set Image default 16:9 ×1, Video default 16:9 ×1, model **Veo 3.1 - Fast**. Keep "Confirm before generating: Always" — approve each batch in chat (the card shows the credit cost; tell the user the total).
- Video models available: Omni 1.1 Flash, Veo 3.1 Lite / Fast / Quality. Use Fast by default; Quality only for hero dialogue if the user wants better voice and has credits.

## Start
1. `tabs_context_mcp` → `tabs_create_mcp` → navigate `https://labs.google/fx/tools/flow`. If redirected to accounts.google.com, ask the user to sign in and wait.
2. Click "New project" (or reuse the project the user names). Dismiss changelog popups ("Get started", "Got it").

## Prompting the agent
- Click the prompt box (find "What do you want to create?"), type, press Return. If Return does not send (agent busy), click the arrow button.
- One message can request several outputs: "Make 3 separate videos from the pandit image… Video 1: … Video 2: …". The agent replies with a confirmation card → click **Approve** (find "Approve").
- Refer to earlier images by description ("the existing still image of the Indian news anchor in a navy suit… from this project") — the agent resolves it.
- Generation takes 1–3 min per batch ("queued due to high demand" is normal). Poll with browser_batch waits + a 0.6-scale screenshot; don't burn turns on single waits.

## Downloading (720p is enough; panels are ≤1080 px wide)
1. Click **Videos** in the left nav; close the agent panel (X) so tiles are wide.
2. Hover a tile → click its ⋮ ("More") at the tile's top-right → `find` "Download menuitem in open menu" → click it → `find` "720p Original size menu item" → click. (Wait 1s between steps; menus render late.)
3. If the click opens the clip editor instead, use the download icon in the editor's top bar → 720p.
4. Dismiss the "Your video has been downloaded" toast before clicking the next tile's ⋮ (it covers the top-right tile).
5. Files land in `~/Downloads` named from the agent's title, e.g. `Man_speaking_on_television_debate_20261022161624.mp4`. List the folder (output is big: parse the saved JSON, sort by mtimeMs) and stage the newest N. Identify which clip is which by transcript (speakers) or contact sheet (b-roll), not by order.

## Known failures
- "Audio generation failed" → negative audio phrasing ("no speech, room tone only"). Rephrase positively and retry (refund is automatic).
- Listener characters mouth words even when told not to (Veo lip-syncs to its own generated audio). Ask for 2 takes, run QA, use `qa.py fix-listener`, or use the still fallback.
