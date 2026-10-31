"""Original massage photos from sweettouch.fr (../ref/massages/NN.img, order = SLUG in build.py) -> public/img/o-<slug>.webp + -800 copy."""
import re
from pathlib import Path
from PIL import Image

src = Path("../ref/massages")
slugs = re.findall(r'": "([a-z-]+)"', re.search(r"^SLUG = \{.*?\}", Path("build.py").read_text(encoding="utf-8"), re.S | re.M).group())
assert len(slugs) == 39 == len(list(src.glob("*.img"))), "photos must pair one-to-one with services"
for i, slug in enumerate(slugs, 1):
    im = Image.open(src / f"{i:02}.img").convert("RGB")
    im.thumbnail((1400, 1400), Image.LANCZOS)  # never upscaled: small originals stay small
    im.save(f"public/img/o-{slug}.webp", quality=84, method=6)
    if im.width > 800:
        im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS).save(f"public/img/o-{slug}-800.webp", quality=80, method=6)
