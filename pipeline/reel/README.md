# Avar Reel kit

Vertical 1080×1920 motion-graphics Reels, 12 s, music + sound effects, no voiceover. Four formats, so the
four weekly Reels never feel like copies of each other. Each week uses each format once.

| Template | Story | Shots | AI clip | Music (suggested) |
|---|---|---|---|---|
| `queue` | Car / You: the car is stuck in line, you are living | orange queue → Ink "turn" → scene → green verdict + checkmark → end card | yes (shot 3) | `--bpm 128 --drop 2.81` |
| `day` | The stolen day: a clock races 08:00→16:30 while a bar fills with queue chips, then rewinds | orange clock + day bar → Ink rewind → scene → end card | yes (shot 3) | `--bpm 120 --drop 5.5` |
| `app` | Watch it happen: tap "הזמינו טסט", the status timeline lights step by step, a push lands | mint + phone (one continuous shot) → end card | none (0 credits) | `--bpm 124 --drop 0.55` |
| `list` | What you didn't do today: three chores slam in and get struck out in orange | white checklist → scene + verdict + check badge → end card | yes (shot 2) | `--bpm 112 --drop 5.36` |

Use a different `--key` and `--seed` for every Reel so no two tracks repeat.

Spec fields per template:
- `queue`: `{"pain":[2 lines],"turn","answer","lines":[2],"verdict":[2],"end"}`
- `day`: `{"kicker","chips":[5 short],"big","turn","answer","line","end"}`
- `app`: `{"headline":[2],"button","steps":[5],"notif","verdict","end"}` (steps are the app's real status labels)
- `list`: `{"kicker","items":[3],"turn","verdict":[2],"end"}`

```bash
python3 pipeline/reel/render_reel.py clip.mp4 silent.mp4 --template day --duration 12 --spec spec.json   # writes silent.mp4.cues.json
python3 pipeline/reel/music.py music.wav 12 --bpm 120 --drop 5.5 --key 2 --seed 3
python3 pipeline/reel/sfx.py sfx.wav 12 --events silent.mp4.cues.json      # queue template: omit --events
python3 pipeline/reel/mix.py silent.mp4 music.wav out.mp4 --sfx sfx.wav
python3 pipeline/reel/render_reel.py clip.mp4 x.mp4 --template day --spec spec.json --preview 0.5,2.5,4.9,6.5,10.5   # stills for QA
```
For `app` pass any PNG as the clip (it isn't used).

## queue template details

Only shot 3 is AI-generated; all type, logo, badges, CTA and legal are rendered by the kit.



`spec.json`: `{"pain":["הרכב","בתור"],"turn":"ואתם?","answer":"בים","lines":["היום שלכם","הטסט שלנו"],"verdict":["הטסט?","כבר עבר"],"end":"אתם בבית. הרכב עובר"}`

The clip is a 9:16 Kling animation of a vertical scene whose top ~35% is empty sky (room for type).
No voiceover: Reels run on music + sound effects (see `voice.json`).

Sonic kit (`sfx.py`): slam on every word, zip when the queue arrives, two short honks while it's stuck,
whoosh on every cut, a sea/air wash when the day comes back, a rising swish while the checkmark draws,
and the Avar "passed" chime (two notes up, E6→B6) when the check lands and when the logo pops.
If you change shot timings in `templates/queue.html`, change the `S` list in `sfx.py` to match. The other templates send their own sound cues (`cue()` in the template) to `sfx.py --events`.
