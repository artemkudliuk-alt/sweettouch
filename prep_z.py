"""Generated Z-Image frames -> public/img/z-<slot>.webp (+ -800 copy for srcset). Rerun after changing PICKS."""
from pathlib import Path
from PIL import Image

SRC = Path(__file__).parent.parent / "photos" / "zimage"
DST = Path(__file__).parent / "public" / "img"
PICKS = {  # slot: source frame
    "about": "p18-b", "all-day": "c06", "promo": "p21-a",
    "sensual": "c12", "couple": "c04", "strawberry": "c03", "six-hands": "c07",
    "tantra-1": "p24-a", "tantra-2": "p27-a", "tantra-3": "p18-a",
    "adv-premium": "p08-b", "adv-private": "t2-hotel-window", "adv-techniques": "m05-b",
    "bg-how": "c08", "bg-faq": "c12",
    "gal-1": "p12-a", "gal-2": "p19-a", "gal-3": "t2-rooftop", "gal-4": "t2-library",
    "menu-girls": "p22-a", "menu-massages": "t-oil-hands", "menu-locations": "p34-a", "menu-france": "p10-a", "menu-jobs": "p21-b", "menu-card": "p08-a",
    "tantra-origin": "m02-c", "tantra-meet": "t2-masseuse-candles",
}

for slot, src in PICKS.items():
    im = Image.open(SRC / f"{src}.jpg").convert("RGB")
    im.save(DST / f"z-{slot}.webp", quality=88)
    im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS).save(DST / f"z-{slot}-800.webp", quality=84)
    print(slot, src, im.size)
