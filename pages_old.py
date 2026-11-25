"""Pages carried over 1:1 from sweettouch.fr (25.11): every massage (/info/<slug>) and the secondary pages.
Text comes from ../content/txt (extract.py dumps of ../content/raw). Imported by build.py, which owns the layout helpers."""
import difflib, re
from pathlib import Path

TXT = Path(__file__).parent.parent / "content" / "txt"
INFO_SLUGS = sorted(p.stem for p in (TXT / "info").glob("*.txt"))
MFILE = {s: "tantra.html" if s == "tantra-massage" else f"massage-{s}.html" for s in INFO_SLUGS}
# Secondary pages built locally (contact = the full booking form, since 25.11)
SECONDARY = ["paris-locations", "erotic-massage-in-france", "job-offers", "fidelity-card", "faq", "about", "testimonials",
             "discounts", "terms-and-conditions", "dmca-policy", "partners", "blog", "sitemap", "contact", "book-your-massage"]
norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-⛿️]")  # emoji only; keeps the ✓ (U+2713) of the check lists


def raw_items(rel):
    """[(text, url)] per line; images dropped, a bare <url> line attaches to the line above (blog titles)."""
    out = []
    for l in (TXT / rel).read_text(encoding="utf-8").splitlines():
        l = re.sub(r"\[img:[^\]]*\]", "", l)
        urls = re.findall(r"<\s*([^<>\s]+)\s*>", l)
        t = EMOJI.sub("", re.sub(r"\s+", " ", re.sub(r"<[^<>]*>", " ", l))).strip()
        if not t and urls and out and not out[-1][1]:
            out[-1] = (out[-1][0], urls[-1])
        elif t or urls:
            out.append((t, urls[-1] if urls else None))
    return out


def fix_head(l):
    """The source splits capitals in some headings: 'M assage', 'T echnique'."""
    return re.sub(r"(?<![\w])([B-HJ-Z]) (?=[a-z]{2,})", r"\1", l) if l.startswith("#") else l


def dur(d):
    m = re.fullmatch(r"(\d+)\s*(h|hours?|min)", d.strip(), re.I)
    if not m:
        return d
    n, u = m.groups()
    return f"{n} min" if u.lower() == "min" else f"{n} hour{'s' if n != '1' else ''}"


def parse_info(slug, services):
    L = [t for t, _ in raw_items(f"info/{slug}.txt") if t]
    h1 = next(i for i, l in enumerate(L) if l.startswith("# "))
    end = next((i for i, l in enumerate(L) if l == "You can find us"), len(L))
    durs = [i for i in range(h1, end) if L[i] == "Duration"]
    rows, note = [], ""
    for l in L[durs[0] + 1:end] if durs else []:
        if l.startswith(("Book online", "#")) or l == "Other erotic massage services":
            break
        if l in ("Incall", "Outcall"):
            continue
        if l.startswith("*"):
            note = l.lstrip("* ")
        elif re.match(r"^\d+\s*(min|h)", l, re.I) and "€" not in l:
            rows.append([dur(l)])
        elif rows and "€" in l:
            rows[-1].append(None if "only" in l.lower() else l.replace("€", "").strip())
    oi = L.index("Other erotic massage services") if "Other erotic massage services" in L else None
    a0 = next((i for i in range((oi or h1) + 1, end) if L[i].startswith("## ") and L[i] != "## FAQ"), None)
    lead = []
    if a0 is None and oi:  # some pages (4 Hands) start the text without a heading, right after the price list
        a0 = next((i for i in range(oi + 1, end) if len(L[i]) > 70 and "—" not in L[i]), None)
        lead = [f"## {L[h1][2:].strip()}"]
    stop = next((i for i in range(a0 or end, end) if L[i] == "Our Professional Masseuses" or L[i].startswith("## FAQ")), None)
    a1 = stop or (durs[1] if len(durs) > 1 else end)
    fi = next((i for i in range(h1, end) if L[i].startswith("## FAQ")), None)
    return {
        "slug": slug, "title": L[0], "name": L[h1][2:].strip(),
        "checks": [l[:-1].strip() for l in L[h1:end] if l.endswith("✓")],
        "rows": rows, "note": note,
        "others": services(L[oi + 1:a0]) if oi and a0 else [],
        "art": lead + [fix_head(l) for l in L[a0:a1] if not l.startswith("+33")] if a0 else [],
        "team": [L[k + 2] for k in range(h1, end - 2) if L[k].startswith("girl_video")],
        "faq": L[fi + 1:next((d for d in durs if d > fi), end)] if fi else [],
    }


def name_to_slug(infos):
    """Service names used across the site (cards, profiles) -> info slug, matched by name."""
    by = {norm(d["name"]): s for s, d in infos.items()}
    def find(name):
        n = norm(name)
        if n in by:
            return by[n]
        hit = difflib.get_close_matches(n, list(by), n=1, cutoff=0.72)
        return by[hit[0]] if hit else None
    return find


def local(url, girl_slugs):
    """Old-site URL -> page of this site when we have it, otherwise the old page."""
    if not url or url.startswith(("tel:", "mailto:", "#")):
        return url
    u = re.sub(r"^https?://(www\.)?sweettouch\.fr", "", url).rstrip("/")
    if u.startswith("/info/") and u[6:] in MFILE:
        return MFILE[u[6:]]
    if u.startswith("/girl/"):
        return f"girl-{u[6:]}.html" if u[6:] in girl_slugs else "masseuses.html"
    if u.lstrip("/") in SECONDARY:
        return f"{u.lstrip('/')}.html"
    return {"": "index.html", "/girl": "masseuses.html", "/info": "massages.html"}.get(u, url)
