import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";
import Lenis from "lenis";

gsap.registerPlugin(ScrollTrigger, SplitText);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const fine = matchMedia("(pointer: fine)").matches;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

/* Full-screen menu: curtain drops from the top, items rise line by line, the photo follows the hovered item */
const burger = $("[data-burger]"), drawer = $("[data-drawer]"), nav = $("[data-nav]");
const label = $(".nav__menu-label", burger), dImg = $(".drawer__img img", drawer);
let lenis, drawerTl;
const setDrawer = (open) => {
  if (open === !drawer.hidden) return;
  burger.setAttribute("aria-expanded", open);
  label.textContent = open ? "Close" : "Menu";
  document.documentElement.style.overflow = open ? "hidden" : "";
  if (lenis) open ? lenis.stop() : lenis.start();
  drawerTl?.kill();
  if (reduce) { drawer.hidden = !open; return; }
  if (open) {
    drawer.hidden = false;
    drawerTl = gsap.timeline()
      .fromTo(drawer, { clipPath: "inset(0% 0% 100% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.9, ease: "expo.inOut" })
      .fromTo($$(".drawer__t", drawer), { yPercent: 110 }, { yPercent: 0, duration: 1, ease: "expo.out", stagger: 0.06 }, 0.45)
      .fromTo(".drawer__img", { clipPath: "inset(100% 0% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 1.1, ease: "expo.inOut" }, 0.35)
      .fromTo(".drawer__img img", { scale: 1.3 }, { scale: 1, duration: 1.6, ease: "expo.out" }, 0.35)
      .fromTo($$(".drawer__side > *", drawer), { autoAlpha: 0, y: 24 }, { autoAlpha: 1, y: 0, duration: 0.8, ease: "expo.out", stagger: 0.06 }, 0.6);
  } else {
    drawerTl = gsap.timeline({ onComplete: () => (drawer.hidden = true) })
      .to(drawer, { clipPath: "inset(0% 0% 100% 0%)", duration: 0.7, ease: "expo.inOut" });
  }
};
burger.addEventListener("click", () => setDrawer(drawer.hidden));
addEventListener("keydown", (e) => { if (e.key === "Escape") setDrawer(false); });
$$(".drawer__big", drawer).forEach((a) => a.addEventListener("pointerenter", () => {
  if (dImg.getAttribute("src") === a.dataset.img) return;
  gsap.timeline().to(dImg, { autoAlpha: 0, scale: 1.06, duration: 0.25 })
    .add(() => dImg.setAttribute("src", a.dataset.img))
    .to(dImg, { autoAlpha: 1, scale: 1, duration: 0.6, ease: "expo.out" });
}));

/* Smooth scroll */
if (!reduce) {
  // Heavier, longer glide after the wheel (as on mandra.nextweb.ua); touch keeps the native inertia
  lenis = new Lenis({ lerp: 0.07, wheelMultiplier: 0.9, smoothWheel: true });
  lenis.on("scroll", ScrollTrigger.update);
  gsap.ticker.add((t) => lenis.raf(t * 1000));
  gsap.ticker.lagSmoothing(0);
}
// In-page anchors, including "index.html#girls" while already on "/": scroll here instead of reloading the page
const page = (path) => path.replace(/\/index\.html$/, "/");
document.addEventListener("click", (e) => {
  const a = e.target.closest("a[href*='#']");
  if (!a) return;
  const u = new URL(a.href, location.href);
  if (!u.hash || u.origin !== location.origin || page(u.pathname) !== page(location.pathname)) return;
  const target = document.getElementById(decodeURIComponent(u.hash.slice(1)));
  if (!target) return;
  e.preventDefault();
  setDrawer(false);
  lenis ? lenis.scrollTo(target, { duration: 1.4 }) : target.scrollIntoView();
});

// Language switcher (<details>): closes on a click elsewhere or Escape
const langSw = $("[data-lang]");
if (langSw) {
  document.addEventListener("pointerdown", (ev) => { if (langSw.open && !langSw.contains(ev.target)) langSw.open = false; });
  langSw.addEventListener("keydown", (ev) => { if (ev.key === "Escape") { langSw.open = false; $("summary", langSw).focus(); } });
}

// Glass pill once off the top; always visible
ScrollTrigger.create({ onUpdate: (s) => nav.classList.toggle("is-solid", s.scroll() > 80) });

/* ---------- Hero ---------- */
const hx = $("[data-hx]");
if (hx) {
  const svg = $(".hx__svg", hx), imgs = $$(".hx__img", svg), groups = $$(".hx__words", svg);
  const hero = { glyphs: [], fs: 0, dirty: true }; // canvas letter layout
  const after = $(".hx__after", hx);
  // Video hero: the letters are painted on a canvas and the video is drawn through them (source-in). An SVG mask over a
  // <video> is ignored by Safari (it showed the bare clip, no letters) and re-rasterised on the CPU every frame elsewhere.
  const cv = $(".hx__cv", hx), ctx = cv?.getContext("2d"), vid = $(".hx__src", hx);
  const useVid = !!vid && !reduce;
  const narrow = matchMedia("(max-width: 767px), (orientation: portrait) and (max-width: 1024px)").matches;
  const poster = new Image();
  if (cv) poster.onload = () => { hero.dirty = true; };
  if (cv) poster.src = narrow ? cv.dataset.posterM : cv.dataset.poster;
  if (useVid) { vid.src = narrow ? vid.dataset.srcM : vid.dataset.src; vid.play().catch(() => {}); }

  /* The SVG lives in screen pixels: viewBox = viewport, so the masked word is laid out and scaled as vector, never as a bitmap */
  const measure = document.createElement("canvas").getContext("2d");
  const layoutHero = () => {
    // Layout viewport height: on iOS it is the small viewport and does not change while the browser bar slides
    const W = innerWidth, H = document.documentElement.clientHeight || innerHeight;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    $$("rect, image, mask", svg).forEach((n) => { n.setAttribute("x", 0); n.setAttribute("y", 0); n.setAttribute("width", W); n.setAttribute("height", H); });
    const texts = $$("text", $(".hx__words--edge", svg)), last = texts[texts.length - 1].textContent, navH = W < 720 ? 66 : 96;
    const bottomZone = after ? H - after.offsetTop + 40 : 48; // buttons + intro live below the word
    // Real glyph metrics of the loaded face (measured at 100px, scale linearly): centre the visible caps, not the em boxes
    measure.font = `900 100px "Bodoni Hero"`;
    const capR = (measure.measureText("E").actualBoundingBoxAscent || 70) / 100;
    const descR = /[gjpqy]/.test(last) ? (measure.measureText("g").actualBoundingBoxDescent || 20) / 100 : 0;
    // Width sets the size, but on short screens the word must still fit between the header and the copy below it
    const heightFit = (H - navH - bottomZone - 24) / (capR + 0.82 * (texts.length - 1) + descR);
    const fs = Math.min(W * +(W < 720 ? svg.dataset.fsM : svg.dataset.fs), 420, heightFit), lh = fs * 0.82;
    const cap = capR * fs, desc = descR * fs, block = cap + (texts.length - 1) * lh;
    const first = navH + (H - navH - bottomZone) / 2 - (block + desc) / 2 + cap; // centre between header and the bottom zone
    groups.forEach((g) => $$("text", g).forEach((t, i) => {
      t.setAttribute("x", W / 2);
      t.setAttribute("y", first + i * lh);
      t.setAttribute("font-size", fs);
    }));
    // Bodoni's hairlines are 1-2 px at this size and vanish over dark video frames; a thin same-colour stroke on the
    // mask text (scales with the zoom, keeps the letterforms) gives every serif and diagonal enough photo to read
    $(".hx__words--mask", svg).setAttribute("stroke-width", (fs * 0.014).toFixed(2));
    // Canvas letters sit exactly where the SVG laid them out (per-glyph positions carry kerning and letter-spacing)
    hero.fs = fs;
    hero.glyphs = texts.flatMap((t) => [...t.textContent].map((ch, i) => { const p = t.getStartPositionOfChar(i); return [ch, p.x, p.y]; }));
    if (hero.mask) hero.mask.key = ""; // glyphs moved: rebuild the mask
    hero.dirty = true;
  };
  layoutHero();
  const heroFont = document.fonts.load('900 100px "Bodoni Hero"').catch(() => {});
  heroFont.then(layoutHero); // metrics are exact only once the hero face is in
  document.fonts.ready.then(layoutHero); // the copy under the word grows once its own fonts arrive
  // Phones fire "resize" whenever the browser bar slides in or out during a swipe: re-laying out the hero and every
  // trigger on that made the page jump. Only a real width change (rotation, desktop resize) re-lays out.
  ScrollTrigger.config({ ignoreMobileResize: true });
  let lastW = innerWidth;
  addEventListener("resize", () => { if (innerWidth === lastW && !fine) return; lastW = innerWidth; layoutHero(); ScrollTrigger.refresh(); });

  // Paint: the frame, cut to the glyphs (destination-in), then a warm 10% lift. Pixel ratio capped at 2 (sharp, half the fill).
  // The word as a white mask on its own canvas (same pixel size as the hero canvas)
  const paintMask = (m, W, H, d) => {
    const key = `${hero.fs}|${hero.glyphs.length}|${cv.width}x${cv.height}`;
    if (m.key === key) return; // unchanged since the last frame: video frames reuse the same mask
    m.key = key;
    if (m.width !== cv.width || m.height !== cv.height) { m.width = cv.width; m.height = cv.height; }
    const c = m.getContext("2d");
    c.setTransform(d, 0, 0, d, 0, 0);
    c.clearRect(0, 0, W, H);
    c.font = `900 ${hero.fs}px "Bodoni Hero"`;
    c.fillStyle = c.strokeStyle = "#fff";
    c.lineWidth = hero.fs * 0.014; // Bodoni hairlines are 1-2 px: a thin stroke keeps every serif readable over dark frames
    c.lineJoin = "round";
    for (const [ch, x, y] of hero.glyphs) { c.fillText(ch, x, y); c.strokeText(ch, x, y); }
  };
  const paintHero = () => {
    const W = innerWidth, H = document.documentElement.clientHeight || innerHeight, d = Math.min(devicePixelRatio || 1, 2);
    if (cv.width !== Math.round(W * d) || cv.height !== Math.round(H * d)) { cv.width = Math.round(W * d); cv.height = Math.round(H * d); }
    ctx.setTransform(d, 0, 0, d, 0, 0);
    ctx.globalCompositeOperation = "source-over";
    ctx.clearRect(0, 0, W, H);
    const src = useVid && vid.readyState >= 2 ? vid : poster.naturalWidth ? poster : null;
    if (!src || !hero.fs) return;
    // Frame first with plain source-over, then cut it to the glyphs (destination-in). The composite op is applied to the
    // text, never to the video: iOS Safari ignores composite modes when drawing <video> frames, which showed the bare clip.
    const sw = src.videoWidth || src.naturalWidth, sh = src.videoHeight || src.naturalHeight, sc = Math.max(W / sw, H / sh);
    ctx.drawImage(src, (W - sw * sc) / 2, (H - sh * sc) / 2, sw * sc, sh * sc);
    // destination-in per glyph would erase the earlier glyphs, so the whole word is one mask canvas applied once
    const mask = hero.mask || (hero.mask = document.createElement("canvas"));
    paintMask(mask, W, H, d);
    ctx.save();
    ctx.globalCompositeOperation = "destination-in";
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(mask, 0, 0);
    ctx.restore();
    ctx.setTransform(d, 0, 0, d, 0, 0);
    ctx.globalCompositeOperation = "source-atop";
    ctx.fillStyle = "rgba(242, 179, 94, 0.1)";
    ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = "source-over";
  };
  if (cv) {
    // Repaint only when something changed: a new video frame (requestVideoFrameCallback), layout or the poster
    const rvfc = useVid && "requestVideoFrameCallback" in vid;
    if (rvfc) { const onFrame = () => { hero.dirty = true; vid.requestVideoFrameCallback(onFrame); }; vid.requestVideoFrameCallback(onFrame); }
    gsap.ticker.add(() => {
      if (hero.dirty || (useVid && !rvfc && !vid.paused)) { hero.dirty = false; paintHero(); }
    });
  }

  if (!reduce) {
    // Frames cross-dissolve inside the letters every 4 s
    let cur = 0;
    if (imgs.length > 1) setInterval(() => {
      imgs[cur].classList.remove("is-on");
      cur = (cur + 1) % imgs.length;
      imgs[cur].classList.add("is-on");
    }, 4000);
    // No Ken Burns on the masked photos: a continuously transformed <image> is resampled with Chrome's fast filter (looked pixelated)

    // The clip plays only while the hero is on screen
    if (useVid) ScrollTrigger.create({ trigger: hx, start: "top bottom", end: "bottom top",
      onToggle: (s) => (s.isActive ? vid.play().catch(() => {}) : vid.pause()) });
  }
}

if (!reduce) {
  gsap.to(".thread span", { scaleY: 1, ease: "none", scrollTrigger: { trigger: "main", start: "top top", end: "bottom bottom", scrub: true } });

  const p = $("[data-highlight]");
  if (p) {
    p.innerHTML = p.textContent.split(" ").map((w) => `<span>${w}</span>`).join(" ");
    gsap.to($$("span", p), { opacity: 1, stagger: 0.1, ease: "none", scrollTrigger: { trigger: p, start: "top 80%", end: "bottom 45%", scrub: true } });
  }

  // Big photos drift slower than the page
  $$("[data-parallax] img").forEach((img) => gsap.fromTo(img, { yPercent: -8 }, { yPercent: 0, ease: "none",
    scrollTrigger: { trigger: img.parentElement, start: "top bottom", end: "bottom top", scrub: true } }));

}

/* ---------- Tone journey: the page slowly sinks from red to black, and only twice opens to skin-light ----------
   Each section declares data-tone; the body colour is scrubbed from the previous tone over ~70% of the viewport,
   so changes are long and continuous instead of a quick switch. */
const TONES = { nuit: ["#1a0609", "#ead7c5", 1], wine: ["#3d0a14", "#ead7c5", 1], noir: ["#0c0305", "#ead7c5", 0.6], chair: ["#ead7c5", "#1a0609", 0] };
// One page-long timeline whose time unit is a scrolled pixel: every transition sits at its own scroll position,
// so tones never fight each other (separate tweens on the same property did on fast scroll).
const toneTl = gsap.timeline({ paused: true });
const buildTones = () => {
  // Rebuild the contents only; the ScrollTrigger below lives for the whole page (killing it during a refresh broke ST's loop)
  toneTl.clear();
  const tl = toneTl, body = document.body, glowEl = $(".glow"), vh = innerHeight, max = ScrollTrigger.maxScroll(window);
  tl.set(body, { backgroundColor: TONES.nuit[0], color: TONES.nuit[1] }, 0).set(glowEl, { opacity: 1 }, 0);
  let prev = "nuit";
  $$("[data-tone]").forEach((sec) => {
    const [bg, fg, glow] = TONES[sec.dataset.tone], [pbg, pfg, pglow] = TONES[prev], dur = vh * 0.7;
    const at = Math.min(Math.max(0, sec.getBoundingClientRect().top + scrollY - vh * 0.85), Math.max(0, max - dur));
    tl.fromTo(body, { backgroundColor: pbg, color: pfg }, { backgroundColor: bg, color: fg, duration: dur, ease: "none", immediateRender: false }, at)
      .fromTo(glowEl, { opacity: pglow }, { opacity: glow, duration: dur, ease: "none", immediateRender: false }, at);
    prev = sec.dataset.tone;
  });
  tl.set({}, {}, Math.max(max, tl.duration()));
};
buildTones();
ScrollTrigger.create({ start: 0, end: () => ScrollTrigger.maxScroll(window), animation: toneTl, scrub: reduce ? true : 0.8 });
ScrollTrigger.addEventListener("refreshInit", buildTones); // layout changed (resize, accordion, fonts): re-place transitions
$$("details").forEach((d) => d.addEventListener("toggle", () => ScrollTrigger.refresh()));
// SEO block: folded to a short preview; "Show all" opens the full list of chapters
$$("[data-seo]").forEach((seo) => {
  const btn = $("[data-seo-toggle]", seo);
  btn.addEventListener("click", () => {
    const open = seo.classList.toggle("is-open");
    btn.setAttribute("aria-expanded", open);
    btn.textContent = open ? "Show less" : "Show all";
    ScrollTrigger.refresh();
  });
});
// Accordions open and close as a smooth height tween instead of the native jump
if (!reduce) $$("details.faq__item, details.chapter").forEach((d) => {
  const body = d.querySelector(":scope > :not(summary)");
  $("summary", d).addEventListener("click", (ev) => {
    ev.preventDefault();
    gsap.killTweensOf(body);
    if (d.open) {
      gsap.to(body, { height: 0, opacity: 0, overflow: "hidden", duration: 0.5, ease: "power3.inOut",
        onComplete: () => { d.open = false; gsap.set(body, { clearProps: "height,opacity,overflow" }); } });
    } else {
      d.open = true;
      gsap.fromTo(body, { height: 0, opacity: 0, overflow: "hidden" }, { height: "auto", opacity: 1, duration: 0.8, ease: "expo.out",
        onComplete: () => gsap.set(body, { clearProps: "height,opacity,overflow" }) });
    }
  });
});
// Any later change of page height (lazy images, fonts, split text) would leave trigger positions stale; on mobile the
// footer mark's start ended up below the max scroll and never fired
let lastH = 0, heightTimer;
new ResizeObserver(() => {
  const h = document.documentElement.scrollHeight;
  if (Math.abs(h - lastH) < 2) return;
  lastH = h;
  clearTimeout(heightTimer);
  heightTimer = setTimeout(() => ScrollTrigger.refresh(), 200);
}).observe(document.body);

/* ---------- Reveals ---------- */
if (!reduce) {
  // Headings and copy rise line by line from behind a mask (re-split on resize/font load)
  document.fonts.ready.then(() => {
    $$(".sect .h2, .lead, .how__intro, .split p, .step h3, .step p, .faq .h2, .book__title").forEach((el) => SplitText.create(el, {
      type: "lines", mask: "lines", autoSplit: true,
      onSplit: (s) => gsap.from(s.lines, { yPercent: 110, duration: 1.2, ease: "expo.out", stagger: 0.08,
        scrollTrigger: { trigger: el, start: "top 88%", once: true } }),
    }));
  });

  // Big photos open like a curtain from the bottom while the frame settles from 1.25
  $$(".about__img, .split__img, .chapter__img").forEach((fig) => {
    gsap.timeline({ scrollTrigger: { trigger: fig, start: "top 85%", once: true } })
      .fromTo(fig, { clipPath: "inset(100% 0% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 1.4, ease: "expo.inOut" })
      .from($("img", fig), { scale: 1.25, duration: 1.8, ease: "expo.out" }, 0.1);
  });

  // How it works: each step's gold rule draws left to right, then its outlined number rises
  $$(".step").forEach((st, i) => gsap.timeline({ scrollTrigger: { trigger: ".steps", start: "top 80%", once: true }, delay: i * 0.18 })
    .fromTo(st, { "--line-x": 0 }, { "--line-x": 1, duration: 1.2, ease: "expo.inOut" })
    .from($(".step__n", st), { yPercent: 40, autoAlpha: 0, duration: 1.2, ease: "expo.out" }, 0.3));

  // Rail cards arrive as a wave
  $$("[data-rail]").forEach((rail) => {
    if (rail.closest("[hidden]")) return;
    gsap.from($$(".card", rail).slice(0, 6), { x: 120, autoAlpha: 0, duration: 1.2, ease: "expo.out", stagger: 0.07,
      scrollTrigger: { trigger: rail, start: "top 85%", once: true } });
  });

}

/* ---------- Cursor ring with context labels + magnetic buttons ---------- */
if (fine && !reduce) {
  const cur = $(".cursor"), label = $(".cursor__label", cur);
  const cx = gsap.quickTo(cur, "x", { duration: 0.35, ease: "power3" }), cy = gsap.quickTo(cur, "y", { duration: 0.35, ease: "power3" });
  addEventListener("pointermove", (e) => { cur.classList.add("is-on"); cx(e.clientX); cy(e.clientY); });
  document.addEventListener("pointerleave", () => cur.classList.remove("is-on"));
  const hint = (sel, text) => $$(sel).forEach((el) => {
    el.addEventListener("pointerenter", () => { label.textContent = text; cur.classList.add("is-big"); });
    el.addEventListener("pointerleave", () => cur.classList.remove("is-big"));
  });
  hint(".card--m, .card--g", "View");
  hint(".card--b", "Read");

  $$(".btn").forEach((b) => {
    const bx = gsap.quickTo(b, "x", { duration: 0.6, ease: "elastic.out(1, 0.4)" }), by = gsap.quickTo(b, "y", { duration: 0.6, ease: "elastic.out(1, 0.4)" });
    b.addEventListener("pointermove", (e) => { const r = b.getBoundingClientRect(); bx((e.clientX - r.left - r.width / 2) * 0.3); by((e.clientY - r.top - r.height / 2) * 0.4); });
    b.addEventListener("pointerleave", () => { bx(0); by(0); });
  });
}

/* ---------- Rails: drag with inertia-free pointer scroll + buttons ---------- */
$$("[data-rail]").forEach((rail) => {
  const track = $(".rail__track", rail);
  // Arrows move exactly one card: to the next (or previous) card edge from where the track is now
  const go = (dir) => {
    const cards = [...track.children], base = cards[0]?.offsetLeft ?? 0, x = track.scrollLeft;
    const lefts = cards.map((c) => c.offsetLeft - base);
    const t = dir > 0 ? lefts.find((l) => l > x + 4) : lefts.findLast((l) => l < x - 4);
    if (t !== undefined) track.scrollTo({ left: t, behavior: "smooth" });
  };
  $("[data-prev]", rail).addEventListener("click", () => go(-1));
  $("[data-next]", rail).addEventListener("click", () => go(1));
  if (!fine) return;
  let x0 = 0, s0 = 0, moved = false, down = false;
  track.addEventListener("pointerdown", (e) => { down = true; moved = false; x0 = e.clientX; s0 = track.scrollLeft; });
  addEventListener("pointermove", (e) => {
    if (!down) return;
    const dx = e.clientX - x0;
    if (Math.abs(dx) > 5) { moved = true; track.classList.add("is-drag"); }
    track.scrollLeft = s0 - dx;
  });
  addEventListener("pointerup", () => { down = false; setTimeout(() => track.classList.remove("is-drag"), 0); });
  track.addEventListener("click", (e) => { if (moved) e.preventDefault(); }, true);
});

/* ---------- Stage: a still block, the advantages beside one photo ---------- */
const stage = $("[data-stage]");
// The photo is a CSS background (no native lazy loading): attach it only when the block is ~2 screens away, so it
// never competes with the hero video on load
if (stage) {
  const io = new IntersectionObserver(([en]) => {
    if (!en.isIntersecting) return;
    const l = $(".stage__layer", stage);
    l.style.setProperty("--img", `url(${l.dataset.img})`);
    io.disconnect();
  }, { rootMargin: "200% 0px" });
  io.observe(stage);
}

/* ---------- Booking: choices -> live summary, price and a prefilled WhatsApp message ---------- */
const bookEl = $("[data-book]");
// Massage picker: a styled listbox built from the native select's optgroups; choosing writes back to the select
// and fires "change", so the booking logic below stays unaware of it
const buildPicker = (sel) => {
  const wrap = sel.parentElement, chevron = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
  const from = (o) => `from ${Math.min(...JSON.parse(o.dataset.prices).map((p) => +p[1]))} €`;
  const btn = Object.assign(document.createElement("button"), { type: "button", className: "msel__btn" });
  btn.setAttribute("aria-haspopup", "listbox"); btn.setAttribute("aria-expanded", "false"); btn.setAttribute("aria-label", "Massage");
  btn.innerHTML = `<span></span><small></small>${chevron}`;
  const list = Object.assign(document.createElement("div"), { className: "msel__list", hidden: true });
  list.setAttribute("role", "listbox"); list.setAttribute("data-lenis-prevent", "");
  $$("optgroup", sel).forEach((g) => {
    const h = Object.assign(document.createElement("p"), { className: "msel__group", textContent: g.label });
    list.append(h);
    $$("option", g).forEach((o) => {
      const b = Object.assign(document.createElement("button"), { type: "button", className: "msel__opt" });
      b.setAttribute("role", "option"); b.dataset.value = o.value;
      b.innerHTML = "<span></span><small></small>";
      b.firstChild.textContent = o.value; b.lastChild.textContent = from(o);
      list.append(b);
    });
  });
  wrap.classList.add("is-custom"); wrap.append(btn, list);
  const opts = $$(".msel__opt", list);
  const paint = () => {
    btn.firstChild.textContent = sel.value; btn.children[1].textContent = from(sel.selectedOptions[0]);
    opts.forEach((b) => b.setAttribute("aria-selected", b.dataset.value === sel.value));
  };
  const open = (yes) => {
    if (yes === !list.hidden) return;
    btn.setAttribute("aria-expanded", yes);
    if (yes) {
      list.hidden = false;
      const cur = opts.find((b) => b.dataset.value === sel.value);
      list.scrollTop = cur.offsetTop - list.clientHeight / 2 + cur.offsetHeight / 2;
      if (!reduce) gsap.fromTo(list, { opacity: 0, y: -10, clipPath: "inset(0% 0% 100% 0% round 22px)" },
        { opacity: 1, y: 0, clipPath: "inset(0% 0% 0% 0% round 22px)", duration: 0.55, ease: "expo.out" });
      cur.focus({ preventScroll: true });
    } else if (reduce) list.hidden = true;
    else gsap.to(list, { opacity: 0, y: -6, duration: 0.25, ease: "power2.in", onComplete: () => { list.hidden = true; } });
  };
  btn.addEventListener("click", () => open(list.hidden));
  list.addEventListener("click", (ev) => {
    const b = ev.target.closest(".msel__opt");
    if (!b) return;
    sel.value = b.dataset.value;
    sel.dispatchEvent(new Event("change", { bubbles: true }));
    paint(); open(false); btn.focus();
  });
  list.addEventListener("keydown", (ev) => {
    const i = opts.indexOf(document.activeElement);
    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") { ev.preventDefault(); opts[Math.max(0, Math.min(opts.length - 1, i + (ev.key === "ArrowDown" ? 1 : -1)))].focus(); }
    if (ev.key === "Escape" || ev.key === "Tab") { open(false); if (ev.key === "Escape") btn.focus(); }
  });
  btn.addEventListener("keydown", (ev) => { if (ev.key === "ArrowDown") { ev.preventDefault(); open(true); } });
  document.addEventListener("pointerdown", (ev) => { if (!wrap.contains(ev.target)) open(false); });
  paint();
};
if (bookEl) {
  buildPicker($("select", bookEl));
  const sel = $("select", bookEl), durs = $("[data-durs]", bookEl), wa = $("[data-wa]", bookEl), photo = $("[data-book-photo]", bookEl);
  const sum = (k, v) => { $(`[data-sum="${k}"]`, bookEl).textContent = v; };
  const fillDurs = () => {
    const keep = $("input[name=dur]:checked", durs)?.value;
    durs.replaceChildren(...JSON.parse(sel.selectedOptions[0].dataset.prices).map(([d, p]) => {
      const l = document.createElement("label");
      l.className = "dur";
      l.innerHTML = `<input type="radio" name="dur"><span></span><b></b>`;
      Object.assign(l.firstChild, { value: d });
      l.firstChild.dataset.price = p;
      l.children[1].textContent = d;
      l.children[2].textContent = `${p} €`;
      return l;
    }));
    ($$("input", durs).find((i) => i.value === keep) || $("input", durs)).checked = true;
  };
  const update = (animate) => {
    const girl = $("input[name=girl]:checked", bookEl).value, d = $("input[name=dur]:checked", durs);
    sum("girl", girl); sum("massage", sel.value); sum("dur", d.value); sum("price", d.dataset.price);
    wa.href = `https://wa.me/33758963765?text=${encodeURIComponent(`Hello SweetTouch! I would like to book ${sel.value} (${d.value}) with ${girl}.`)}`;
    if (animate && !reduce) gsap.from('[data-sum="price"]', { yPercent: 70, autoAlpha: 0, duration: 0.6, ease: "expo.out" });
  };
  bookEl.addEventListener("change", (ev) => {
    if (ev.target === sel) fillDurs();
    if (ev.target.name === "girl") {
      const n = ev.target.dataset.photo;
      photo.removeAttribute("srcset"); photo.src = `img/${n}.webp`;
      if (!reduce) gsap.fromTo(photo, { autoAlpha: 0, scale: 1.06 }, { autoAlpha: 1, scale: 1, duration: 0.8, ease: "expo.out" });
    }
    update(true);
  });
  fillDurs();
  update(false);
}
