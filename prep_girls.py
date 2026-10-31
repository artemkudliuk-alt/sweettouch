"""Masseuse photos from content/girls_raw/<slug>/<n>.jpg -> public/img/g-<slug>-<n>.webp (+ -800 copy when wider).
Run after content/scrape_girls.py: python -I prep_girls.py"""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
RAW = ROOT.parent / "content" / "girls_raw"
OUT = ROOT / "public" / "img"

for g in json.loads((ROOT.parent / "content" / "girls.json").read_text(encoding="utf-8")):
    for f in g["files"]:
        dst = OUT / f"g-{g['slug']}-{Path(f).stem}.webp"
        if dst.exists():
            continue
        im = Image.open(RAW / g["slug"] / f).convert("RGB")
        if im.width > 1200:
            im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
        im.save(dst, "webp", quality=82)
        if im.width > 800:
            im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS).save(dst.with_name(dst.stem + "-800.webp"), "webp", quality=80)
print("ok")
