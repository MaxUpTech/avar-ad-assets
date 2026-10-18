#!/usr/bin/env python3
"""Avar ad renderer: copy + a text-free scene -> on-brand ad PNGs.

Formats: 1x1 (1080x1080), 4x5 (1080x1350), 9x16 (1080x1920), rendered at 2x.
The image model never draws text, logos or badges. Hebrew copy is set in Rubik,
and the real logo + official store badges are composited from pipeline/assets/.

Usage:
  python3 render.py SPEC.json --out OUT_DIR [--formats 1x1,4x5,9x16] [--standins DIR]

Exit codes: 0 ok · 2 copy/spec problem (fix the copy) · 3 brand assets missing.
"""
import argparse
import json
import pathlib
import re
import sys
import tempfile

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

KIT = pathlib.Path(__file__).resolve().parent
FORMATS = {"1x1": 1080, "4x5": 1350, "9x16": 1920}
LEGAL = "*השירות זמין ברחובות והסביבה בלבד. בכפוף לתנאי השירות."
ASSET_NAMES = {
    "logo": ["logo.svg", "logo.png"],
    "appstore": ["badge-appstore.svg", "badge-appstore.png"],
    "googleplay": ["badge-googleplay.svg", "badge-googleplay.png"],
}

# --- copy lint: the deterministic half of Brand QA -------------------------
SERVICE_VERBS = ["אוספים", "מחזירים", "נאסוף", "נחזיר"]          # never in a headline
BANNED = {                                                        # never anywhere
    "pass guarantee": ["מובטח", "מבטיחים", "בטוח עובר", "עובר בטוח", "100%", "תמיד עובר"],
    "authority implied": ["משרד התחבורה", "משרד הרישוי"],
    "ratings/reviews": ["★", "כוכבים", "דירוג"],
}


def lint(spec):
    errors = []
    lines = spec.get("hook", []) + spec.get("top", []) + spec.get("bottom", [])
    body = [spec.get("context", ""), spec.get("details", "")]
    everything = " ".join(lines + body)
    for line in lines:
        if line.rstrip().endswith("."):
            errors.append(f"headline line ends with a period: {line!r}")
        for v in SERVICE_VERBS:
            if v in line:
                errors.append(f"service verb {v!r} in headline: {line!r}")
    for b in body:
        if b and b.rstrip().endswith("."):
            errors.append(f"subline ends with a period: {b!r}")
    for why, words in BANNED.items():
        for w in words:
            if w in everything:
                errors.append(f"{why}: {w!r}")
    if "___" in everything or "₪___" in everything:
        errors.append("unfilled placeholder (___) — needs a real fact from Muhanad")
    if re.search(r"₪\s?\d|\d\s?₪", everything) and not spec.get("facts_confirmed"):
        errors.append("price in copy without facts_confirmed=true (prices come from Muhanad only)")
    if not (lines and any(l.strip() for l in lines)):
        errors.append("no headline")
    return errors


# --- assets ------------------------------------------------------------------
PLACEHOLDER_SVG = {
    "logo": '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300"><rect width="300" height="300" rx="66" fill="#55D8CB"/><text x="150" y="170" font-family="sans-serif" font-size="44" text-anchor="middle" fill="#222">LOGO</text></svg>',
    "appstore": '<svg xmlns="http://www.w3.org/2000/svg" width="250" height="83"><rect x="1" y="1" width="248" height="81" rx="13" fill="#fff" stroke="#999" stroke-dasharray="6 4" stroke-width="2"/><text x="125" y="50" font-family="sans-serif" font-size="20" text-anchor="middle" fill="#666">App Store badge</text></svg>',
    "googleplay": '<svg xmlns="http://www.w3.org/2000/svg" width="250" height="83"><rect x="1" y="1" width="248" height="81" rx="13" fill="#fff" stroke="#999" stroke-dasharray="6 4" stroke-width="2"/><text x="125" y="50" font-family="sans-serif" font-size="20" text-anchor="middle" fill="#666">Google Play badge</text></svg>',
}


def find_assets(standins, allow_missing=False, tmp=None):
    found, missing = {}, []
    for key, names in ASSET_NAMES.items():
        hit = next((KIT / "assets" / n for n in names if (KIT / "assets" / n).exists()), None)
        if hit is None and standins:
            hit = next((pathlib.Path(standins) / n for n in names if (pathlib.Path(standins) / n).exists()), None)
            if hit is not None:
                found.setdefault("_standins", []).append(key)
        if hit is None and allow_missing and tmp is not None:
            hit = tmp / f"placeholder-{key}.svg"            # labeled box, never fake brand art
            hit.write_text(PLACEHOLDER_SVG[key], encoding="utf-8")
            found.setdefault("_standins", []).append(key)
        if hit is None:
            missing.append(key)
        else:
            found[key] = hit
    return found, missing


def trim_png(src, dst):
    """Official PNG badges ship with transparent padding; trim it so heights match."""
    im = Image.open(src).convert("RGBA")          # official PNGs may be palette-mode with transparency
    box = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if box:
        im = im.crop(box)
    im.save(dst)
    return dst


def prep_scene(src, dst):
    """Make the scene's paper background transparent and crop to the drawing,
    so it melts into the canvas whatever off-white the model chose."""
    rgb = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    h, w, _ = rgb.shape
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, axis=0)
    dist = np.sqrt(((rgb - bg) ** 2).sum(-1))
    alpha = np.clip((dist - 5.0) / 9.0, 0, 1)
    f = max(1, int(0.025 * min(h, w)))                      # feather the outer edge
    ry = np.clip(np.minimum(np.arange(h), np.arange(h)[::-1]) / f, 0, 1)
    rx = np.clip(np.minimum(np.arange(w), np.arange(w)[::-1]) / f, 0, 1)
    alpha *= np.minimum.outer(ry, rx)
    ys, xs = np.where(alpha > 0.08)
    if len(xs) == 0:
        raise SystemExit("scene is blank")
    pad = int(0.02 * min(h, w))
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(w, xs.max() + pad), min(h, ys.max() + pad))
    rgba = np.dstack([rgb, alpha * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").crop(box).save(dst)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--formats", default="1x1,4x5,9x16")
    ap.add_argument("--standins", help="preview only: folder with stand-in logo/badges; renders get a PREVIEW tag")
    ap.add_argument("--allow-missing", action="store_true",
                    help="preview only: draw a labeled placeholder for a missing logo/badge; renders get a PREVIEW tag")
    a = ap.parse_args()

    spec_path = pathlib.Path(a.spec).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    errors = lint(spec)
    if errors:
        print(json.dumps({"ok": False, "stage": "lint", "errors": errors}, ensure_ascii=False, indent=1))
        sys.exit(2)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="avar-render-"))
    assets, missing = find_assets(a.standins, a.allow_missing, tmp)
    if missing:
        print(json.dumps({"ok": False, "stage": "assets", "missing": missing,
                          "fix": "put the real logo and official badges in pipeline/assets/"}, ensure_ascii=False))
        sys.exit(3)

    out = pathlib.Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    page_assets = {}
    for key in ("logo", "appstore", "googleplay"):
        p = assets[key]
        if p.suffix.lower() == ".png" and key != "logo":
            p = trim_png(p, tmp / p.name)
        page_assets[key] = p.as_uri()

    layout = spec.get("layout", "scene")
    scene_uri = None
    if layout == "scene":
        if not spec.get("scene"):
            print(json.dumps({"ok": False, "stage": "spec", "errors": ["scene layout needs a scene image"]}))
            sys.exit(2)
        scene_src = (spec_path.parent / spec["scene"]).resolve()
        scene_uri = prep_scene(scene_src, tmp / "scene.png").as_uri()

    report = {"ok": True, "id": spec["id"], "files": [], "warnings": []}
    standin_keys = assets.get("_standins")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for fmt in [f.strip() for f in a.formats.split(",") if f.strip()]:
            page_spec = {
                "format": fmt, "layout": layout,
                "hook": spec.get("hook", []), "context": spec.get("context", ""), "details": spec.get("details", ""),
                "top": spec.get("top", []), "bottom": spec.get("bottom", []), "top_color": spec.get("top_color", "orange"),
                "cta": "הורידו את עבר", "legal": spec.get("legal", LEGAL),
                "scene": scene_uri, "assets": page_assets,
                "preview_tag": ("PREVIEW · stand-in " + ", ".join(standin_keys)) if standin_keys else None,
            }
            page = browser.new_page(viewport={"width": 1080, "height": FORMATS[fmt]}, device_scale_factor=2)
            page.add_init_script(f"window.__SPEC__ = {json.dumps(page_spec, ensure_ascii=False)};")
            page.goto((KIT / "template.html").as_uri())
            page.wait_for_function("window.__RESULT__ !== undefined", timeout=30000)
            res = page.evaluate("window.__RESULT__")
            if not res.get("ok"):
                print(json.dumps({"ok": False, "stage": "layout", "format": fmt, "error": res.get("error")}, ensure_ascii=False))
                sys.exit(2)
            dst = out / f"{spec['id']}-{fmt}.png"
            page.locator(".canvas").screenshot(path=str(dst))
            page.close()
            report["files"].append(str(dst))
            report["warnings"] += [f"{fmt}: {w}" for w in res.get("warnings", [])]
            report.setdefault("sizes", {})[fmt] = res.get("sizes")
        browser.close()
    if standin_keys:
        report["warnings"].append("PREVIEW ONLY — stand-in " + ", ".join(standin_keys) + "; not for publishing")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
