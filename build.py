"""Builds index.html and tantra.html from the sweettouch.fr text dumps in ../content.
Run: python -I build.py   (re-run after editing content or templates)"""
import difflib, html, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))  # -I drops the script folder from the path
import pages_old as po

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
       "Couple Erotic Massage", "Happy Ending Massage", "Domination massage", "Erotic Massage", "Erotic Chat with the Masseuse", "Private & Mutual Massage"]


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


def dur(d):
    """'1h', '1hour', '2h' -> '1 hour', '2 hours'; '90min' -> '90 min' (the source mixes spellings)."""
    m = re.fullmatch(r"(\d+)\s*(h|hours?|min)", d.strip(), re.I)
    if not m: return d
    n, u = m.groups()
    return f"{n} min" if u.lower() == "min" else f"{n} hour{'s' if n != '1' else ''}"


def mimg(name):
    """Old-site photo of a massage: o-<slug>.webp, matched by name."""
    if name in SLUG:
        return SLUG[name]
    hit = difflib.get_close_matches(po.norm(name), [po.norm(k) for k in SLUG], n=1, cutoff=0.6)
    return next((v for k, v in SLUG.items() if hit and po.norm(k) == hit[0]), "erotic")


def mfile(name):
    """Page of a massage on this site (massage-<old slug>.html, Tantra keeps tantra.html), or None."""
    s = find_info(name)
    return po.MFILE[s] if s else None


def mcard(name, prices):
    """Service card; links to the massage's own page."""
    dl = "".join(f"<div><dt>{e(dur(d))}</dt><dd>{p} €</dd></div>" for d, p in prices)
    inner = (f'<figure><img src="img/o-{mimg(name)}.webp" alt="" sizes="(max-width: 720px) 46vw, 30vw" loading="lazy"></figure>'
             f'<h3 class="card__title">{e(name)}</h3><dl class="card__prices">{dl}</dl>')
    href = mfile(name)
    return (f'<a class="card card--m" id="m-{mimg(name)}" href="{href}">{inner}</a>' if href
            else f'<div class="card card--m" id="m-{mimg(name)}">{inner}</div>')


def rail(cards, label, cls="", auto=False):
    return (f'<div class="rail{cls}" data-rail{" data-auto" if auto else ""}><div class="rail__track" tabindex="0" aria-label="{e(label)}">{"".join(cards)}</div>'
            f'<div class="rail__nav"><button type="button" data-prev aria-label="Previous">{icon("left")}</button>'
            f'<button type="button" data-next aria-label="Next">{icon("right")}</button></div></div>')


def group_rows(rows):
    return [[r for r in rows if (g is None and not any(r[0] in s for _, s in GROUPS[1:])) or (g and r[0] in g)] for _, g in GROUPS]


def massages_grid(rows, shown=6):
    """The first services; the full list lives on massages.html."""
    return (f'<div class="cgrid cgrid--m">{"".join(mcard(n, p) for n, p in rows[:shown])}</div>'
            f'<div class="cgrid__foot"><a class="btn btn--line" href="massages.html">All massages ({len(rows)}){icon("right")}</a></div>')


def book(names, rows, note="", shown=12):
    """Booking: three dropdowns (masseuse, massage, duration); the summary shows the price and hands the choice to
    phone / WhatsApp (prefilled message) / Telegram. The dropdowns are <details> with radios inside, so they work without
    any widget code. Prices come straight from the parsed service list. ?girl=<slug> preselects a masseuse (profile pages link here)."""
    order = [GIRL[n] for n in names if n in GIRL] + [g for g in GIRLS if g["name"] not in names]
    girls_html = "".join(f'<label class="dd__opt"><input type="radio" name="girl" value="{e(g["name"])}" data-slug="{g["slug"]}"{" checked" if i == 0 else ""}>'
                         f'<img src="img/g-{g["slug"]}-0.webp" alt="" sizes="40px" loading="lazy"><span>{e(g["name"])}</span></label>' for i, g in enumerate(order))
    first = rows[0][0]
    massages = "".join(f'<p class="dd__group">{e(t)}</p>' + "".join(
        f'<label class="dd__opt"><input type="radio" name="massage" value="{e(n)}" data-prices="{e(json.dumps(p))}"{" checked" if n == first else ""}>'
        f'<span>{e(n)}</span><small>from {min(int(x) for _, x in p)} €</small></label>' for n, p in g)
        for (t, _), g in zip(GROUPS, group_rows(rows)))
    chev = '<svg class="dd__chev" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'
    dd = lambda label, thumb, value, attrs, items: (f'<details class="dd"><summary>{thumb}<span class="dd__val"><small>{label}</small><b>{value}</b></span>{chev}</summary>'
                                                    f'<div class="dd__list" role="group" aria-label="{label}" data-lenis-prevent {attrs}>{items}</div></details>')
    girl_thumb = f'<img data-book-photo src="img/g-{order[0]["slug"]}-0.webp" alt="" sizes="40px" decoding="async">'
    return f"""<section class="sect book" id="book" data-tone="wine">
  <div class="book__grid" data-book>
    <div class="book__steps">
      <h2 class="h2 book__title">Book your session</h2>
      {note}
      {dd("Masseuse", girl_thumb, '<span data-sum="girl"></span>', "", girls_html)}
      {dd("Massage", "", '<span data-sum="massage"></span>', "", massages)}
      {dd("Duration", "", '<span data-sum="dur"></span>', "data-durs", "")}
    </div>
    <aside class="book__card">
      <div class="book__who"><img data-book-photo src="img/g-{order[0]["slug"]}-0.webp" alt="" sizes="72px" loading="lazy" decoding="async">
        <div><p data-sum="girl"></p><a class="link" data-book-profile href="girl-{order[0]["slug"]}.html">View profile</a></div></div>
      <dl class="book__sum">
        <div><dt>Massage</dt><dd data-sum="massage"></dd></div>
        <div><dt>Duration</dt><dd data-sum="dur"></dd></div>
      </dl>
      <p class="book__price"><span data-sum="price"></span> €</p>
      <div class="book__cta">
        <a class="btn btn--gold" href="tel:+33758963765">{icon("phone")}+33 7 58 96 37 65</a>
        <a class="btn btn--line" data-wa href="https://wa.me/33758963765">{icon("chat")}Call by Whatsapp</a>
      </div>
      <form class="book__send" data-send>
        <input name="website" tabindex="-1" autocomplete="off" aria-hidden="true" class="book__hp">
        <input name="name" autocomplete="name" placeholder="Your name" aria-label="Your name">
        <input name="contact" required autocomplete="tel" placeholder="Your phone or email *" aria-label="Your phone or email">
        <button class="btn btn--line" type="submit">{icon("mail")}<span data-send-label>Send booking request</span></button>
        <p class="book__sent" data-send-msg role="status" aria-live="polite"></p>
      </form>
    </aside>
  </div>
</section>"""


# Core massages first on catalog cards, so a card never opens with "Wife for rent"
CORE = ["Tantra Massage", "Body to Body Massage", "Nuru Massage", "Erotic Massage", "Sensual Massage", "Oriental Massage",
       "Thai Massage", "Deep tissue massage", "Shiatsu Massage", "Feet body massage"]


def facets(g):
    """data-* the catalog filter reads: orientation, cup, figure, nationality, age group, massage for."""
    P = g["params"]
    age = int(P.get("Age") or 0)
    who = {w for w, keys in (("men", ("man", "men")), ("women", ("woman", "women")), ("couples", ("couple",)))
           if any(k in re.split(r"[ ,]+", P.get("Massage for", "").lower()) for k in keys) or (w == "couples" and "couple" in P.get("Massage for", "").lower())}
    f = {"orient": "bisexual" if "bi" in P.get("Orientation", "").lower() else "heterosexual", "cup": P.get("Cup size", ""),
         "figure": P.get("Build", "").lower(), "nat": P.get("Nationality", ""), "age": "21-30" if age <= 30 else "31-40" if age <= 40 else "mature",
         "for": " ".join(sorted(who))}
    return "".join(f' data-{k}="{e(v)}"' for k, v in f.items() if v)


def gcard(g):
    """Catalog card: photo, name and tier, then the facts a client scans first and three of her massages."""
    P = g["params"]
    meta = " · ".join(x for x in (P.get("Age") and f'{P["Age"]} y.o.', P.get("Nationality"), P.get("Height", "").replace("cm", " cm")) if x)
    cup = f'<span class="card__cup"> · Cup {e(P["Cup size"])}</span>' if P.get("Cup size") else ""
    where = " · ".join(t for t, k in (("Incall", "incall"), ("Outcall", "outcall")) if g[k])
    svc = sorted(g["services"], key=lambda x: CORE.index(x) if x in CORE else len(CORE))[:2]
    more = len(g["services"]) - len(svc)
    tags = "".join(f"<li>{e(x.replace(' Massage', '').replace(' massage', ''))}</li>" for x in svc) + (f'<li class="card__more">+{more}</li>' if more > 0 else "")
    return (f'<a class="card card--g" href="girl-{g["slug"]}.html"{facets(g)}><figure><img src="img/g-{g["slug"]}-0.webp" alt="{e(g["name"])}" sizes="(max-width: 720px) 46vw, 18vw" loading="lazy"></figure>'
            f'<span class="card__title">{e(g["name"])}</span><span class="card__vip">{e(g["tier"].upper())}</span>'
            f'<span class="card__meta">{e(meta)}{cup}</span>'
            + (f'<span class="card__where">{e(where)}</span>' if where else "")
            + (f'<ul class="card__tags">{tags}</ul>' if svc else "") + '</a>')


def girls(names):
    return (f'<div class="cgrid cgrid--g">{"".join(gcard(GIRL[n]) for n in names if n in GIRL)}</div>'
            f'<div class="cgrid__foot"><a class="btn btn--line" href="masseuses.html">All masseuses ({len(GIRLS)}){icon("right")}</a></div>')


def article(block, images):
    out, sec = [], None

    def close():
        if sec:
            h, body = sec
            img = images.get(h)
            fig = f'<figure class="chapter__img"><img src="img/{img}.webp" alt="" sizes="(max-width: 720px) 92vw, 46vw" loading="lazy"></figure>' if img else ""
            out.append(f'<details class="chapter"><summary><h2 class="chapter__title">{e(h)}</h2><span class="chapter__toggle" aria-hidden="true"></span></summary>'
                       f'<div class="chapter__grid">{fig}<div class="chapter__body">{"".join(body)}</div></div></details>')

    for l in block:
        if l.startswith("## "):
            close()
            sec = (l[3:], [])
        elif l.startswith("###"):
            sec[1].append(f"<h3>{e(l.lstrip('# '))}</h3>")
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
            out.append(f'<details class="faq__item" open><summary>{e(q)}</summary><p>{e(l)}</p></details>')
            q = None
    # Answers are open from the start; the left column carries the contacts, so the block has no empty half
    return f'''<section class="sect faq" data-tone="noir">
  <img class="sect__bg" src="img/v-faq-bg.webp" alt="" sizes="(max-width: 720px) 100vw, 36vw" loading="lazy" decoding="async">
  <div class="faq__side"><h2 class="h2">FAQ</h2><p class="lead">Call, write, we are waiting for you!</p>
    <div class="faq__cta"><a class="btn btn--gold" href="tel:+33758963765">{icon("phone")}+33 7 58 96 37 65</a>
      <a class="btn btn--line" href="https://wa.me/33758963765">{icon("chat")}Call by Whatsapp</a>
      <a class="btn btn--line" href="mailto:erotic.sweettouch@gmail.com">{icon("mail")}erotic.sweettouch@gmail.com</a></div></div>
  <div class="faq__list">{"".join(out)}</div>
</section>'''


ICON = {  # Lucide-style line icons
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
    "chat": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/>',
    "calendar": '<rect x="3" y="4.5" width="18" height="17" rx="2"/><path d="M16 2.5v4M8 2.5v4M3 10h18"/>',
    "send": '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
    "left": '<path d="M19 12H5"/><path d="m12 19-7-7 7-7"/>',
    "right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "down": '<path d="m6 9 6 6 6-6"/>',
    "out": '<path d="M7 17 17 7"/><path d="M7 7h10v10"/>',
}
MAIN = [("Our masseuses", "masseuses.html", "b-katlin-2"), ("Massages & prices", "massages.html", "b-leya-3"),
        ("Paris locations", "paris-locations.html", "b-alina-0"), ("Erotic Massage in France", "erotic-massage-in-france.html", "b-eva-0"),
        ("Job offers", "job-offers.html", "b-lily-0"), ("Fidelity Card", "fidelity-card.html", "b-katlin-0")]
# Header dropdown: Tantra has its own page, the rest open the full price list at their card
SUB_SLUG = {"Tantric Massage": "tantra", "Prostate massage": "prostate", "Domination massage": "domination", "Erotic Chat with the Masseuse": "chat"}
def SUB_HREF(s):
    return mfile(s) or f"massages.html#m-{SUB_SLUG.get(s) or SLUG.get(s, '')}"
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
    sub = "".join(f'<li><a href="{SUB_HREF(s)}">{s}</a></li>' for s in SUB)
    big = "".join(f'<li><a class="drawer__big" href="{u}" data-img="img/{im}.webp"><span class="drawer__t">{e(t)}</span></a></li>'
                  for t, u, im in MAIN)
    msub = "".join(f'<li><a href="{SUB_HREF(s)}">{e(s)}</a></li>' for s in SUB)
    links = "".join(f'<div class="nav__dd"><a href="{u}">{e(t)}{icon("down")}</a><ul class="nav__sub">{msub}</ul></div>' if u == "massages.html"
                    else f'<a href="{u}">{e(t)}</a>' for t, u, _ in MAIN)
    return f'''<header class="nav" data-nav>
  <button class="nav__menu" data-burger aria-expanded="false" aria-controls="drawer"><span class="burger" aria-hidden="true"><i></i><i></i></span><span class="nav__menu-label">Menu</span></button>
  <a class="nav__logo" href="index.html"><img src="img/logo.svg" alt="SweetTouch" width="138" height="42"></a>
  <nav class="nav__links" aria-label="Main">{links}</nav>
  <div class="nav__right">
    <a class="nav__phone" href="tel:+33758963765">{icon("phone")}+33 7 58 96 37 65</a>
    <a class="nav__icon nav__icon--call" href="tel:+33758963765" aria-label="+33 7 58 96 37 65" title="+33 7 58 96 37 65">{icon("phone")}</a>
    <a class="nav__icon" href="https://wa.me/%2B33758963765" aria-label="Call by Whatsapp" title="Call by Whatsapp">{icon("chat")}</a>
    <a class="nav__icon" href="mailto:erotic.sweettouch@gmail.com" aria-label="erotic.sweettouch@gmail.com" title="erotic.sweettouch@gmail.com">{icon("mail")}</a>
    {lang_switch()}
    <a class="btn btn--gold btn--nav" href="contact.html">Make a booking</a>
  </div>
</header>
<div class="drawer" id="drawer" data-drawer hidden>
  <figure class="drawer__img" aria-hidden="true"><img src="img/menu-bg.webp" alt="" loading="lazy"></figure>
  <nav class="drawer__main" aria-label="Main"><ol>{big}</ol></nav>
  <div class="drawer__side">
    <div><p class="drawer__label">Massages &amp; prices</p><ul class="drawer__sub">{sub}</ul></div>
    <div class="drawer__contact">
      <a class="drawer__phone" href="tel:+33758963765">+33 7 58 96 37 65</a>
      <a class="drawer__chip" href="https://wa.me/%2B33758963765">{icon("chat")}Call by Whatsapp</a>
      <a class="btn drawer__book" href="contact.html">{icon("calendar")}Book a massage</a>
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


FOOT_ICON = {"Contact us": "contact", "FAQ": "faq", "Terms and Conditions": "terms", "DMCA policy": "dmca", "Blog": "blog", "Partners": "partners", "Sitemap": "sitemap"}
SOC_ICON = {"Twitter": "twitter", "YouTube": "youtube", "Pinterest": "pinterest", "Instagram": "inst", "Facebook": "facebook"}


def marquee(text):
    """Big running title (the client asked for it back): the real heading stays for readers and search engines."""
    dot = '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M5 0 10 5 5 10 0 5z"/></svg>'
    run = "".join(f"<span>{e(text)}</span>{dot}" for _ in range(4))
    return f'<h2 class="sr-only">{e(text)}</h2><div class="marq" aria-hidden="true"><div class="marq__track">{run}{run}</div></div>'


def footer():
    fi = lambda k: f'<svg class="fi" aria-hidden="true"><use href="img/foot-icons.svg#icon-{k}"/></svg>'
    links = "".join(f'<a href="{po.local("https://sweettouch.fr/" + u, GSLUGS)}">{fi("footer-" + FOOT_ICON.get(t, "about"))}{t}</a>' for t, u in FOOT_LINKS)
    soc = "".join(f'<a href="{u}" aria-label="{t}"><img src="img/soc-{SOC_ICON[t]}.svg" alt="" width="32" height="32"><span>{t}</span></a>' for t, u in SOCIAL)
    return f'''<footer class="foot" data-tone="noir">
  <div class="foot__top">
    <div><a class="foot__logo" href="index.html"><img src="img/logo.svg" alt="SweetTouch" width="138" height="42" loading="lazy"></a><p class="foot__muted">You can find us</p><div class="foot__soc">{soc}</div></div>
    <div class="foot__links">{links}</div>
    <address class="foot__contact"><a href="tel:+33758963765">{fi("phone-call")}+33 7 58 96 37 65</a><a href="https://wa.me/%2B33758963765">{fi("whatsapp")}WhatsApp +33 7 58 96 37 65</a>
      <a href="mailto:erotic.sweettouch@gmail.com">{fi("contact-mail")}erotic.sweettouch@gmail.com</a><a href="https://goo.gl/maps/CbB6k75MipvzVnVbA">{fi("map-marker")}Avenue de Wagram 75017</a></address>
  </div>
  <div class="foot__bottom"><span>We do not offer any kind of sexual services.</span><span class="foot__credit">Designed &amp; developed by <b>NextWeb</b></span></div>
</footer>'''


def hero(words, label, imgs, after, cls="", fs=(0.165, 0.205), video=None, lh=None):
    """Vector hero: the word is an SVG mask over full-resolution photos, so scaling it stays sharp.
    main.js sizes the viewBox to the viewport and lays out the lines (fs = font size as share of width, desktop/mobile).
    video: looped full-screen clip under solid letters; imgs[0] is its poster while it loads."""
    texts = "".join(f'<text text-anchor="middle">{e(w)}</text>' for w in words)
    vid = f'<video class="hx__src" data-src="video/{video}.mp4" data-src-m="video/{video}-m.mp4" data-poster="img/{imgs[0]}.webp" data-poster-m="img/{imgs[0]}-m.webp" muted loop playsinline preload="none" aria-hidden="true"></video>' if video else ""
    images = "".join(f'<image class="hx__img{" is-on" if i == 0 else ""}" href="img/{s}.webp" preserveAspectRatio="xMidYMid slice"/>' for i, s in enumerate(imgs))
    return f'''<section class="hx {cls}{" hx--video" if video else ""}" data-hx>
  <div class="hx__pin">
    <h1 class="sr-only">{e(label)}</h1>
    {vid}
    <svg class="hx__svg" data-fs="{fs[0]}" data-fs-m="{fs[1]}"{f' data-lh="{lh}"' if lh else ""} aria-hidden="true">
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
<div class="glow" aria-hidden="true"></div>
<div class="thread" aria-hidden="true"><span></span></div>
{nav()}
<nav class="mbar" aria-label="Quick contact">
  <a href="tel:+33758963765" aria-label="+33 7 58 96 37 65">{icon("phone")}Call</a>
  <a href="https://wa.me/33758963765" aria-label="Call by Whatsapp">{icon("chat")}WhatsApp</a>
  <a class="mbar__book" href="contact.html">Make a booking</a>
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
    adv_img = ["v-adv-premium", "v-adv-private", "v-adv-techniques", "v-adv-fast", "v-adv-real"]  # Seedream 5.5 set in the client's chosen style (11.11), same order as the advantages
    layers = "".join(f'<div class="stage__layer"><img src="img/{i}.webp" alt="" sizes="(max-width: 720px) 92vw, 50vw" loading="lazy" decoding="async"></div>' for i in adv_img)
    texts = "\n".join(f'<article class="stage__text"><img class="stage__ph" src="img/{i}.webp" alt="" loading="lazy" decoding="async"><h2>{e(a)}</h2><p class="stage__sub">{e(b)}</p><p>{e(c)}</p><a class="link" href="#">{e(d)}</a></article>'
                      for (a, b, c, d), i in zip(advs, adv_img))
    steps_html = "\n".join(f'<li class="step"><span class="step__n">{e(n)}</span><h3>{e(t)}</h3><p>{e(p)}</p></li>' for n, t, p in steps)
    cities = ["madrid", "marbella", "mallorca", "ibiza", "amsterdam", "rome", "milan", "london", "courchevel", "aix"]
    posts_html = [f'<a class="card card--b" href="#"><figure><img src="img/{c}.webp" alt="" loading="lazy"></figure><time>{e(d)}</time><h3 class="card__title">{e(t)}</h3><p>{e(x)}</p><span class="link">read more</span></a>'
                  for (t, d, x, _), c in zip(posts, cities)]

    body = f'''{hero(["Erotic", "Massage"], "Erotic Massage in Paris", ["hero-poster"], after, video="hero")}

<section class="sect massages" id="massages" data-tone="noir">
  {marquee("Massages & prices")}
  {massages_grid(rows)}
</section>

<section class="sect girls" id="girls" data-tone="noir">
  {marquee("Gallery of masseuses")}
  {girls(names)}
</section>

{book(names, rows, f'<p class="book__note"><b>{e(inc_h)}.</b> {e(inc_p)}</p>')}

<section class="sect about" data-tone="wine">
  <div class="about__text"><h2 class="h2">About SweetTouch</h2><p class="lead">Relive the unique experience of sensual intimate massage with SweetTouch!</p><p class="about__p" data-highlight>{e(about)}</p></div>
  <figure class="about__img" data-parallax><img src="img/v-about.webp" alt="" sizes="(max-width: 720px) 92vw, 46vw" loading="lazy"></figure>
</section>

<section class="stage is-static" data-stage data-tone="noir" aria-label="Why SweetTouch">
  <div class="stage__pin">
    <div class="stage__media">{layers}</div>
    <div class="stage__texts"><h2 class="h2 stage__title">Benefits of SweetTouch</h2>{texts}</div>
  </div>
</section>


<section class="sect how" data-tone="noir">
  <img class="sect__bg" src="img/v-how-bg.webp" alt="" sizes="(max-width: 720px) 100vw, 46vw" loading="lazy" decoding="async">
  <h2 class="h2">How it works</h2>
  <p class="how__intro">{e(hw_intro)}</p>
  <ol class="steps">{steps_html}</ol>
</section>

<section class="sect blog" data-tone="noir">
  <h2 class="h2">Blog</h2>
  {rail(posts_html, "Blog", auto=True)}
</section>

{faq(fq)}
<aside class="promo" aria-label="Make a booking"><img src="img/z-bg-how.webp" alt="" loading="lazy" decoding="async"><a class="btn" href="contact.html">Make a booking</a></aside>
<!-- SEO copy: kept 1:1, folded into closed chapters just above the footer -->
<section class="sect articles seo" data-tone="wine" data-seo>
<div class="seo__body">
{article(art, {"What Is SweetTouch Erotic Massage? A Journey Beyond Relaxation": "old-sensual", "Our Exclusive Erotic Massage Services in Paris": "old-couple",
               "Discover Our Special, One-of-a-Kind Offers!": "old-erotic", "Meet Our Masseuses: The Heart of SweetTouch": "old-massage"})}
</div>
<button class="more seo__toggle" type="button" data-seo-toggle aria-expanded="false">Show all</button>
</section>
{footer()}'''
    return page(L[0], intro[:155], body)


def home_rows():
    L = lines("page_.txt")
    return services(between(L, "## Massages", "## We Invite You to SweetTouch for the Best Erotic Massage in Paris"))


def phead(title, crumbs, sub="", img=None):
    trail = " / ".join([*(f'<a href="{u}">{e(t)}</a>' for t, u in crumbs), f"<span>{e(title)}</span>"])
    sub = f'<p class="phead__sub">{e(sub)}</p>' if sub else ""
    bg = f'<img class="phead__bg" src="img/{img}.webp" alt="" sizes="100vw" fetchpriority="high">' if img else ""
    return (f'<header class="sect phead{" phead--img" if img else ""}" data-tone="wine">{bg}<nav class="crumbs" aria-label="Breadcrumb">{trail}</nav>'
            f'<h1 class="phead__h">{e(title)}</h1>{sub}</header>')


def build_massages():
    groups = "\n".join(f'<section class="sect massages" data-tone="noir">{"" if i == 0 else f"<h2 class=\"h2 h2--m\">{e(t)}</h2>"}'
                       f'<div class="cgrid cgrid--m">{"".join(mcard(n, p) for n, p in g)}</div></section>'
                       for i, ((t, _), g) in enumerate(zip(GROUPS, group_rows(home_rows()))))
    body = f'''{phead("Massages & prices", [("SweetTouch", "index.html")])}
{groups}
{footer()}'''
    return page("Erotic Massages & Prices in Paris - SweetTouch", "All erotic massages of SweetTouch in Paris with prices for every duration.", body)


def filters():
    """Old-site fast filter as one horizontal strip of dropdowns; main.js shows the cards that match every chosen group."""
    from collections import Counter
    groups = [("Orientation", "orient", ["heterosexual", "bisexual"]), ("Breast size", "cup", ["A", "B", "C", "D"]),
              ("Figure", "figure", ["athletic", "normal", "slim"]),
              ("Nationality", "nat", sorted(Counter(g["params"].get("Nationality") for g in GIRLS if g["params"].get("Nationality")))),
              ("Age", "age", ["21-30", "31-40", "mature"]), ("Massage for", "for", ["men", "women", "couples"])]
    dd = "".join(f'<details class="fdd{" fdd--hot" if k in ("cup", "age") else ""}"><summary>{t}<span class="fdd__n" data-n></span>{icon("down")}</summary><div class="fdd__list" data-lenis-prevent>'
                 + "".join(f'<label><input type="checkbox" name="{k}" value="{e(v)}"><span>{e(v.capitalize() if k != "cup" else v)}</span></label>' for v in vals)
                 + "</div></details>" for t, k, vals in groups)
    return (f'<div class="fstrip" data-filter><div class="fstrip__head"><b>Filters</b><button type="button" class="fstrip__x" data-sheet-close aria-label="Close">{icon("down")}</button></div>'
            f'<button type="button" class="fstrip__all" data-sheet-open>All filters<span class="fdd__n" data-total></span></button>'
            f'<span class="fstrip__label">Fast filter</span>{dd}'
            f'<span class="fstrip__count" data-count>{len(GIRLS)} masseuses</span><button type="button" class="link" data-reset hidden>Reset</button>'
            f'<button type="button" class="btn btn--gold fstrip__show" data-sheet-close>Show <span data-count-n>{len(GIRLS)}</span> masseuses</button></div>')


def build_masseuses():
    L = lines("page_girl.txt")
    body = f'''{phead(L[L.index("# Paris Luxury Sweet Girls")][2:], [("SweetTouch", "index.html")], "Best selection of sexy masseuses in Paris & France")}
<section class="sect girls" data-tone="noir">{filters()}<div class="cgrid cgrid--g" data-cards>{"".join(gcard(g) for g in GIRLS)}</div>
  <p class="fstrip__none" data-none hidden>No masseuse matches these filters. <button type="button" class="link" data-reset>Reset filters</button></p></section>
{footer()}'''
    return page(L[0], "Best selection of sexy masseuses in Paris & France", body)


def build_girl(g, rows):
    """Profile: every photo in a column on the left, name, booking and facts on the right; then locations, hours, services."""
    from urllib.parse import quote
    price, n, P = dict(rows), g["name"], g["params"]
    pics = "".join(f'<figure class="prof__pic"><img src="img/g-{g["slug"]}-{i}.webp" alt="{e(n)}" sizes="(max-width: 720px) 92vw, 46vw"{"" if i == 0 else " loading=\"lazy\""}></figure>'
                   for i in range(len(g["files"])))
    facts = "".join(f"<div><dt>{e(k)}</dt><dd>{e(re.sub(r",\s*", ", ", v))}</dd></div>" for k, v in P.items())
    DAYS = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}
    hours = "".join(f"<div><dt>{DAYS.get(d, d)}</dt><dd>{e(h)}</dd></div>" for d, h in g["hours"].items())

    def tile(x):
        dl = "".join(f"<div><dt>{e(dur(d))}</dt><dd>{p} €</dd></div>" for d, p in price[x])
        head = f'<h3 class="ptile__h">{e(x)}</h3>'
        href = mfile(x)
        return f'<li class="ptile">{f"<a href=\"{href}\">{head}</a>" if href else head}<dl class="card__prices">{dl}</dl></li>'
    svc = f'<ul class="ptiles">{"".join(tile(x) for x in g["services"] if x in price)}</ul>'
    others = [x for x in GIRLS if x is not g][:5]
    wa = "https://wa.me/33758963765?text=" + quote(f"Hello SweetTouch! I would like to book a massage with {n}.")
    about = "".join(f'<p class="prof__about">{e(a)}</p>' for a in g["about"])
    locs = '<div class="facts facts--loc"><div><dt>Base city</dt><dd>Paris</dd></div></div>' + "".join(
        f'<h3 class="prof__h3">{t}</h3><ul class="plain plain--links">{"".join(f"<li><a href=\"paris-locations.html\">{e(x)}</a></li>" for x in g[k])}</ul>'
        for t, k in (("Incall locations", "incall"), ("Outcall locations", "outcall")) if g[k])
    body = f'''<section class="sect prof" data-tone="wine">
  <div class="prof__pics">{pics}</div>
  <div class="prof__info">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">SweetTouch</a> / <a href="masseuses.html">Masseuses</a> / <span>{e(n)}</span></nav>
    <h1 class="phead__h">{e(n)}</h1>
    <p class="prof__key"><span class="card__vip">{e(g["tier"].upper())}</span>{e(P["Age"])} y.o. · {e(P["Height"])} · {e(P["Nationality"])}</p>
    <div class="prof__cta"><a class="btn btn--gold" href="index.html?girl={g["slug"]}#book">Book with {e(n)}</a><a class="btn btn--line" href="{e(wa)}">{icon("chat")}WhatsApp</a></div>
    <div class="ptabs">
      <input type="radio" name="ptab" id="ptab-a" checked><label for="ptab-a">{e(n)}</label>
      <input type="radio" name="ptab" id="ptab-b"><label for="ptab-b">Location</label>
      <dl class="facts ptabs__a">{facts}</dl>
      <div class="ptabs__b">{locs}</div>
    </div>
  </div>
</section>
<section class="sect prof2" data-tone="noir">
  <div><h2 class="h2 h2--m">Working hours</h2><dl class="facts facts--hours">{hours}</dl></div>
  <div><h2 class="h2 h2--m">About {e(n)}</h2>{about}</div>
</section>
<section class="sect" data-tone="noir"><h2 class="h2 h2--m">{e(n)} provides</h2>{svc}</section>
<section class="sect girls" data-tone="wine"><h2 class="h2 h2--m">Other masseuses</h2>
  <div class="cgrid cgrid--g">{"".join(gcard(x) for x in others)}</div>
  <div class="cgrid__foot"><a class="btn btn--line" href="masseuses.html">All masseuses ({len(GIRLS)}){icon("right")}</a></div></section>
{footer()}'''
    return page(f"{n} - erotic masseuse in Paris - SweetTouch", (g["about"] or [n])[0][:155], body)


GSLUGS = {g["slug"] for g in GIRLS}
INFOS = {sl: po.parse_info(sl, services) for sl in po.INFO_SLUGS}
find_info = po.name_to_slug(INFOS)
# Order of the massage menu: the price list order first, then the pages it does not list
MORDER = list(dict.fromkeys([find_info(n) for n, _ in home_rows() if find_info(n)] + po.INFO_SLUGS))


def ptable(rows, note=""):
    outc = any(len(r) > 2 for r in rows)
    cell = lambda p: (f"<b>{e(p)} €</b>" if p.isdigit() else '<b class="dim">—</b>') if p else '<b class="dim">only incall</b>'
    head = '<div class="ptable__row ptable__head"><span>Duration</span><span>Incall</span>' + ('<span>Outcall</span>' if outc else "") + "</div>"
    body = "".join(f'<div class="ptable__row"><span>{e(r[0])}</span>{"".join(cell(p) for p in r[1:])}</div>' for r in rows)
    return (f'<div class="ptable{"" if outc else " ptable--2"}">{head}{body}' + (f'<p class="ptable__note">* {e(note)}</p>' if note else "")
            + '<a class="btn" href="#book">Book online</a></div>')


def build_info(d):
    """Massage page in the client's order: video with the prices on the first screen, prices, who provides it, other massages, FAQ, a booking call to action (one price table only); the SEO text last."""
    name, sl = d["name"], d["slug"]
    short = {"4 hands massage with lesbian show": "Lesbian Show", "Erotic Chat with the Masseuse": "Erotic Chat"}.get(name) or re.sub(r"\s*massage$", "", name, flags=re.I) or name
    words, cur = [], ""
    for w in short.split():
        if cur and len(cur) + 1 + len(w) > 11:
            words.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    words.append(cur)
    longest = max(len(w) for w in words)
    vid = f"massage-{sl}" if (ROOT / "public" / "video" / f"massage-{sl}.mp4").exists() else None
    check_svg = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    checks = f'<ul class="checks">{"".join(f"<li>{check_svg}{e(c)}</li>" for c in d["checks"])}</ul>' if d["checks"] else ""
    outs = [int(r[2]) for r in d["rows"] if len(r) > 2 and (r[2] or "").isdigit()]  # some pages put "-" for "no outcall"
    quick = ('<dl class="hx__prices">' + "".join(f"<div><dt>{e(r[0])}</dt><dd>{e(r[1])} €</dd></div>" for r in d["rows"] if len(r) > 1 and (r[1] or "").isdigit()) + "</dl>"
             + f'<p class="hx__pnote">Incall prices{f" · outcall from {min(outs)} €" if outs else ""}</p>') if d["rows"] else ""
    after = f"""<div class="hx__after">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">SweetTouch</a> / <a href="massages.html">Massages &amp; prices</a> / <span>{e(name)}</span></nav>
      {checks}
      <div class="hx__mprices">{quick}</div>
      <a class="btn" href="contact.html">Book online</a>
    </div>
    <div class="hx__side">{quick}</div>"""
    team = ([n for n in d["team"] if n in GIRL] or [g["name"] for g in GIRLS if name in g["services"]] or [g["name"] for g in GIRLS])[:5]  # one row of five
    intro = next((l for l in d["art"] if not l.startswith("#")), "")
    body = f"""{hero(words, name, [f"pv-{sl}" if vid else f"p-{sl}" if (ROOT / "public" / "img" / f"p-{sl}.webp").exists() else f"o-{mimg(name)}"], after, "hx--short", (min(0.24, 1.45 / longest), min(0.27, 1.4 / longest)), video=vid, lh=0.98)}
<section class="sect split split--dark" data-tone="wine">
  <div><h2 class="h2 h2--m">Duration &amp; prices</h2>{checks.replace('class="checks"', 'class="checks checks--m"')}{f"<p>{e(intro)}</p>" if intro else ""}</div>
  {ptable(d["rows"], d["note"])}
</section>
<section class="sect girls" data-tone="noir">
  <h2 class="h2 h2--m">Who provides {e(name)}</h2>
  {girls(team)}
</section>
{f'<section class="sect massages" id="massages" data-tone="noir"><h2 class="h2 h2--m">Other erotic massage services</h2>{rail([mcard(n, p) for n, p in d["others"]], "Other erotic massage services")}</section>' if d["others"] else ""}
{faq(d["faq"]) if d["faq"] else ""}
<section class="sect split split--dark book book--cta" data-tone="wine">
  <h2 class="book__title">{e(name)}</h2>
  <p class="prose__cta"><a class="btn btn--gold btn--xl" href="contact.html">{icon("calendar")}Book online</a><a class="btn btn--line btn--xl" href="https://wa.me/33758963765">{icon("chat")}WhatsApp</a></p>
</section>
{f'<section class="sect articles" data-tone="noir">{article(d["art"], {})}</section>' if d["art"] else ""}
{footer()}"""
    return page(d["title"], (intro or name)[:155], body)


def build_text(sl):
    """Secondary page from the old site, text 1:1: headings, paragraphs, lists, links, plus the blocks some pages have
    (district tiles, blog posts, reviews, questions, masseuse lists)."""
    it = po.raw_items(f"pages/{sl}.txt")
    h1 = next(i for i, (t, _) in enumerate(it) if t.startswith("# "))
    end = next((i for i, (t, _) in enumerate(it) if t == "You can find us"), len(it))
    if sl == "faq":
        end = min(end, next((i for i, (t, u) in enumerate(it) if t == "Leave a Reply" and not u), end))
    if sl == "job-offers":
        end = min(end, next((i for i, (t, _) in enumerate(it) if t.startswith("### Apply")), end) + 2)
    it = it[h1:end]
    title = it[0][0][2:]
    out, k, grp = [], 1, None
    DATE_EU, DATE_US = re.compile(r"^\d{2}\.\d{2}\.\d{4}$"), re.compile(r"^[A-Z][a-z]+ \d{1,2}, \d{4}$")

    def emit(kind, html_):
        nonlocal grp
        wrap = {"tile": "dtiles", "quote": "quotes", "post": "posts", "chip": "links", "li": "prose__ul", "qa": "prose__qa"}
        if kind != grp:
            if grp in wrap:
                out.append(f"</{'ul' if grp in ('chip', 'li') else 'div'}>")
            if kind in wrap:
                out.append(f'<{"ul" if kind in ("chip", "li") else "div"} class="{wrap[kind]}">')
            grp = kind
        out.append(html_)

    href = lambda u: e(po.local(u, GSLUGS))
    names, after_colon = [], False
    while k < len(it):
        t, u = it[k]
        nxt = it[k + 1][0] if k + 1 < len(it) else ""
        if t in ("\\", "") and u and u.startswith("http") and "sweettouch.fr" not in u:  # logo-only partner link (sweettouch.es)
            dom = u.split("//")[-1].strip("/")
            emit("cta", f'<p class="prose__cta"><a class="btn btn--gold btn--xl" href="{e(u)}" rel="noopener">{e(dom.replace("sweettouch", "SweetTouch"))}</a></p>')
            k += 1; continue
        if ((u or "").startswith("#") or not t and not u or t in ("\\", "##", "vip", "silver") or t.endswith(" *") or t == "Yes No"
                or re.fullmatch(r"(www\.)?sweettouch\.fr/?", (t or (u or "").split("//")[-1]).strip())):
            k += 1; continue
        if re.fullmatch(r"\d+( \d+)* … \d+", t):
            emit("post", f'<a class="post post--more" href="https://sweettouch.fr/blog/page/2"><span>More articles</span>{icon("right")}</a>')  # last tile of the grid
            k += 1; continue
        if t.startswith("girl_video"):
            if k + 2 < len(it) and it[k + 2][0] in GIRL:
                names.append(it[k + 2][0])
            k += 3; continue
        if names:
            emit("girls", girls(names)); names = []
        if t.startswith("#"):
            lvl = min(len(t) - len(t.lstrip("#")), 3)
            emit("h", f'<h{lvl} class="prose__h{lvl}">{e(po.fix_head(t).lstrip("# "))}</h{lvl}>'); after_colon = False
        elif DATE_EU.match(it[k + 2][0] if k + 2 < len(it) else ""):
            emit("quote", f'<figure class="quote"><blockquote>{e(t)}</blockquote><figcaption>{e(nxt)}<span>{e(it[k + 2][0])}</span></figcaption></figure>'); k += 2
        elif DATE_US.match(nxt):
            ex = it[k + 2][0] if k + 2 < len(it) and not it[k + 2][0].startswith("read more") else ""
            city = next((c for c in ("madrid", "marbella", "mallorca", "ibiza", "amsterdam", "rome", "milan") if c in t.lower()), None)
            cover = f'<figure class="post__img"><img src="img/p-blog-{city}.webp" alt="" loading="lazy"></figure>' if city else ""
            emit("post", f'<a class="post" href="{href(u)}">{cover}<div class="post__body"><time>{e(nxt)}</time><h3>{e(t)}</h3><p>{e(ex)}</p><span>Read more</span></div></a>')
            k += 1 + (1 if ex else 0) + (1 if k + 3 < len(it) and it[k + 3][0].startswith("read more") else 0)  # date, excerpt, read more (the loop adds the last step)
        elif re.match(r"^\d+ girls?$", nxt) and it[k + 1][1]:
            emit("tile", f'<a class="dtile" href="{href(it[k + 1][1])}"><span>{e(t)}</span><b>{e(nxt)}</b></a>'); k += 1
        elif t.endswith("?") and not u and len(nxt) > 60 and not nxt.startswith("#"):
            emit("qa", f'<details class="faq__item" open><summary>{e(t)}</summary><p>{e(nxt)}</p></details>'); k += 1
        elif u and len(t) < 70:
            if t.lower().startswith("buy "):
                emit("btn", f'<p class="prose__cta"><a class="btn btn--gold btn--xl" href="{href(u)}">{icon("chat")}{e(t)}</a></p>')
            elif t.lower().startswith(("book online", "view all")):
                emit("btn", f'<p><a class="btn btn--line" href="{href(u)}">{e(t)}</a></p>')
            else:
                emit("chip", f'<li><a href="{href(u)}">{e(t or u.split("//")[-1].strip("/"))}</a></li>')
        elif after_colon and len(t) < 160 and not t.endswith(":"):
            emit("li", f"<li>{e(t)}</li>")
        else:
            emit("p", f"<p>{e(t)}</p>")
            after_colon = t.endswith(":")
        if t.endswith(":") and not t.startswith("#"):
            after_colon = True
        k += 1
    if names:
        emit("girls", girls(names))
    emit(None, "")
    extra = ""
    if sl == "job-offers":
        extra = job_form()
    img = f"p-hdr-{sl}" if (ROOT / "public" / "img" / f"p-hdr-{sl}.webp").exists() else None
    inner = (f'<div class="jobgrid"><div class="prose__in">{"".join(out)}</div><aside class="jobgrid__form" data-sticky-side>{extra}</aside></div>'
             if sl == "job-offers" else f'<div class="prose__in">{"".join(out)}{extra}</div>')
    body = f"""{phead(title, [("SweetTouch", "index.html")], img=img)}
<section class="sect prose" data-tone="noir">{inner}</section>
{footer()}"""
    return page(it[0][0][2:] + " - SweetTouch", title, body)


def job_form():
    """Application form as on sweettouch.fr/job-offers; main.js shrinks the photos and posts everything to /api/job."""
    f = lambda nm, lab, t="text": f'<label class="jf__f"><span>{lab} *</span><input name="{nm}" type="{t}" required></label>'
    fields = "".join(f(*x) for x in (("name", "Name"), ("age", "Age", "number"), ("country", "Country"), ("city", "City"),
                                      ("languages", "Languages spoken"), ("dress", "Dress size"), ("phone", "Phone number", "tel"),
                                      ("email", "Email", "email"), ("whatsapp", "WhatsApp"), ("instagram", "Instagram")))
    return f"""<form class="jf" data-job novalidate>
  <div class="jf__grid">{fields}</div>
  <fieldset class="jf__q"><legend>Do you own a private location to provide in-call massages?</legend>
    <label><input type="radio" name="location" value="Yes"> Yes</label><label><input type="radio" name="location" value="No"> No</label></fieldset>
  <label class="jf__c"><input type="checkbox" name="outcall_only" value="Yes"> I want to work with you only outcall</label>
  <label class="jf__f jf__f--wide"><span>Describe your experience *</span><textarea name="experience" rows="5" required></textarea></label>
  <label class="jf__f jf__f--wide jf__file"><span>Download recent photos *</span><input name="photos" type="file" accept="image/*" multiple required>
    <small>Required photos: 1. Selfie 2. Full height in underwear 3. Professional photos (if you have them)</small></label>
  <label class="jf__c"><input type="checkbox" name="escort" value="Yes"> I want to work with you as escort companion</label>
  <input name="website" tabindex="-1" autocomplete="off" aria-hidden="true" class="book__hp">
  <button class="btn btn--gold" type="submit"><span data-job-label>Send application</span></button>
  <p class="book__sent" data-job-msg role="status" aria-live="polite"></p>
</form>
<div class="jf__contacts"><h3 class="prose__h3">Contact information</h3>
  <ul class="links"><li><a href="tel:+33758963765">Phone +33 7 58 96 37 65</a></li><li><a href="https://wa.me/33758963765">WhatsApp +33 7 58 96 37 65</a></li>
  <li><a href="viber://add?number=+33758963765">Viber +33 7 58 96 37 65</a></li><li><a href="mailto:erotic.sweettouch@gmail.com">erotic.sweettouch@gmail.com</a></li></ul></div>"""


def build_contact():
    """The old site's booking form (contact page), incall or outcall; main.js posts it to /api/contact."""
    cities = json.loads((CONTENT / "cities.json").read_text(encoding="utf-8"))
    opt = lambda vals, first="": (f'<option value="">{first}</option>' if first else "") + "".join(f'<option>{e(v)}</option>' for v in vals)
    sel = lambda nm, lab, vals, first="Choose": f'<label class="jf__f"><span>{lab} *</span><select name="{nm}" required>{opt(vals, first)}</select></label>'
    inp = lambda nm, lab, t="text", req=True, cls="": f'<label class="jf__f{cls}"><span>{lab}{" *" if req else ""}</span><input name="{nm}" type="{t}"{" required" if req else ""}></label>'
    durs = ["30 min", "1 hr", "1 hr 30 min", "2 hr", "3 hr", "6 hr", "12 hr"]
    form = f"""<form class="jf bform" data-contact novalidate>
  <div class="bform__type"><label><input type="radio" name="type" value="Incall" checked><span>Incall</span></label><label><input type="radio" name="type" value="Outcall"><span>Outcall</span></label></div>
  <div class="jf__grid">
    {sel("girl", "I would like to book", [g["name"] for g in GIRLS])}
    {sel("massage", "Type of massage", [n for n, _ in home_rows()])}
    {inp("date", "Booking date", "date")}
    {inp("time", "Time", "time", False)}
    {sel("duration", "Duration", durs)}
    {sel("city", "City", cities, "")}
    {inp("first", "First name")}
    {inp("last", "Last name", req=False)}
    {inp("phone", "Phone number", "tel")}
    {inp("email", "E-mail", "email", False)}
  </div>
  <div class="bform__out" data-out hidden>
    <div class="bform__type bform__type--small"><label><input type="radio" name="place" value="Hotel" checked><span>Hotel</span></label><label><input type="radio" name="place" value="Apartment"><span>Apartment</span></label></div>
    <div class="jf__grid" data-hotel>{inp("hotel", "Full hotel name", req=False)}{inp("room", "Room number", req=False)}</div>
    <div class="jf__grid" data-apart hidden>{inp("address", "Address", req=False, cls=" jf__f--wide")}{inp("zip", "Zip code", req=False)}{inp("door", "Door code", req=False)}
      {inp("interphone", "Interphone", req=False)}{inp("floor", "Floor", req=False)}{inp("flat", "Flat number", req=False)}</div>
    <p class="bform__note">*This information is confidential and will not be shared.</p>
  </div>
  <label class="jf__f jf__f--wide"><span>Comment</span><textarea name="comment" rows="3"></textarea></label>
  <input name="website" tabindex="-1" autocomplete="off" aria-hidden="true" class="book__hp">
  <button class="btn btn--gold btn--xl" type="submit"><span data-contact-label>Send booking</span></button>
  <p class="book__sent" data-contact-msg role="status" aria-live="polite"></p>
</form>"""
    body = f"""{phead("Contact us", [("SweetTouch", "index.html")], "Get in touch with SweetTouch", img="p-hdr-contact")}
<section class="sect prose" data-tone="noir"><div class="jobgrid">
  <div class="prose__in">
    <h2 class="prose__h2">We are available 24/7</h2>
    <p>The fastest and easiest way to contact us or make a booking is to give us a call on +33 7 58 96 37 65.</p>
    <p class="prose__cta"><a class="btn btn--gold" href="tel:+33758963765">{icon("phone")}+33 7 58 96 37 65</a><a class="btn btn--line" href="https://wa.me/33758963765">{icon("chat")}WhatsApp</a>
      <a class="btn btn--line" href="mailto:erotic.sweettouch@gmail.com">{icon("mail")}erotic.sweettouch@gmail.com</a></p>
    <p>Avenue de Wagram 75017, Paris. All locations are open daily from 10:00 to 02:00.</p>
  </div>
  <aside class="jobgrid__form" data-sticky-side>{form}</aside>
</div></section>
{footer()}"""
    return page("Contact us and book an erotic massage in Paris - SweetTouch", "Book an incall or outcall erotic massage in Paris: choose the masseuse, massage, date and duration.", body)


def build_book_page():
    """Book your massage: the six Paris locations as cards, then timetable and contacts (text 1:1 from the old page)."""
    it = [(t, u) for t, u in po.raw_items("pages/book-your-massage.txt")]
    h1 = next(i for i, (t, _) in enumerate(it) if t.startswith("# "))
    end = next(i for i, (t, _) in enumerate(it) if t == "You can find us")
    it = it[h1:end]
    title, lead = it[0][0][2:], it[1][0]
    k = next(i for i, (t, _) in enumerate(it) if t.startswith("SweetTouch Locations"))
    intro = "".join(f"<p>{e(t)}</p>" for t, _ in it[2:k] if t)
    cards, i = [], k + 1
    while i < len(it) and it[i][0].startswith("Paris "):
        name, addr, feat, note = it[i][0], it[i + 1][0], it[i + 2][0], it[i + 3][0]
        cards.append(f'<article class="loc"><h3>{e(name)}</h3><p class="loc__a">{icon("pin")}{e(addr.replace("Address: ", ""))}</p>'
                     f'<p class="loc__f">{e(feat.replace("Features: ", ""))}</p><p class="loc__n">{e(note)}</p></article>')
        i += 4
    rest = [t for t, _ in it[i:] if t and not t.startswith(("Book now", "Chat online", "WhatsApp:"))]
    body = f"""{phead(title, [("SweetTouch", "index.html")], lead, img="p-hdr-book-your-massage")}
<section class="sect prose" data-tone="noir"><div class="prose__in">{intro}
  <h2 class="prose__h2">SweetTouch locations</h2>
  <div class="locs">{"".join(cards)}</div>
  {"".join(f'<h3 class="prose__h3">{e(t)}</h3>' if len(t) < 40 and not t.endswith(".") else f"<p>{e(t)}</p>" for t in rest)}
  <p class="prose__cta"><a class="btn btn--gold btn--xl" href="contact.html">{icon("calendar")}Book now</a><a class="btn btn--line" href="https://wa.me/33758963765">{icon("chat")}WhatsApp +33 7 58 96 37 65</a></p>
</div></section>
{footer()}"""
    return page("Book your erotic massage in Paris - SweetTouch", lead, body)


def build_about():
    """About: the old text, laid out like the home page: banner, lead, two chapters with photos, numbers, masseuses."""
    L = [t for t, _ in po.raw_items("pages/about.txt")]
    h1 = next(i for i, t in enumerate(L) if t.startswith("# "))
    end = next(i for i, t in enumerate(L) if t == "You can find us")
    L = [t for t in L[h1 + 1:end] if t]
    si, mi = L.index("Services"), L.index("Masseuses and masseurs")
    para = lambda ls: "".join(f'<p class="lead">{e(t)}</p>' if t.startswith("Relive") else f"<p>{e(t)}</p>" for t in ls)
    nums = [(str(len(GIRLS)), "masseuses"), (str(len(INFOS)), "massages"), ("24/7", "booking support"), ("2015", "in Paris since")]
    body = f"""{phead("About SweetTouch", [("SweetTouch", "index.html")], img="p-hdr-about")}
<section class="sect about-lead" data-tone="noir"><p class="lead lead--wide">{e(L[0])}</p></section>
<section class="sect split split--dark" data-tone="wine">
  <div><h2 class="h2 h2--m">Services</h2>{para(L[si + 1:mi])}</div>
  <figure class="about2__img"><img src="img/v-adv-techniques.webp" alt="" sizes="(max-width: 720px) 92vw, 46vw" loading="lazy"></figure>
</section>
<section class="sect nums" data-tone="noir">{"".join(f'<div><b>{n}</b><span>{t}</span></div>' for n, t in nums)}</section>
<section class="sect split split--dark split--rev" data-tone="wine">
  <figure class="about2__img"><img src="img/v-about.webp" alt="" sizes="(max-width: 720px) 92vw, 46vw" loading="lazy"></figure>
  <div><h2 class="h2 h2--m">Masseuses and masseurs</h2>{para(L[mi + 1:])}</div>
</section>
<section class="sect girls" data-tone="noir"><h2 class="h2 h2--m">Meet our masseuses</h2>{girls([g["name"] for g in GIRLS[:5]])}</section>
{footer()}"""
    return page("About SweetTouch - erotic massage in Paris", L[0][:155], body)


def build_sitemap():
    sec = [("Main", [("Home", "index.html"), ("Our masseuses", "masseuses.html"), ("Massages & prices", "massages.html")]
            + [(t, f"{sl}.html") for t, sl in (("Paris locations", "paris-locations"), ("Erotic Massage in France", "erotic-massage-in-france"),
                                              ("Job offers", "job-offers"), ("Fidelity Card", "fidelity-card"), ("FAQ", "faq"), ("About", "about"),
                                              ("Testimonials", "testimonials"), ("Discounts", "discounts"), ("Blog", "blog"), ("Partners", "partners"),
                                              ("Terms and Conditions", "terms-and-conditions"), ("DMCA policy", "dmca-policy"))]),
           ("Massages", [(INFOS[sl]["name"], po.MFILE[sl]) for sl in MORDER]),
           ("Masseuses", [(g["name"], f"girl-{g['slug']}.html") for g in GIRLS])]
    cols = "".join(f'<div><h2 class="prose__h2">{t}</h2><ul class="links">{"".join(f"<li><a href=\"{u}\">{e(n)}</a></li>" for n, u in ls)}</ul></div>' for t, ls in sec)
    return page("Sitemap - SweetTouch", "All pages of SweetTouch", f"""{phead("Sitemap", [("SweetTouch", "index.html")], img="p-hdr-sitemap")}
<section class="sect prose" data-tone="noir"><div class="prose__in">{cols}</div></section>
{footer()}""")


# Booking lives on the home page; every "#book" link on other pages points there
away = lambda h: h.replace('href="#book"', 'href="index.html#book"')
out = {"index.html": build_home(), "massages.html": away(build_massages()), "masseuses.html": away(build_masseuses())}
out.update({po.MFILE[sl]: away(build_info(d)) for sl, d in INFOS.items()})
SPECIAL = {"sitemap": build_sitemap, "contact": build_contact, "book-your-massage": build_book_page, "about": build_about}
out.update({f"{sl}.html": away(SPECIAL[sl]() if sl in SPECIAL else build_text(sl)) for sl in po.SECONDARY})
out.update({f"girl-{g['slug']}.html": away(build_girl(g, home_rows())) for g in GIRLS})
for name, h in out.items():
    (ROOT / name).write_text(h, encoding="utf-8")
print("built", len(out), "pages")
