# Avar Reel kit

Vertical 1080×1920 motion-graphics Reels, ~12 s at 128 BPM, cut on the beat:

| Shot | Time | Look | Copy (spec field) |
|---|---|---|---|
| 1 | 0–1.9 s | Signal Orange, queue of right-facing cars zips in and gets stuck, clock spinning | `pain` (2 short lines, slammed in on beats) |
| 2 | 1.9–2.8 s | Ink, white type | `turn` (e.g. "ואתם?") |
| 3 | 2.8–6.6 s | the animated vertical scene (AI clip), full bleed | `answer`, then `lines` (2 lines) |
| 4 | 6.6–8.4 s | Avar Green, Ink type, a checkmark draws on | `verdict` (2 lines) |
| 5 | 8.4–12 s | Mint end card: logo, `end` line, CTA pill pulsing on the beat, official badges, legal line | `end` |

Only shot 3 is AI-generated; all type, logo, badges, CTA and legal are rendered by the kit.

```bash
python3 pipeline/reel/render_reel.py clip.mp4 silent.mp4 --duration 12 --spec spec.json
python3 pipeline/reel/music.py music.wav 12          # synthesized, royalty-free 128 BPM bed
python3 pipeline/reel/mix.py silent.mp4 music.wav out.mp4 [vo1.wav@0.1 vo2.wav@1.9 ...]
python3 pipeline/reel/render_reel.py clip.mp4 x.mp4 --spec spec.json --preview 1.2,3.1,5.8,7.8,10   # stills for QA
```

`spec.json`: `{"pain":["הרכב","בתור"],"turn":"ואתם?","answer":"בים","lines":["היום שלכם","הטסט שלנו"],"verdict":["הטסט?","כבר עבר"],"end":"אתם בבית. הרכב עובר"}`

The clip is a 9:16 Kling animation of a vertical scene whose top ~35% is empty sky (room for type).
`voice.json` holds the brand voice settings once chosen.
