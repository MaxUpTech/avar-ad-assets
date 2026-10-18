#!/usr/bin/env python3
"""Render reel.html (vertical 1080x1920 motion-graphics Reel) frame by frame (window.seek(t)) and encode a 1080x1920 H.264 MP4.
usage: render_reel.py CLIP.mp4|STILL.png OUT.mp4 [--duration 13] [--preview t1,t2,...]"""
import argparse, asyncio, glob, os, shutil, subprocess
from playwright.async_api import async_playwright

KIT = os.path.dirname(os.path.abspath(__file__))
HERE = os.path.join(KIT, "build")  # scratch: assets, frames, clip frames (gitignored)
os.makedirs(HERE, exist_ok=True)
def _prep():
    from PIL import Image
    shutil.copy(os.path.join(KIT, "reel.html"), HERE)
    fonts = os.path.join(HERE, "fonts")
    if not os.path.exists(fonts): shutil.copytree(os.path.join(KIT, "..", "fonts"), fonts)
    css = open(os.path.join(KIT, "..", "template.html"), encoding="utf-8").read()
    open(os.path.join(HERE, "fonts.css"), "w", encoding="utf-8").write("\n".join(l for l in css.splitlines() if l.startswith("@font-face")))
    A = os.path.join(KIT, "..", "assets")
    shutil.copy(os.path.join(A, "logo.png"), HERE)
    for b in ["badge-appstore", "badge-googleplay"]:
        im = Image.open(os.path.join(A, b + ".png")).convert("RGBA")
        im.crop(im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()).save(os.path.join(HERE, b + ".png"))
_prep()
ap = argparse.ArgumentParser()
ap.add_argument("clip"); ap.add_argument("out")
ap.add_argument("--duration", type=float, default=13.0)
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--preview", default="")
ap.add_argument("--spec", default="")
a = ap.parse_args()

cf = os.path.join(HERE, "clipframes")
shutil.rmtree(cf, ignore_errors=True); os.makedirs(cf)
if a.clip.endswith(".png"):
    shutil.copy(a.clip, os.path.join(cf, "0001.png"))
else:
    subprocess.check_call(["ffmpeg", "-v", "error", "-i", a.clip, "-vf", f"fps={a.fps},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                           os.path.join(cf, "%04d.png")])
nframes = len(glob.glob(os.path.join(cf, "*.png")))

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        await pg.goto("file://" + os.path.join(HERE, "reel.html"))
        await pg.evaluate("document.fonts.ready")
        await pg.evaluate(f"window.CLIP_FRAMES={nframes}; window.CLIP_FPS={a.fps}")
        if a.spec:
            import json as _j
            await pg.evaluate("sp => window.applySpec(sp)", _j.load(open(a.spec)))
        if a.preview:
            for t in a.preview.split(","):
                await pg.evaluate(f"window.seek({float(t)})")
                await pg.screenshot(path=os.path.join(HERE, f"preview_{t}.png"))
            await b.close(); return
        fd = os.path.join(HERE, "frames"); shutil.rmtree(fd, ignore_errors=True); os.makedirs(fd)
        n = int(round(a.duration * a.fps))
        for i in range(n):
            await pg.evaluate(f"window.seek({i / a.fps})")
            await pg.screenshot(path=os.path.join(fd, f"{i:04d}.png"))
        await b.close()
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", os.path.join(HERE, "frames", "%04d.png"),
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-movflags", "+faststart", a.out])
    print(a.out)

asyncio.run(main())
