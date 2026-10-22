# LESSONS — read fully before every job. Never repeat a mistake listed here.

Each lesson: `- [area] rule — why (source, date)`. Add new ones with the `learn` skill. Never delete; if a lesson is superseded, mark it `(superseded by …)`.

## Generation (Flow / Veo)
- [veo-audio] Describe sound positively ("soft ambient studio sound"). Never write "no speech / no music / silence" — causes "Audio generation failed". (QA, 2026-10-22)
- [veo-listener] Veo lip-syncs silent listeners to its own audio even when told "mouth closed". Always request 2 takes, run `qa.py listener`, then `qa.py fix-listener`; fallback = character still as a `.png` panel. Reuse `assets/library/anchor_listen_loop.mp4` for news anchors. (client feedback "anchor lipsing kar raha hai", 2026-10-22)
- [veo-dialogue] ≤16 Hindi words per 8s clip, Devanagari in quotes. Longer lines get rushed or cut. (QA, 2026-10-22)
- [veo-voice] Veo 3.1 Fast Hindi voice sounds thin; engine `voice_fx` helps. For hero lines offer Veo 3.1 Quality. Prompt "deep, resonant, clear broadcast voice, close microphone". (client feedback "voice thoda bura hai", 2026-10-22)
- [flow-ui] Download: tile ⋮ → find "Download" → find "720p Original size". Dismiss the download toast before the next tile; it covers the top-right ⋮. (2026-10-22)
- [flow-ui] Identify downloaded clips by transcript / contact sheet, never by download order. (2026-10-22)

## Edit
- [timing] Set speaker scene `duration` = Whisper `speech_end` + 0.3–0.5s so scenes end on the last word. (2026-10-22)
- [demo] Demo must show the real product (recording or official Play Store screenshots), never AI-generated UI. B-roll phones: "screen not visible to camera". (2026-10-22)
- [panels] Veo watermark sparkle sits bottom-right of 16:9 frames — center-crop panels so it is cut off; check sheets. (2026-10-22)

## Script / policy
- [claims] No guaranteed outcomes (money, house, job, cure, marks). Use emotional/relational benefits. (Crafto reference review, 2026-10-22)
- [brand] Invent channel/anchor/expert names; never real channels, logos or people. (2026-10-22)
