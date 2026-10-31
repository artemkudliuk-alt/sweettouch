"""Builds index.html and tantra.html from the sweettouch.fr text dumps in ../content.
Run: python -I build.py   (re-run after editing content or templates)"""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT = ROOT.parent / "content"
e = html.escape

LIST_STARTS = ("Take a warm", "Wear loose", "Come with", "Arrive on", "Is it your first", "Turn off",
               "Physical relaxation", "Mental escape", "Awakened senses", "Better intimacy", "Enhanced confidence",
               "Strawberry Massage —", "Big Breasts Massage —", "Feather Massage —", "Massage with Toys —",
               "Expert Training:", "Personalised Approach:", "Attentive & Discreet:",
               "Arab countries.", "Brazil.", "Colombia.", "France.", "Spain.", "Russia.",
               "We accept only", "Payment should", "You can contact SweetTouch", "There is a chat", "Confidentiality is guaranteed.")
LEADS = ("Dear Guests and Parisians,", "Welcome to SweetTouch, the art", "You’ll want to come back!",
         "Call, write, we are waiting for you!", "Book your naturist massage now")

# Site service name -> generated photo slug (photos are placeholders until the real shoot)
SLUG = {"Oriental Massage": "oriental", "Erotic Massage": "erotic", "Tantra Massage": "tantra", "Body to Body Massage": "body-to-body",
        "Nuru Massage": "nuru", "Private & Mutual Massage": "private-mutual", "Erotic Chat with the Masseuse": "erotic-chat",
        "Lingam Massage": "lingam", "Tantra Prostate massage": "prostate", "Domination massage": "domination", "Yoni Massage": "yoni",
        "Naturist Massage": "naturist", "4 Hands Massage": "four-hands", "4 hands massage with lesbian show": "lesbian-show",
        "Couple Erotic Massage": "couple", "Date with masseuse": "date", "Party with Masseuses": "party", "All day Option": "all-day",
        "Overnight massage": "overnight", "Feet body massage": "feet", "Happy Ending Massage": "happy-ending", "Sensual Massage": "sensual",
        "Lesbian Massage": "lesbian", "Big breasts massage": "big-breasts", "Deep tissue massage": "deep-tissue",
        "Erotic feather massage": "feather", "Erotic Peep Show": "peep-show", "Erotic strawberry massage": "strawberry",
        "Fantasy Erotic Massage": "fantasy", "Sexy guide": "sexy-guide", "Gay Massage": "gay", "Shiatsu Massage": "shiatsu",
        "Thai Massage": "thai", "Wife for rent": "wife", "Erotic 6 Hands Massage": "six-hands", "VIP Soapy Erotic Massage": "soapy",
        "Tantra Reciprocal Candle Massage": "candle", "Strip Tease and Massage": "striptease", "Outcall Erotic Massage": "outcall"}
# Our grouping for the tabs; order inside each group follows the site
GROUPS = [("Massages", None),
          ("4 hands & couples", {"4 Hands Massage", "4 hands massage with lesbian show", "Couple Erotic Massage", "Lesbian Massage", "Erotic 6 Hands Massage"}),
          ("Shows", {"Domination massage", "Erotic Peep Show", "Strip Tease and Massage", "Erotic Chat with the Masseuse"}),
          ("Dates & time", {"Date with masseuse", "Party with Masseuses", "All day Option", "Overnight massage", "Sexy guide", "Wife for rent"})]
SUB = ["Tantric Massage", "Nuru Massage", "Lingam Massage", "Body to Body Massage", "Prostate massage", "Yoni Massage",
       "Couple Erotic Massage", "Happy Ending Massage", "Domination massage", "Erotic Massage", "Erotic Chat with the Masseuse"]


# Real masseuses from sweettouch.fr (content/scrape_girls.py); photos are img/g-<slug>-<n>.webp (prep_girls.py)
GIRLS = json.loads((CONTENT / "girls.json").read_text(encoding="utf-8"))
GIRL = {g["name"]: g for g in GIRLS}
gphoto = lambda name: f'g-{GIRL[name]["slug"]}-0'


def lines(name):
    out = []
    for l in (CONTENT / name).read_text(encoding="utf-8").splitlines():
        l = re.sub(r"\s*<[^>]*>\s*", " ", l)
        l = re.sub(r"\[img:[^\]]*\]", "", l)
        l = re.sub(r"\s+", " ", l).strip()
        if l:
            out.append(l)
    return out


def between(ls, start, end):
    i = ls.index(start)
    return ls[i + 1:ls.index(end, i + 1)]


def services(block):
    rows, cur = [], None
    for l in block:
        m = re.match(r"^(.+?) — (\d+) €$", l)
        if m and cur:
            cur[1].append((m.group(1), m.group(2)))
        elif not m and l != "vip":
            cur = (l, [])
            rows.append(cur)
    return [r for r in rows if r[1]]


def mcard(name, prices):
    """Service card; only services with a page of their own (Tantra) are links."""
    dl = "".join(f"<div><dt>{e(d)}</dt><dd>{p} €</dd></div>" for d, p in prices)
    inner = (f'<figure><img src="img/m-{SLUG[name]}.webp" alt="" sizes="(max-width: 720px) 46vw, 30vw" loading="lazy"></figure>'
             f'<h3 class="card__title">{e(name)}</h3><dl class="card__prices">{dl}</dl>')
    return f'<a class="card card--m" href="tantra.html">{inner}</a>' if name == "Tantra Massage" else f'<div class="card card--m">{inner}</div>'


def rail(cards, label, cls=""):
    return (f'<div class="rail{cls}" data-rail><div class="rail__track" tabindex="0" aria-label="{e(label)}">{"".join(cards)}</div>'
            f'<div class="rail__nav"><button type="button" data-prev aria-label="Previous">{icon("left")}</button>'
            f'<button type="button" data-next aria-label="Next">{icon("right")}</button></div></div>')


def group_rows(rows):
    return [[r for r in rows if (g is None and not any(r[0] in s for _, s in GROUPS[1:])) or (g and r[0] in g)] for _, g in GROUPS]


def massages_grid(rows, shown=6):
    """The first services; the full list lives on massages.html."""
    return (f'<div class="cgrid cgrid--m">{"".join(mcard(n, p) for n, p in rows[:shown])}</div>'
            f'<div class="cgrid__foot"><a class="btn btn--line" href="massages.html">All massages ({len(rows)}){icon("right")}</a></div>')


def book(names, rows, note=""):
    """Booking: pick a masseuse, a massage and a duration; the summary shows the price and hands the choice to
    phone / WhatsApp (prefilled message) / Telegram. Prices come straight from the parsed service list."""
    girls_html = "".join(f'<label class="pick"><input type="radio" name="girl" value="{e(n)}" data-photo="{gphoto(n)}"{" checked" if i == 0 else ""}>'
                         f'<img src="img/{gphoto(n)}.webp" alt="" loading="lazy"><span>{e(n)}</span></label>' for i, n in enumerate(names))
    opts = "".join(f'<optgroup label="{e(t)}">' + "".join(f'<option value="{e(n)}" data-prices="{e(json.dumps(p))}">{e(n)}</option>' for n, p in g) + "</optgroup>"
                   for (t, _), g in zip(GROUPS, group_rows(rows)))
    return f'''<section class="sect book" id="book" data-tone="wine">
  <h2 class="h2 book__title">Book your massage</h2>
  {note}
  <div class="book__grid" data-book>
    <div class="book__steps">
      <fieldset class="book__step"><legend><span>01</span>Masseuse</legend><div class="picks">{girls_html}</div></fieldset>
      <fieldset class="book__step"><legend><span>02</span>Massage</legend>
        <div class="book__select"><select name="massage" aria-label="Massage">{opts}</select></div></fieldset>
      <fieldset class="book__step"><legend><span>03</span>Duration</legend><div class="durs" data-durs></div></fieldset>
    </div>
    <aside class="book__card">
      <figure class="book__photo"><img data-book-photo src="img/{gphoto(names[0])}.webp" alt="" sizes="(max-width: 720px) 86vw, 460px" loading="lazy" decoding="async"></figure>
      <dl class="book__sum">
        <div><dt>Masseuse</dt><dd data-sum="girl"></dd></div>
        <div><dt>Massage</dt><dd data-sum="massage"></dd></div>
        <div><dt>Duration</dt><dd data-sum="dur"></dd></div>
      </dl>
      <p class="book__price"><span data-sum="price"></span> €</p>
      <div class="book__cta">
        <a class="btn" href="tel:+33758963765">{icon("phone")}+33 7 58 96 37 65</a>
        <a class="btn btn--line" data-wa href="https://wa.me/33758963765">{icon("chat")}Call by Whatsapp</a>
        <a class="btn btn--line" href="https://t.me/sweettouchfr">{icon("send")}Send to Telegram</a>
      </div>
    </aside>
  </div>
</section>'''


def gcard(g):
    return (f'<a class="card card--g" href="girl-{g["slug"]}.html"><figure><img src="img/g-{g["slug"]}-0.webp" alt="{e(g["name"])}" sizes="(max-width: 720px) 46vw, 18vw" loading="lazy"></figure>'
            f'<span class="card__title">{e(g["name"])}</span><span class="card__vip">{e(g["tier"].upper())}</span></a>')


def girls(names):
    return (f'<div class="cgrid cgrid--g">{"".join(gcard(GIRL[n]) for n in names if n in GIRL)}</div>'
            f'<div class="cgrid__foot"><a class="btn btn--line" href="masseuses.html">All masseuses ({len(GIRLS)}){icon("right")}</a></div>')


def article(block, images):
    out, sec = [], None

    def close():
        if sec:
            h, body = sec
            img = images.get(h)
            fig = f'<figure class="chapter__img"><img src="img/m-{img}.webp" alt="" sizes="(max-width: 720px) 92vw, 46vw" loading="lazy"></figure>' if img else ""
            out.append(f'<details class="chapter"><summary><h2 class="chapter__title">{e(h)}</h2><span class="chapter__toggle" aria-hidden="true"></span></summary>'
                       f'<div class="chapter__grid">{fig}<div class="chapter__body">{"".join(body)}</div></div></details>')

    for l in block:
        if l.startswith("## "):
            close()
            sec = (l[3:], [])
        elif l.startswith("### "):
            sec[1].append(f"<h3>{e(l[4:])}</h3>")
        elif l.startswith(LIST_STARTS):
            sec[1].append(f'<p class="li">{e(l)}</p>')
        elif l.startswith(LEADS):
            sec[1].append(f'<p class="lead">{e(l)}</p>')
        else:
            sec[1].append(f"<p>{e(l)}</p>")
    close()
    return "\n".join(out)


def faq(block):
    out, q = [], None
    for l in block:
        if l.startswith("### "):
            q = l[4:]
        elif q:
            out.append(f'<details class="faq__item"{"" if out else " open"}><summary>{e(q)}</summary><p>{e(l)}</p></details>')
            q = None
    return "\n".join(out)


ICON = {  # Lucide-style line icons
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
    "chat": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/>',
    "send": '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
    "left": '<path d="M19 12H5"/><path d="m12 19-7-7 7-7"/>',
    "right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "out": '<path d="M7 17 17 7"/><path d="M7 7h10v10"/>',
}
MAIN = [("Our masseuses", "masseuses.html", "m-about"), ("Massages & prices", "massages.html", "m-tantra"),
        ("Paris locations", "https://sweettouch.fr/paris-locations", "m-overnight"), ("Erotic Massage in France", "https://sweettouch.fr/erotic-massage-in-france", "m-sexy-guide"),
        ("Job offers", "https://sweettouch.fr/job-offers", "m-six-hands"), ("Fidelity Card", "https://sweettouch.fr/fidelity-card", "m-date")]
LANGS = '<a aria-current="true">English</a><a href="https://sweettouch.fr/fr/">Français</a><a href="https://sweettouch.fr/ru/">Русский</a>'
FLAG = {  # small rectangular flags for the compact language switcher (as on mandra.nextweb.ua)
    "EN": '<svg viewBox="0 0 60 40" aria-hidden="true"><rect width="60" height="40" fill="#012169"/><path d="M0 0l60 40M60 0L0 40" stroke="#fff" stroke-width="8"/><path d="M0 0l60 40M60 0L0 40" stroke="#C8102E" stroke-width="3"/><path d="M30 0v40M0 20h60" stroke="#fff" stroke-width="12"/><path d="M30 0v40M0 20h60" stroke="#C8102E" stroke-width="7"/></svg>',
    "FR": '<svg viewBox="0 0 60 40" aria-hidden="true"><rect width="20" height="40" fill="#0055A4"/><rect x="20" width="20" height="40" fill="#fff"/><rect x="40" width="20" height="40" fill="#EF4135"/></svg>',
    "RU": '<svg viewBox="0 0 60 40" aria-hidden="true"><rect width="60" height="14" fill="#fff"/><rect y="13" width="60" height="14" fill="#0039A6"/><rect y="26" width="60" height="14" fill="#D52B1E"/></svg>',
}
# Header shortcuts: the three things a visitor looks for first; everything else lives in the burger
TOP = [("Masseuses", "masseuses.html"), ("Massages & prices", "massages.html"), ("Locations", "https://sweettouch.fr/paris-locations")]


def lang_switch():
    others = "".join(f'<a href="https://sweettouch.fr/{c.lower()}/" lang="{c.lower()}">{FLAG[c]}<span>{c}</span></a>' for c in ("FR", "RU"))
    return (f'<details class="lang" data-lang><summary aria-label="Language: English">{FLAG["EN"]}<span>EN</span>'
            '<svg class="lang__chev" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></summary>'
            f'<div class="lang__menu">{others}</div></details>')


def icon(name):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>'


def nav():
    sub = "".join(f'<li><a href="{"tantra.html" if s == "Tantric Massage" else "#"}">{s}</a></li>' for s in SUB)
    big = "".join(f'<li><a class="drawer__big" href="{u}" data-img="img/{im}.webp"><span class="drawer__t">{e(t)}</span></a></li>'
                  for t, u, im in MAIN)
    return f'''<header class="nav" data-nav>
  <div class="nav__left">
    <button class="nav__menu" data-burger aria-expanded="false" aria-controls="drawer"><span class="burger" aria-hidden="true"><i></i><i></i></span><span class="nav__menu-label">Menu</span></button>
    <nav class="nav__links" aria-label="Shortcuts">{"".join(f'<a href="{u}">{e(t)}</a>' for t, u in TOP)}</nav>
  </div>
  <a class="nav__logo" href="index.html">SweetTouch</a>
  <div class="nav__right">
    {lang_switch()}
    <a class="nav__icon nav__icon--call" href="tel:+33758963765" aria-label="+33 7 58 96 37 65" title="+33 7 58 96 37 65">{icon("phone")}</a>
    <a class="nav__icon" href="https://wa.me/%2B33758963765" aria-label="Call by Whatsapp" title="Call by Whatsapp">{icon("chat")}</a>
    <a class="nav__icon" href="https://t.me/sweettouchfr" aria-label="Send to Telegram" title="Send to Telegram">{icon("send")}</a>
    <a class="btn btn--gold btn--nav" href="#book">Make a booking</a>
  </div>
</header>
<div class="drawer" id="drawer" data-drawer hidden>
  <figure class="drawer__img" aria-hidden="true"><img src="img/{MAIN[0][2]}.webp" alt=""></figure>
  <nav class="drawer__main" aria-label="Main"><ol>{big}</ol></nav>
  <div class="drawer__side">
    <div><p class="drawer__label">Massages &amp; prices</p><ul class="drawer__sub">{sub}</ul></div>
    <div class="drawer__contact">
      <a class="drawer__phone" href="tel:+33758963765">+33 7 58 96 37 65</a>
      <a class="drawer__chip" href="https://wa.me/%2B33758963765">{icon("chat")}Call by Whatsapp</a>
      <a class="drawer__chip" href="https://t.me/sweettouchfr">{icon("send")}Send to Telegram</a>
      <a class="btn" href="#book">Make a booking</a>
    </div>
    <span class="nav__lang">{LANGS}</span>
  </div>
</div>'''


FOOT_LINKS = [("Contact us", "contact"), ("FAQ", "faq"), ("Terms and Conditions", "terms-and-conditions"), ("DMCA policy", "dmca-policy"),
              ("Blog", "blog"), ("Partners", "partners"), ("Sitemap", "sitemap"), ("About", "about"), ("Discounts", "discounts"),
              ("Testimonials", "testimonials"), ("Book your massage", "book-your-massage"), ("Erotic massage in France", "erotic-massage-in-france")]
SOCIAL = [("Twitter", "https://twitter.com/SweettouchParis"), ("YouTube", "https://www.youtube.com/channel/UCPpgdZ-Z3EPngJuJxBFpuWg"),
          ("Pinterest", "https://www.pinterest.fr/sweeeettouch/"), ("Instagram", "https://www.instagram.com/erotic_massage_paris"),
          ("Facebook", "https://facebook.com/sweettouchoutcallparis/")]


def footer():
    links = "".join(f'<a href="https://sweettouch.fr/{u}">{t}</a>' for t, u in FOOT_LINKS)
    soc = "".join(f'<a href="{u}">{t}</a>' for t, u in SOCIAL)
    return f'''<footer class="foot" data-tone="noir">
  <div class="foot__top">
    <div><a class="foot__logo" href="index.html">SweetTouch</a><p class="foot__muted">You can find us</p><div class="foot__soc">{soc}</div></div>
    <div class="foot__links">{links}</div>
    <address class="foot__contact"><a href="tel:+33758963765">{icon("phone")}+33 7 58 96 37 65</a><a href="https://wa.me/%2B33758963765">{icon("chat")}WhatsApp +33 7 58 96 37 65</a>
      <a href="mailto:erotic.sweettouch@gmail.com">{icon("mail")}erotic.sweettouch@gmail.com</a><a href="https://goo.gl/maps/CbB6k75MipvzVnVbA">{icon("pin")}Avenue de Wagram 75017</a></address>
  </div>
  <div class="foot__bottom"><span>We do not offer any kind of sexual services.</span><span class="foot__credit">Designed &amp; developed by <b>Next Web</b></span></div>
</footer>'''


def hero(words, label, imgs, after, cls="", fs=(0.165, 0.205), video=None):
    """Vector hero: the word is an SVG mask over full-resolution photos, so scaling it stays sharp.
    main.js sizes the viewBox to the viewport and lays out the lines (fs = font size as share of width, desktop/mobile).
    video: looped clip inside the letters; imgs[0] stays under it as the poster while it loads."""
    texts = "".join(f'<text text-anchor="middle">{e(w)}</text>' for w in words)
    # Video pages paint the letters on a canvas (video drawn through the glyphs, see main.js): an SVG mask over a
    # <video> is ignored by Safari and re-rasterised on the CPU every frame elsewhere
    vid = (f'<video class="hx__src" data-src="video/{video}.mp4" data-src-m="video/{video}-m.mp4" muted loop playsinline preload="none" aria-hidden="true"></video>'
           f'<canvas class="hx__cv" data-poster="img/{imgs[0]}.webp" data-poster-m="img/{imgs[0]}-m.webp" aria-hidden="true"></canvas>') if video else ""
    images = "".join(f'<image class="hx__img{" is-on" if i == 0 else ""}" href="img/{s}.webp" preserveAspectRatio="xMidYMid slice"/>' for i, s in enumerate(imgs))
    return f'''<section class="hx {cls}" data-hx>
  <div class="hx__pin">
    <h1 class="sr-only">{e(label)}</h1>
    {vid}
    <svg class="hx__svg" data-fs="{fs[0]}" data-fs-m="{fs[1]}" aria-hidden="true">
      <defs><mask id="hx-mask" maskUnits="userSpaceOnUse">
        <rect class="hx__mbg" fill="#000"/><rect class="hx__mfull" fill="#fff" opacity="0"/>
        <g class="hx__words hx__words--mask" fill="#fff" stroke="#fff" stroke-linejoin="round">{texts}</g>
      </mask></defs>
      {"" if video else f'<g mask="url(#hx-mask)">{images}<rect class="hx__lift" fill="#f2b35e" opacity="0.1"/></g>'}
      <g class="hx__words hx__words--edge" fill="none">{texts}</g>
    </svg>
    <div class="hx__shade" aria-hidden="true"></div>
    {after}
  </div>
</section>'''


def responsive(html_):
    """Every <img> with an 800px copy gets a srcset (phones pick the light one for cards) and async decoding."""
    from PIL import Image as _I

    def sub(m):
        tag, name = m.group(0), m.group(1)
        small = ROOT / "public" / "img" / f"{name}-800.webp"
        if "decoding=" not in tag:
            tag = tag.replace("<img ", '<img decoding="async" ', 1)
        if small.exists() and "srcset=" not in tag:
            w = _I.open(ROOT / "public" / "img" / f"{name}.webp").width
            sizes = "" if "sizes=" in tag else ' sizes="(max-width: 720px) 72vw, 380px"'
            tag = tag.replace(f'src="img/{name}.webp"', f'src="img/{name}.webp" srcset="img/{name}-800.webp 800w, img/{name}.webp {w}w"{sizes}', 1)
        return tag
    return re.sub(r'<img [^>]*?src="img/([\w-]+)\.webp"[^>]*>', sub, html_)


def page(title, desc, body):
    body = responsive(body)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/bodoni-black.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,900;1,6..96,400&family=Instrument+Sans:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/src/style.css">
<script type="module" src="/src/main.js"></script>
</head>
<body>
<div class="cursor" aria-hidden="true"><span class="cursor__label"></span></div>
<div class="glow" aria-hidden="true"></div>
<div class="thread" aria-hidden="true"><span></span></div>
{nav()}
<nav class="mbar" aria-label="Quick contact">
  <a href="tel:+33758963765" aria-label="+33 7 58 96 37 65">{icon("phone")}Call</a>
  <a href="https://wa.me/33758963765" aria-label="Call by Whatsapp">{icon("chat")}WhatsApp</a>
  <a class="mbar__book" href="#book">Make a booking</a>
</nav>
<main>
{body}
</main>
</body>
</html>
'''


def build_home():
    L = lines("page_.txt")
    intro = L[L.index("# Erotic Massage in Paris") + 1].replace(" Book online", "").strip()
    about = between(L, "## About SweetTouch", "## Our sweet girls")[0]
    gblock = between(L, "## Our sweet girls", "Relive the unique experience of sensual intimate massage with SweetTouch!")
    names = list(dict.fromkeys(l for l in gblock if re.fullmatch(r"[A-Z][a-z]+", l) and l != "See"))
    inc_h = next(l for l in L if l.startswith("## You can book"))[3:]
    inc_p = L[L.index("## " + inc_h) + 1]
    rows = services(between(L, "## Massages", "## We Invite You to SweetTouch for the Best Erotic Massage in Paris"))
    art = L[L.index("## We Invite You to SweetTouch for the Best Erotic Massage in Paris"):L.index("Premium service and quality")]
    adv_block = L[L.index("Premium service and quality"):L.index("## How it works")]
    advs = [adv_block[k:k + 4] for k in range(0, len(adv_block), 4)]
    hw = between(L, "## How it works", "Blog")
    hw_intro, steps = hw[0], [hw[k:k + 3] for k in range(1, len(hw), 3)]
    blog = between(L, "Blog", "## FAQ")
    posts = [blog[k:k + 4] for k in range(0, len(blog), 4)]
    fq = between(L, "## FAQ", "You can find us")

    after = f'''<div class="hx__after hx__after--home">
      <div class="hx__cta"><a class="btn btn--gold btn--xl" href="#book">Book online</a><a class="btn btn--line btn--xl" href="masseuses.html">Our sweet girls</a></div>
      <p class="hx__intro">{e(intro)}</p>
    </div>'''
    texts = "\n".join(f'<article class="stage__text"><h2>{e(a)}</h2><p class="stage__sub">{e(b)}</p><p>{e(c)}</p><a class="link" href="#">{e(d)}</a></article>'
                      for a, b, c, d in advs)
    steps_html = "\n".join(f'<li class="step"><span class="step__n">{e(n)}</span><h3>{e(t)}</h3><p>{e(p)}</p></li>' for n, t, p in steps)
    cities = ["madrid", "marbella", "mallorca", "ibiza", "amsterdam", "rome", "milan", "london", "courchevel", "aix"]
    posts_html = [f'<a class="card card--b" href="#"><figure><img src="img/{c}.webp" alt="" loading="lazy"></figure><time>{e(d)}</time><h3 class="card__title">{e(t)}</h3><p>{e(x)}</p><span class="link">read more</span></a>'
                  for (t, d, x, _), c in zip(posts, cities)]

    body = f'''{hero(["Erotic", "Massage"], "Erotic Massage in Paris", ["hero-poster"], after, video="hero")}

<section class="sect massages" id="massages" data-tone="noir">
  <h2 class="h2">Massages &amp; prices</h2>
  {massages_grid(rows)}
</section>

<section class="sect girls" id="girls" data-tone="noir">
  <h2 class="h2">Our sweet girls</h2>
  {girls(names)}
</section>

{book(names, rows, f'<p class="book__note"><b>{e(inc_h)}.</b> {e(inc_p)}</p>')}

<section class="sect about" data-tone="wine">
  <div class="about__text"><h2 class="h2">About SweetTouch</h2><p class="lead">Relive the unique experience of sensual intimate massage with SweetTouch!</p><p class="about__p" data-highlight>{e(about)}</p></div>
  <figure class="about__img" data-parallax><img src="img/m-about.webp" alt="" sizes="(max-width: 720px) 92vw, 46vw" loading="lazy"></figure>
</section>

<section class="stage is-static" data-stage data-tone="noir" aria-label="Why SweetTouch">
  <div class="stage__pin">
    <div class="stage__media"><div class="stage__layer" data-img="/img/m-all-day.webp"></div></div>
    <div class="stage__texts">{texts}</div>
  </div>
</section>


<section class="sect how" data-tone="noir">
  <h2 class="h2">How it works</h2>
  <p class="how__intro">{e(hw_intro)}</p>
  <ol class="steps">{steps_html}</ol>
</section>

<section class="sect blog" data-tone="noir">
  <h2 class="h2">Blog</h2>
  {rail(posts_html, "Blog")}
</section>

<section class="sect faq" data-tone="noir">
  <h2 class="h2">FAQ</h2>
  <div class="faq__list">{faq(fq)}</div>
</section>
<aside class="promo" aria-label="Make a booking"><img src="img/teacher.webp" alt="" loading="lazy" decoding="async"><a class="btn" href="#book">Make a booking</a></aside>
<!-- SEO copy: kept 1:1, folded into closed chapters just above the footer -->
<section class="sect articles seo" data-tone="wine" data-seo>
<div class="seo__body">
{article(art, {"What Is SweetTouch Erotic Massage? A Journey Beyond Relaxation": "sensual", "Our Exclusive Erotic Massage Services in Paris": "couple",
               "Discover Our Special, One-of-a-Kind Offers!": "strawberry", "Meet Our Masseuses: The Heart of SweetTouch": "six-hands"})}
</div>
<button class="more seo__toggle" type="button" data-seo-toggle aria-expanded="false">Show all</button>
</section>
{footer()}'''
    return page(L[0], intro[:155], body)


def build_tantra():
    L = lines("page_info_tantra-massage.txt")
    checks = [l.replace(" ✓", "") for l in L if l.endswith("✓")]
    others = services(between(L, "Other erotic massage services", "## Tantra Massage in Paris"))
    art = L[L.index("## Tantra Massage in Paris"):L.index("Our Professional Masseuses", L.index("## Our Professional Masseuses") + 1)]
    gi = L.index("## FAQ")
    team = [L[k + 2] for k in range(gi) if L[k] == "girl_video"]
    fq = L[gi + 1:L.index("Duration", gi)]
    table = '''<div class="ptable">
  <div class="ptable__row ptable__head"><span>Duration</span><span>Incall</span><span>Outcall</span></div>
  <div class="ptable__row"><span>30 min</span><b>300 €</b><b class="dim">only incall €</b></div>
  <div class="ptable__row"><span>1 hour</span><b>450 €</b><b>500 €</b></div>
  <div class="ptable__row"><span>90 min</span><b>550 €</b><b>650 €</b></div>
  <div class="ptable__row"><span>2 hours</span><b>700 €</b><b>750 €</b></div>
  <p class="ptable__note">* taxi included only inside Paris</p>
  <a class="btn" href="#book">Book online</a>
</div>'''
    check_svg = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    after = f'''<div class="hx__after">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">SweetTouch</a> / <a href="massages.html">Massages &amp; prices</a> / <span>Tantra Massage</span></nav>
      <p class="hx__paris">Massage</p>
      <ul class="checks">{"".join(f"<li>{check_svg}{e(c)}</li>" for c in checks)}</ul>
      <a class="btn" href="#book">Book online</a>
    </div>
    '''
    body = f'''{hero(["Tantra"], "Tantra Massage", ["hx-tantra", "hero-2", "hx-candle"], after, "hx--short", (0.27, 0.27))}

<section class="sect split split--dark" data-tone="wine">
  <div><h2 class="h2 h2--m">{e(art[0][3:])}</h2><p>{e(art[1])}</p></div>
  {table}
</section>

<section class="sect massages" id="massages" data-tone="noir">
  <h2 class="h2">Other erotic massage services</h2>
  {rail([mcard(n, p) for n, p in others], "Other erotic massage services")}
</section>

<section class="sect articles" data-tone="wine">
{article(art[2:], {"Erotic Origin of Tantra": "oriental", "Meet Tantric Massage in Paris": "candle"})}
</section>

<section class="sect girls" data-tone="noir">
  <h2 class="h2">Our Professional Masseuses</h2>
  {girls(team)}
</section>

<section class="sect faq" data-tone="noir">
  <h2 class="h2">FAQ</h2>
  <div class="faq__list">{faq(fq)}</div>
</section>

<section class="sect split split--dark book" data-tone="wine">
  <h2 class="book__title">Tantra<br>Massage</h2>
  {table}
</section>
{footer()}'''
    return page(L[0], art[1][:155], body)


def home_rows():
    L = lines("page_.txt")
    return services(between(L, "## Massages", "## We Invite You to SweetTouch for the Best Erotic Massage in Paris"))


def phead(title, crumbs, sub=""):
    trail = " / ".join([*(f'<a href="{u}">{e(t)}</a>' for t, u in crumbs), f"<span>{e(title)}</span>"])
    sub = f'<p class="phead__sub">{e(sub)}</p>' if sub else ""
    return f'<header class="sect phead" data-tone="wine"><nav class="crumbs" aria-label="Breadcrumb">{trail}</nav><h1 class="phead__h">{e(title)}</h1>{sub}</header>'


def build_massages():
    groups = "\n".join(f'<section class="sect massages" data-tone="noir"><h2 class="h2 h2--m">{e(t)}</h2>'
                       f'<div class="cgrid cgrid--m">{"".join(mcard(n, p) for n, p in g)}</div></section>'
                       for (t, _), g in zip(GROUPS, group_rows(home_rows())))
    body = f'''{phead("Massages & prices", [("SweetTouch", "index.html")])}
{groups}
{footer()}'''
    return page("Erotic Massages & Prices in Paris - SweetTouch", "All erotic massages of SweetTouch in Paris with prices for every duration.", body)


def build_masseuses():
    L = lines("page_girl.txt")
    body = f'''{phead(L[L.index("# Paris Luxury Sweet Girls")][2:], [("SweetTouch", "index.html")], "Best selection of sexy masseuses in Paris & France")}
<section class="sect girls" data-tone="noir"><div class="cgrid cgrid--g">{"".join(gcard(g) for g in GIRLS)}</div></section>
{footer()}'''
    return page(L[0], "Best selection of sexy masseuses in Paris & France", body)


def build_girl(g, rows):
    """Profile: every photo in a column on the left, name, booking and facts on the right; then locations, hours, services."""
    from urllib.parse import quote
    price, n, P = dict(rows), g["name"], g["params"]
    pics = "".join(f'<figure class="prof__pic"><img src="img/g-{g["slug"]}-{i}.webp" alt="{e(n)}" sizes="(max-width: 720px) 92vw, 46vw"{"" if i == 0 else " loading=\"lazy\""}></figure>'
                   for i in range(len(g["files"])))
    facts = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in P.items())
    hours = "".join(f"<div><dt>{d}</dt><dd>{e(h)}</dd></div>" for d, h in g["hours"].items())
    svc = "".join(f'<li><span>{e(x)}</span><b>from {min(int(p) for _, p in price[x])} €</b></li>' for x in g["services"] if x in price)
    others = [x for x in GIRLS if x is not g][:5]
    wa = "https://wa.me/33758963765?text=" + quote(f"Hello SweetTouch! I would like to book a massage with {n}.")
    about = "".join(f'<p class="prof__about">{e(a)}</p>' for a in g["about"])
    locs = "".join(f'<h3 class="prof__h3">{t}</h3><ul class="plain">{"".join(f"<li>{e(x)}</li>" for x in g[k])}</ul>' for t, k in (("Incall", "incall"), ("Outcall", "outcall")) if g[k])
    body = f'''<section class="sect prof" data-tone="wine">
  <div class="prof__pics">{pics}</div>
  <div class="prof__info">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">SweetTouch</a> / <a href="masseuses.html">Masseuses</a> / <span>{e(n)}</span></nav>
    <h1 class="phead__h">{e(n)}</h1>
    <p class="prof__key"><span class="card__vip">{e(g["tier"].upper())}</span>{e(P["Age"])} y.o. · {e(P["Height"])} · {e(P["Nationality"])}</p>
    <div class="prof__cta"><a class="btn btn--gold" href="#book">Book online</a><a class="btn btn--line" href="{e(wa)}">{icon("chat")}WhatsApp</a></div>
    {about}
    <dl class="facts">{facts}</dl>
  </div>
</section>
<section class="sect prof2" data-tone="noir">
  <div><h2 class="h2 h2--m">Locations</h2>
    {locs}</div>
  <div><h2 class="h2 h2--m">Working hours</h2><dl class="facts facts--hours">{hours}</dl></div>
</section>
<section class="sect" data-tone="noir"><h2 class="h2 h2--m">{e(n)} provides</h2><ul class="svc">{svc}</ul></section>
<section class="sect girls" data-tone="wine"><h2 class="h2 h2--m">Other masseuses</h2>
  <div class="cgrid cgrid--g">{"".join(gcard(x) for x in others)}</div>
  <div class="cgrid__foot"><a class="btn btn--line" href="masseuses.html">All masseuses ({len(GIRLS)}){icon("right")}</a></div></section>
{footer()}'''
    return page(f"{n} - erotic masseuse in Paris - SweetTouch", (g["about"] or [n])[0][:155], body)


# Booking lives on the home page; every "#book" link on other pages points there
away = lambda h: h.replace('href="#book"', 'href="index.html#book"')
out = {"index.html": build_home(), "tantra.html": away(build_tantra()), "massages.html": away(build_massages()), "masseuses.html": away(build_masseuses())}
out.update({f"girl-{g['slug']}.html": away(build_girl(g, home_rows())) for g in GIRLS})
for name, h in out.items():
    (ROOT / name).write_text(h, encoding="utf-8")
print("built", len(out), "pages")
