# Avar render kit

Turns copy plus a text-free scene into on-brand ad PNGs in three formats:
1:1 (1080×1080), 4:5 (1080×1350) and 9:16 (1080×1920, with Stories/Reels safe zones), all rendered at 2×.

The image model never draws text, logos or badges. Hebrew copy is set in Rubik, and the real logo and
official store badges are composited from `assets/`. That is what keeps every creative on-brand.

## Run

```bash
pip install playwright numpy pillow   # Chromium must be available to Playwright
python3 pipeline/render.py spec.json --out out/
```

Exit codes: `0` ok · `2` copy or spec problem (fix the copy) · `3` brand assets missing.

## Spec

Scene layout (text top-right, scene band, one CTA unit):

```json
{"id": "avar-rechev-bator-yam", "layout": "scene",
 "hook": ["הרכב בתור", "אתם בים"], "context": "היום שלכם. הטסט שלנו", "details": "הטסט? כבר עבר",
 "scene": "scene.png"}
```

Split layout (two-color billboard, no scene, zero credits):

```json
{"id": "avar-billboard-hatest-hachi-tov", "layout": "split", "top_color": "orange",
 "top": ["הטסט הכי טוב"], "bottom": ["הוא זה שלא", "הייתם בו"], "context": "היום שלכם. הטסט שלנו"}
```

Optional: `"legal"` overrides the default legal line (e.g. to add offer terms), and `"facts_confirmed": true`
is required before any ₪ amount can appear — prices come from Muhanad only.

## What the renderer enforces

- Copy lint: no period at the end of headlines or sublines, no service verbs (אוספים / מחזירים) in headlines,
  no pass guarantees, no authority or rating claims, no unfilled placeholders, no unconfirmed prices
- Exactly three type levels: hook ≥ 3× context, details smaller than context
- One CTA unit: Avar Green pill with Ink text (Ink pill with white text on green backgrounds), Google Play left,
  App Store right, legal line
- Type shrinks until everything fits; a headline that only fits below the minimum size is rejected
- Scene background is made transparent and cropped to the drawing, so any off-white melts into the canvas

## Assets

Put these in `assets/` (the renderer refuses to run without them):

- `logo.svg` or `logo.png` — the real logo file, transparent corners
- `badge-appstore.svg|png` — official Apple "Download on the App Store" badge, unmodified
- `badge-googleplay.svg|png` — official "Get it on Google Play" badge, unmodified

`--allow-missing` draws a labeled placeholder box for a missing logo or badge, and `--standins DIR` uses stand-in art.
Both stamp the render PREVIEW. Use them only for concept review; never upload or publish a PREVIEW render.
