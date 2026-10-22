# scenes.json — the edit spec

`python3 engine/assemble.py jobs/<job>/scenes.json` → `jobs/<job>/<output>` (1080×1920, 30fps, AAC, −14 LUFS).
All paths are relative to the scenes.json folder.

## Top level
| key | meaning |
|---|---|
| `output` | file name, e.g. `final_v1.mp4` |
| `captions` | default true |
| `caption_style` | `box` (dark pill) · `outline` (UGC white + black stroke) · `yellow` · `white` · `big` |
| `caption_words` | words per caption chunk when no `|` given (default 5) |
| `voice_fx` | dialogue clean-up chain, default true |
| `bgm`, `bgm_volume` | optional music bed (looped, default 0.12) |
| `css` | global CSS for every `html` layer (fonts available: `Mukta` 700/800 Devanagari+Latin, `Anton`) |
| `news`, `ticker`, `live_bug` | only for the `news` preset |

## Scene keys (every layout)
`duration` (else = audio length) · `audio` = `{"from": "<layer id | left | right | top | clip>"}` or `{"file": "x.mp4", "start": 0}`, plus `fx: false`, `volume` · `caption` (Devanagari; `|` splits chunks; `**x**` highlights) · `caption_y` · `caption_style` · `captions: false` · `fade_in`, `fade_out` (s) · `sfx: [{"file","at","volume"}]` · `bg` colour.

## Layouts
### `custom` — any format (preferred for new formats)
`layers` draw bottom→top:
| type | keys |
|---|---|
| `video` / `image` | `src` or `clips:[{clip,start,dur,zoom}]` (sequence), `rect`, `start`, `zoom` (stills push-in), `at`/`until` (visibility window), `id` (to take audio from it) |
| `html` | `html` (any markup), `css`, `rect` [x,y,w,h] = canvas size, `anim` `{in: fade|slide-up|slide-left, dur, blink, out_fade}`, `at`, `until` |
| `png` | `src` image file, `rect`, `anim`, `at`, `until` |
| `ticker` | `items`, `rect` [x,y,w,h], `speed`, `bg`, `style {color,size,dot,sep,bg}` |
| `box` | `rect`, `color` (`black@0.4`), `at`, `until` |
`rect` = `[x,y,w,h]` or a name: `full`, `top` (news top band), `bottom` (news B-roll band), `left`, `right`.
Common rects: top half `[0,0,1080,960]`, bottom half `[0,960,1080,960]`, PiP bottom-right `[640,1300,400,500]`, full-bleed `full`.

### `news` preset — TV debate
`left` / `right` (or `top`) clips, `bottom` B-roll list, `headline_top`, `headline_bottom`, names/roles (or global `news{}`), global `ticker`.

### `full` — clips full-screen in sequence
`clips: [{clip, start, dur, zoom}]` (.png/.jpg get a slow push-in).

### `endcard`
`image` (logo), `image_width`, `clip` (optional background), `cta` (`|` = line break), `bg`.

## Examples
`examples/news/scenes.json` (Rang news debate), `examples/ugc/scenes.json` (UGC hook sticker, split reaction, demo, endcard).
