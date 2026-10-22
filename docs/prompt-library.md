# Prompt library + script rules

## Beat structure (24–32s)
| Beat | Length | Layout | Content |
|---|---|---|---|
| HOOK | 5–8s | `news` | The shock line, on camera, by the expert, with a prop/gesture ("…to yahin live TV pe ye phone tod dunga!"). Anchor reacts silently. |
| PROMISE | 7–9s | `news` | Payoff / urgency (festival, date, emotion). Bottom panel = aspirational B-roll. |
| DEMO | 7–10s | `full` | Real product: phone recording or store screenshots (slow push-in). Expert's voice as VO (use the audio of a Veo clip). |
| CTA | 2–3s | `endcard` | Icon/logo + "<App> download करें" + tagline. |

Other formats from a reference: UGC/testimonial → `full` layout with 9:16 Veo talking-head clips + captions; demo-led → `full` with recordings + VO clip audio.

## Writing rules
- ≤16 Hindi words per 8s Veo line (18 absolute max). Write dialogue in Devanagari inside quotes.
- Headlines: top ≤38 chars (question works: "क्या…?"), bottom ≤28 chars.
- Captions: Devanagari, chunk with `|`, one `**highlight**` per chunk.
- Invent names: channel "K360 NEWS", anchor "राहुल मेहता · एंकर", expert "<पं./डॉ./साध्वी> <name> · <role>".
- Claims: emotional/relational outcomes only. Never: guaranteed money, house, job, cure, marks. Superstition is fine as opinion, not as a guarantee.

## Character stills (Nano Banana, 16:9)
```
Photorealistic still from an Indian Hindi TV news debate. <CHARACTER>. Sits in a news studio with a deep red
curtain backdrop and soft studio lighting, <prop/gesture>, <expression>. Medium close-up, broadcast camera look,
sharp focus, natural skin texture. No text, no logos, no captions, no watermarks.
```
Expert examples: "Indian Hindu pandit in his late 50s, grey stubble, long red-saffron tilak, saffron kurta, rudraksha mala, Ram-naam stole, holding up a smartphone" · "Indian career coach in her 30s, blazer, confident" · "senior Indian CA in his 50s, white shirt, spectacles".

## Speaker clip (i2v from the still, 16:9, 8s)
```
From the <character> image (first frame). The same <character> speaks loudly and passionately in Hindi directly to
camera in an Indian TV news debate studio, <action: raises the phone high and shakes it>, static broadcast camera,
clear <male/female> Hindi voice with natural lip sync, studio ambience. He says: "<Devanagari line>"
```
Better voice: add "deep, resonant, clear broadcast voice, close microphone"; for hero lines consider Veo 3.1 Quality.

## Listener clip (i2v, 16:9, 8s, request 2 takes)
```
Use the <anchor> still as the first frame. He is LISTENING silently to a loud guest off-screen. His mouth stays firmly
closed the entire time, lips pressed together, jaw completely still. He reacts only with his eyes and eyebrows: a
skeptical frown, one raised eyebrow, a slow small head tilt, one blink, a slow disbelieving head shake at the end.
Static locked-off broadcast camera. Soft ambient TV studio sound.
```
Always QA (`listener`) and expect to need `fix-listener`.

## B-roll (t2v, 16:9, 8s)
```
Handheld cinematic shot of <scene>, <details>, warm natural light, realistic. Sound of <positive ambience>. No text on screen.
```
Phones in B-roll: "the phone screen is not visible to the camera" (avoids fake UI).

## Audio phrasing
Describe what IS heard ("soft ambient studio sound", "festive chatter"). Never "no speech / no music / silence" → causes "Audio generation failed".
