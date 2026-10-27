"""Builds index.html and tantra.html from the sweettouch.fr text dumps in ../content.
Run: python -I build.py   (re-run after editing content or templates)"""
import html, re
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


def mcard(name, prices, href="#"):
    dl = "".join(f"<div><dt>{e(d)}</dt><dd>{p} €</dd></div>" for d, p in prices)
    return (f'<a class="card card--m" href="{href}"><figure><img src="img/m-{SLUG[name]}.webp" alt="" loading="lazy"></figure>'
            f'<h3 class="card__title">{e(name)}</h3><dl class="card__prices">{dl}</dl></a>')


def rail(cards, label, cls=""):
    return (f'<div class="rail{cls}" data-rail><div class="rail__track" tabindex="0" aria-label="{e(label)}">{"".join(cards)}</div>'
            '<div class="rail__nav"><button type="button" data-prev aria-label="Previous">Previous</button>'
            '<button type="button" data-next aria-label="Next">Next</button></div></div>')


def massages_tabs(rows):
    grouped = [[r for r in rows if (g is None and not any(r[0] in s for _, s in GROUPS[1:])) or (g and r[0] in g)] for _, g in GROUPS]
    tabs = "".join(f'<button type="button" role="tab" aria-selected="{"true" if i == 0 else "false"}" data-tab="{i}">{e(t)} <sup>{len(grouped[i])}</sup></button>'
                   for i, (t, _) in enumerate(GROUPS))
    panels = "".join(f'<div class="tabpanel" role="tabpanel" data-panel="{i}"{"" if i == 0 else " hidden"}>'
                     f'{rail([mcard(n, p, "tantra.html" if n == "Tantra Massage" else "#") for n, p in g], GROUPS[i][0])}</div>'
                     for i, g in enumerate(grouped))
    assert sum(map(len, grouped)) == len(rows), "every service must land in exactly one tab"
    return f'<div class="tabs" role="tablist">{tabs}</div>{panels}'


def girls(names):
    return rail([f'<a class="card card--g" href="https://sweettouch.fr/girl/{n.lower()}"><figure><img src="img/{n.lower()}.webp" alt="{n}" loading="lazy"></figure>'
                 f'<span class="card__title">{n}</span><span class="card__vip">VIP</span></a>' for n in names], "Masseuses", " rail--girls")


def article(block, images):
    out, sec = [], None

    def close():
        if sec:
            h, body = sec
            img = images.get(h)
            fig = f'<figure class="chapter__img"><img src="img/m-{img}.webp" alt="" loading="lazy"></figure>' if img else ""
            out.append(f'<details class="chapter"{"" if out else " open"}><summary><h2 class="chapter__title">{e(h)}</h2><span class="chapter__toggle" aria-hidden="true"></span></summary>'
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
}
MAIN = [("Our masseuses", "https://sweettouch.fr/girl", "katlin"), ("Massages & prices", "index.html#massages", "m-tantra"),
        ("Paris locations", "https://sweettouch.fr/paris-locations", "m-overnight"), ("Erotic Massage in France", "https://sweettouch.fr/erotic-massage-in-france", "m-sexy-guide"),
        ("Job offers", "https://sweettouch.fr/job-offers", "m-six-hands"), ("Fidelity Card", "https://sweettouch.fr/fidelity-card", "m-date")]
LANGS = '<a aria-current="true">English</a><a href="https://sweettouch.fr/fr/">Français</a><a href="https://sweettouch.fr/ru/">Русский</a>'


def icon(name):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>'


def nav():
    sub = "".join(f'<li><a href="{"tantra.html" if s == "Tantric Massage" else "#"}">{s}</a></li>' for s in SUB)
    big = "".join(f'<li><a class="drawer__big" href="{u}" data-img="img/{im}.webp"><span class="drawer__t">{e(t)}</span></a></li>'
                  for t, u, im in MAIN)
    return f'''<header class="nav" data-nav>
  <div class="nav__left">
    <button class="nav__menu" data-burger aria-expanded="false" aria-controls="drawer"><span class="burger" aria-hidden="true"><i></i><i></i></span><span class="nav__menu-label">Menu</span></button>
    <span class="nav__lang">{LANGS}</span>
  </div>
  <a class="nav__logo" href="index.html">SweetTouch</a>
  <div class="nav__right">
    <a class="nav__icon" href="tel:+33758963765" aria-label="+33 7 58 96 37 65" title="+33 7 58 96 37 65">{icon("phone")}</a>
    <a class="nav__icon" href="https://wa.me/%2B33758963765" aria-label="Call by Whatsapp" title="Call by Whatsapp">{icon("chat")}</a>
    <a class="nav__icon" href="https://t.me/sweettouchfr" aria-label="Send to Telegram" title="Send to Telegram">{icon("send")}</a>
    <a class="btn btn--sm" href="#book">Make a booking</a>
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


def marquee(names):
    """Two rows running in opposite directions; speed follows scroll velocity (main.js)."""
    dot = '<svg class="marquee__dot" viewBox="0 0 10 10" aria-hidden="true"><path d="M5 0 6.2 3.8 10 5 6.2 6.2 5 10 3.8 6.2 0 5 3.8 3.8Z"/></svg>'
    items = "".join(f"<span>{e(n)}</span>{dot}" for n in names)
    return (f'<div class="marquee" data-marquee aria-hidden="true">'
            f'<div class="marquee__row"><div class="marquee__track">{items}{items}</div></div>'
            f'<div class="marquee__row marquee__row--line"><div class="marquee__track">{items}{items}</div></div></div>')


def footer(copy):
    links = "".join(f'<a href="https://sweettouch.fr/{u}">{t}</a>' for t, u in FOOT_LINKS)
    soc = "".join(f'<a href="{u}">{t}</a>' for t, u in SOCIAL)
    return f'''<footer class="foot" id="book" data-tone="noir">
  <div class="foot__top">
    <div><a class="foot__logo" href="index.html">SweetTouch</a><p class="foot__muted">You can find us</p><div class="foot__soc">{soc}</div></div>
    <div class="foot__links">{links}</div>
    <address class="foot__contact"><a href="tel:+33758963765">+33 7 58 96 37 65</a><a href="https://wa.me/%2B33758963765">WhatsApp +33 7 58 96 37 65</a>
      <a href="mailto:erotic.sweettouch@gmail.com">erotic.sweettouch@gmail.com</a><a href="https://goo.gl/maps/CbB6k75MipvzVnVbA">Avenue de Wagram 75017</a></address>
  </div>
  <div class="foot__bottom"><span>{e(copy)}</span><span>We do not offer any kind of sexual services.</span><span class="foot__credit">Designed &amp; developed by <b>Next Web</b></span></div>
</footer>'''


_LS = (ROOT / "public" / "loader.svg").read_text()  # traced by trace_loader.py
VB = re.search(r'viewBox="([^"]+)"', _LS).group(1)
STRANDS = re.search(r'<g id="strands">(.*?)</g>', _LS).group(1)  # contour halves, each running bottom -> top


def loader():
    return f'''<div class="loader" data-loader aria-hidden="true">
  <svg class="loader__sil" viewBox="{VB}">
    {STRANDS.replace("<path ", '<path class="loader__line" fill="none" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" ')}
  </svg>
  
</div>'''


def hero(words, label, imgs, after, cls="", fs=(0.165, 0.205), video=None):
    """Vector hero: the word is an SVG mask over full-resolution photos, so scaling it stays sharp.
    main.js sizes the viewBox to the viewport and lays out the lines (fs = font size as share of width, desktop/mobile).
    The scroll flies through the ball terminal of the first "r" (main.js).
    video: looped clip inside the letters; imgs[0] stays under it as the poster while it loads."""
    vid = (f'<foreignObject class="hx__vid"><video xmlns="http://www.w3.org/1999/xhtml" src="video/{video}.mp4" poster="img/{imgs[0]}.webp" '
           'autoplay muted loop playsinline preload="auto"></video></foreignObject>') if video else ""
    texts = "".join(f'<text text-anchor="middle">{e(w)}</text>' for w in words)
    images = "".join(f'<image class="hx__img{" is-on" if i == 0 else ""}" href="img/{s}.webp" preserveAspectRatio="xMidYMid slice"/>' for i, s in enumerate(imgs))
    return f'''<section class="hx {cls}" data-hx>
  <div class="hx__pin">
    <h1 class="sr-only">{e(label)}</h1>
    <svg class="hx__svg" data-fs="{fs[0]}" data-fs-m="{fs[1]}" aria-hidden="true">
      <defs><mask id="hx-mask" maskUnits="userSpaceOnUse">
        <rect class="hx__mbg" fill="#000"/><rect class="hx__mfull" fill="#fff" opacity="0"/>
        <g class="hx__words hx__words--mask" fill="#fff">{texts}</g>
      </mask></defs>
      <g mask="url(#hx-mask)">{images}{vid}</g>
      <g class="hx__words hx__words--edge" fill="none">{texts}</g>
    </svg>
    <div class="hx__shade" aria-hidden="true"></div>
    <div class="hx__light" aria-hidden="true"></div>
    {after}
  </div>
</section>'''


def page(title, desc, body):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,900;1,6..96,400&family=Instrument+Sans:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/src/style.css">
<script type="module" src="/src/main.js"></script>
</head>
<body class="is-loading">
{loader()}
<div class="cursor" aria-hidden="true"><span class="cursor__label"></span></div>
<div class="glow" aria-hidden="true"></div>
<div class="thread" aria-hidden="true"><span></span></div>
{nav()}
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
    copy = next(l for l in L if l.startswith("Сopyright"))

    words = "".join(f"<li>{e(s)}</li>" for s in SUB)
    after = f'''<ul class="hx__ticker" aria-hidden="true">{words}</ul>
    <div class="hx__after">
      <p class="hx__paris">in Paris</p>
      <p class="hx__intro">{e(intro)}</p>
      <a class="btn" href="#book">Book online</a>
    </div>
    <p class="hx__hint" aria-hidden="true">Scroll</p>'''
    stage_imgs = ["m-all-day", "m-overnight", "m-six-hands", "m-erotic-chat", "m-wife"]
    layers = "\n".join(f'<div class="stage__layer" style="--img:url(/img/{stage_imgs[k]}.webp)"></div>' for k in range(len(advs)))
    texts = "\n".join(f'<article class="stage__text"><h2>{e(a)}</h2><p class="stage__sub">{e(b)}</p><p>{e(c)}</p><a class="link" href="#">{e(d)}</a></article>'
                      for a, b, c, d in advs)
    steps_html = "\n".join(f'<li class="step"><span class="step__n">{e(n)}</span><h3>{e(t)}</h3><p>{e(p)}</p></li>' for n, t, p in steps)
    cities = ["madrid", "marbella", "mallorca", "ibiza", "amsterdam", "rome", "milan", "london", "courchevel", "aix"]
    posts_html = [f'<a class="card card--b" href="#"><figure><img src="img/{c}.webp" alt="" loading="lazy"></figure><time>{e(d)}</time><h3 class="card__title">{e(t)}</h3><p>{e(x)}</p><span class="link">read more</span></a>'
                  for (t, d, x, _), c in zip(posts, cities)]

    body = f'''{hero(["Erotic", "Massage"], "Erotic Massage in Paris", ["hero-poster"], after, video="hero")}

<section class="sect about" data-tone="wine">
  <div class="about__text"><h2 class="h2">About SweetTouch</h2><p class="about__p" data-highlight>{e(about)}</p></div>
  <figure class="about__img" data-parallax><img src="img/m-about.webp" alt="" loading="lazy"></figure>
</section>

<section class="sect girls" id="girls" data-tone="noir">
  <div class="row-head"><h2 class="h2">Our sweet girls</h2><a class="link" href="https://sweettouch.fr/girl">See all</a></div>
  {girls(names)}
  <p class="lead lead--wide">Relive the unique experience of sensual intimate massage with SweetTouch!</p>
</section>

{marquee(SUB)}

<section class="sect split" data-tone="noir">
  <figure class="split__img" data-parallax><img src="img/m-outcall.webp" alt="" loading="lazy"></figure>
  <div><h2 class="h2 h2--m">{e(inc_h)}</h2><p>{e(inc_p)}</p></div>
</section>

<section class="sect massages" id="massages" data-tone="wine">
  <h2 class="h2">Massages</h2>
  {massages_tabs(rows)}
</section>

<section class="stage" data-stage data-tone="noir" aria-label="Why SweetTouch">
  <div class="stage__pin">
    <div class="stage__media">{layers}</div>
    <div class="stage__texts">{texts}</div>
    <div class="stage__bar">{"".join("<span></span>" for _ in advs)}</div>
  </div>
</section>

<section class="sect articles" data-tone="wine">
{article(art, {"What Is SweetTouch Erotic Massage? A Journey Beyond Relaxation": "sensual", "Our Exclusive Erotic Massage Services in Paris": "couple",
               "Discover Our Special, One-of-a-Kind Offers!": "strawberry", "Meet Our Masseuses: The Heart of SweetTouch": "six-hands"})}
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

<section class="sect faq" data-tone="wine">
  <h2 class="h2">FAQ</h2>
  <div class="faq__list">{faq(fq)}</div>
</section>
{footer(copy)}'''
    return page(L[0], intro[:155], body)


def build_tantra():
    L = lines("page_info_tantra-massage.txt")
    checks = [l.replace(" ✓", "") for l in L if l.endswith("✓")]
    others = services(between(L, "Other erotic massage services", "## Tantra Massage in Paris"))
    art = L[L.index("## Tantra Massage in Paris"):L.index("Our Professional Masseuses", L.index("## Our Professional Masseuses") + 1)]
    gi = L.index("## FAQ")
    team = [L[k + 2] for k in range(gi) if L[k] == "girl_video"]
    fq = L[gi + 1:L.index("Duration", gi)]
    copy = next(l for l in L if l.startswith("Сopyright"))
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
      <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">SweetTouch</a> / <a href="index.html#massages">Massages &amp; prices</a> / <span>Tantra Massage</span></nav>
      <p class="hx__paris">Massage</p>
      <ul class="checks">{"".join(f"<li>{check_svg}{e(c)}</li>" for c in checks)}</ul>
      <a class="btn" href="#book">Book online</a>
    </div>
    <p class="hx__hint" aria-hidden="true">Scroll</p>'''
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
{footer(copy)}'''
    return page(L[0], art[1][:155], body)


(ROOT / "index.html").write_text(build_home(), encoding="utf-8")
(ROOT / "tantra.html").write_text(build_tantra(), encoding="utf-8")
print("built index.html, tantra.html")
