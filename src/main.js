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
  lenis = new Lenis();
  lenis.on("scroll", ScrollTrigger.update);
  gsap.ticker.add((t) => lenis.raf(t * 1000));
  // lagSmoothing(0) (needed for Lenis sync) is switched on after the preloader: during page load the main thread
  // stalls, and without smoothing the line drawing would jump ahead instead of continuing
  lenis.stop(); // released by the preloader
}
$$('a[href^="#"]').forEach((a) => a.addEventListener("click", (e) => {
  const target = $(a.getAttribute("href"));
  if (!target) return;
  e.preventDefault();
  setDrawer(false);
  lenis ? lenis.scrollTo(target) : target.scrollIntoView();
}));

// Glass pill once off the top; always visible
ScrollTrigger.create({ onUpdate: (s) => nav.classList.toggle("is-solid", s.scroll() > 80) });

/* ---------- Hero ---------- */
const hx = $("[data-hx]");
const svg = $(".hx__svg", hx), imgs = $$(".hx__img", svg), groups = $$(".hx__words", svg), full = imgs[0];
const after = $(".hx__after", hx), hint = $(".hx__hint", hx), ticker = $(".hx__ticker", hx);
let heroIntro = () => {};
// Hero video starts downloading now, while the preloader draws, and the preloader waits for it. Phones get a
// light vertical cut (540x960) that fills a portrait screen; wider screens get the 1280x720 one.
const vid = $(".hx__vid video", svg);
const useVid = !!vid && !reduce;
if (useVid) {
  const narrow = matchMedia("(max-width: 767px), (orientation: portrait) and (max-width: 1024px)").matches;
  vid.preload = "auto";
  vid.src = narrow ? vid.dataset.srcM : vid.dataset.src;
  if (narrow) vid.poster = "img/hero-poster-m.webp";
} else vid?.parentElement.remove();
const vidReady = useVid ? new Promise((r) => (vid.readyState >= 3 ? r() : vid.addEventListener("canplaythrough", r, { once: true }))) : Promise.resolve();
const flight = { x: 0, y: 0, s: 14 }; // zoom origin + final scale of the scroll fly-in

/* The SVG lives in screen pixels: viewBox = viewport, so the masked word is laid out and scaled as vector, never as a bitmap */
const measure = document.createElement("canvas").getContext("2d");
const layoutHero = () => {
  const W = innerWidth, H = innerHeight;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  $$("rect, image, mask, foreignObject", svg).forEach((n) => { n.setAttribute("x", 0); n.setAttribute("y", 0); n.setAttribute("width", W); n.setAttribute("height", H); });
  const texts = $$("text", groups[0]), last = texts[texts.length - 1].textContent, navH = W < 720 ? 66 : 96;
  // Real glyph metrics of the loaded face (measured at 100px, scale linearly): centre the visible caps, not the em boxes
  measure.font = `900 100px "Bodoni Moda"`;
  const capR = (measure.measureText("E").actualBoundingBoxAscent || 70) / 100;
  const descR = /[gjpqy]/.test(last) ? (measure.measureText("g").actualBoundingBoxDescent || 20) / 100 : 0;
  // Width sets the size, but on short screens the word + ticker + "Scroll" hint must still fit under the header
  const bottomZone = 140; // ticker line + "Scroll" hint live below the word
  const heightFit = (H - navH - bottomZone - 24) / (capR + 0.82 * (texts.length - 1) + descR);
  const fs = Math.min(W * +(W < 720 ? svg.dataset.fsM : svg.dataset.fs), 420, heightFit), lh = fs * 0.82;
  const cap = capR * fs, desc = descR * fs, block = cap + (texts.length - 1) * lh;
  const first = navH + (H - navH - bottomZone) / 2 - (block + desc) / 2 + cap; // centre between header and the bottom zone
  groups.forEach((g) => $$("text", g).forEach((t, i) => {
    t.setAttribute("x", W / 2);
    t.setAttribute("y", first + i * lh);
    t.setAttribute("font-size", fs);
  }));
  hx.style.setProperty("--tick-top", `${first + (texts.length - 1) * lh + desc + 14}px`);
  Object.assign(flight, { x: W / 2, y: H / 2, s: 14 });
  const t = texts.find((n) => n.textContent.includes("r"));
  if (!t) return;
  // Fly-through target: the round ball terminal of the first "r". Render the glyph and take the fattest point of its
  // right half (chamfer distance transform): that is the ball's centre and radius.
  const c = measure.canvas, F = 400, N = 640, O = 80, B = 480;
  c.width = c.height = N;
  measure.font = `900 ${F}px "Bodoni Moda"`;
  measure.fillText("r", O, B);
  const m = measure.measureText("r"), mid = O + (m.actualBoundingBoxRight - m.actualBoundingBoxLeft) / 2;
  const a = measure.getImageData(0, 0, N, N).data, d = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) d[i] = a[i * 4 + 3] > 128 ? 1e9 : 0;
  const relax = (i, j, w) => { if (d[j] + w < d[i]) d[i] = d[j] + w; };
  for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) {
    const i = y * N + x;
    relax(i, i - 1, 1); relax(i, i - N, 1); relax(i, i - N - 1, 1.414); relax(i, i - N + 1, 1.414);
  }
  let best = 0, bi = 0;
  for (let y = N - 2; y > 0; y--) for (let x = N - 2; x > 0; x--) {
    const i = y * N + x;
    relax(i, i + 1, 1); relax(i, i + N, 1); relax(i, i + N + 1, 1.414); relax(i, i + N - 1, 1.414);
    if (x > mid && d[i] > best) { best = d[i]; bi = i; }
  }
  const k = fs / F, box = t.getExtentOfChar(t.textContent.indexOf("r"));
  const x = box.x + ((bi % N) - O) * k, y = +t.getAttribute("y") - (B - Math.floor(bi / N)) * k, r = best * k;
  // Scale at which the ball covers every corner of the screen
  const s = Math.max(...[[0, 0], [W, 0], [0, H], [W, H]].map(([px, py]) => Math.hypot(px - x, py - y))) / r;
  Object.assign(flight, { x, y, s: s * 1.1 });
};
layoutHero();
document.fonts.ready.then(layoutHero); // metrics are exact only once Bodoni Black is in
addEventListener("resize", () => { layoutHero(); ScrollTrigger.refresh(); });

if (!reduce) {
  // Frames cross-dissolve inside the letters every 4 s
  let cur = 0;
  if (imgs.length > 1) setInterval(() => {
    imgs[cur].classList.remove("is-on");
    cur = (cur + 1) % imgs.length;
    imgs[cur].classList.add("is-on");
  }, 4000);
  // No Ken Burns on the masked photos: a continuously transformed <image> is resampled with Chrome's fast filter (looked pixelated)

  // Candle light follows the cursor; on touch it drifts in a 12 s circle
  const pin = $(".hx__pin", hx), pos = { x: innerWidth / 2, y: innerHeight / 2 };
  gsap.ticker.add(() => { pin.style.setProperty("--lx", `${pos.x}px`); pin.style.setProperty("--ly", `${pos.y}px`); });
  if (fine) {
    const qx = gsap.quickTo(pos, "x", { duration: 0.9, ease: "power3" }), qy = gsap.quickTo(pos, "y", { duration: 0.9, ease: "power3" });
    pin.addEventListener("pointermove", (e) => { qx(e.clientX); qy(e.clientY); });
  } else {
    const a = { t: 0 };
    gsap.to(a, { t: Math.PI * 2, duration: 12, repeat: -1, ease: "none", onUpdate: () => {
      pos.x = innerWidth * (0.5 + Math.cos(a.t) * 0.3); pos.y = innerHeight * (0.5 + Math.sin(a.t) * 0.2);
    } });
  }

  // Massage names roll under the word (home only)
  if (ticker) {
    const items = $$("li", ticker);
    ticker.append(items[0].cloneNode(true)); // seamless wrap
    let i = 0;
    setInterval(() => {
      i++;
      gsap.to(ticker.children, { yPercent: -100 * i, duration: 0.9, ease: "expo.inOut", onComplete: () => {
        if (i === items.length) { i = 0; gsap.set(ticker.children, { yPercent: 0 }); }
      } });
    }, 2200);
  }

  gsap.set(after.children, { autoAlpha: 0, y: 40 });
  const fly = { z: 0 };
  // The video inside the masked letters is re-rasterised on every frame it plays, so it runs only while it is the
  // picture: after the intro, at rest or fully landed, and while the hero is on screen. Mid-flight it holds still.
  let vidOn = false, heroOn = true;
  const syncVid = () => {
    if (!useVid) return;
    const play = vidOn && heroOn && (fly.z < 0.02 || fly.z > 0.98);
    if (play && vid.paused) vid.play().catch(() => {});
    else if (!play && !vid.paused) vid.pause();
  };
  ScrollTrigger.create({ trigger: hx, start: "top bottom", end: "bottom top", onToggle: (s) => { heroOn = s.isActive; syncVid(); } });
  const zoomTo = () => {
    const k = flight.s ** fly.z;
    gsap.set(groups, { scale: k, svgOrigin: `${flight.x} ${flight.y}` });
    syncVid();
  };
  zoomTo();
  ScrollTrigger.addEventListener("refresh", zoomTo); // re-apply after resize re-layout
  // Scroll: the letters (mask) grow until they cover the screen, the full frame takes over, then the copy arrives
  gsap.timeline({ scrollTrigger: { trigger: hx, start: "top top", end: "bottom bottom", scrub: 0.8 } })
    .to([hint, ticker].filter(Boolean), { autoAlpha: 0, duration: 0.1 }, 0)
    // Constant-feeling flight: scale = s^z, so every scrolled step multiplies the zoom by the same factor
    .to(fly, { z: 1, ease: "power1.in", duration: 0.6, onUpdate: zoomTo }, 0)
    .set(".hx__mfull", { opacity: 1 }, 0.6) // the ball already fills the screen by now; this only seals the edges
    .to(".hx__shade", { opacity: 1, duration: 0.25 }, 0.5)
    .to(after.children, { autoAlpha: 1, y: 0, stagger: 0.06, duration: 0.2 }, 0.62);

  // Entrance continues the preloader's gold line: the letter outlines draw themselves, then the video fills
  // the letters from the bottom up. Hidden from the start so nothing flashes before the hand-off.
  const edge = $(".hx__words--edge", svg), fill = $("g[mask]", svg), INK = "3000"; // > longest glyph outline in px
  gsap.set(edge, { strokeDasharray: `0 ${INK}` });
  gsap.set(fill, { clipPath: "inset(100% 0% 0% 0%)" });
  heroIntro = () => gsap.timeline({ onStart: () => { vidOn = true; syncVid(); } })
    .to(edge, { strokeDasharray: `${INK} 0`, duration: 2, ease: "power2.inOut" }, 0)
    .to(fill, { clipPath: "inset(0% 0% 0% 0%)", duration: 1.6, ease: "expo.inOut" }, 1.1)
    .to(edge, { opacity: 0, duration: 1.2, ease: "power2.out" }, 2.6); // the gold line only draws the letters in; at rest they are clean photo shapes
}

/* ---------- Preloader: line draws the silhouette, then flows into the hero letters ---------- */
const loader = $("[data-loader]");
// Heavy work (trigger re-measure) runs while the drawing still covers the screen; the hand-off itself only flips flags
const prepLoad = () => ScrollTrigger.refresh();
const finishLoad = () => { document.body.classList.remove("is-loading"); gsap.ticker.lagSmoothing(0); lenis?.start(); };
if (reduce || !loader) {
  loader?.remove();
  prepLoad();
  finishLoad();
} else {
  // Every strand runs bottom -> top; a strand starts when the rising front reaches its lowest point and moves
  // at the same speed as the front, so the whole contour climbs up the figure evenly.
  const drawUp = (T) => {
    const strands = $$(".loader__line", loader), ys = strands.flatMap((s) => [+s.dataset.y0, +s.dataset.y1]);
    const bottom = Math.max(...ys), span = bottom - Math.min(...ys), tl = gsap.timeline();
    strands.forEach((s) => tl.to(s, { attr: { "stroke-dashoffset": 0 }, ease: "none",
      duration: Math.max(0.05, ((s.dataset.y0 - s.dataset.y1) / span) * T) }, ((bottom - s.dataset.y0) / span) * T));
    return tl;
  };
  const ready = Promise.race([
    Promise.all([document.fonts.ready, vidReady, new Promise((r) => { const i = new Image(); i.onload = i.onerror = r; i.src = full.getAttribute("href"); })]),
    new Promise((r) => setTimeout(r, 6000)), // slow network: go anyway, the poster sits under the video
  ]);
  // Start drawing only once the page has loaded and the browser delivers frames again: during load the first
  // paint/decode stalls rAF for ~0.6 s, which froze the line mid-way and then made it jump.
  const settled = new Promise((r) => {
    const go = () => requestAnimationFrame(() => requestAnimationFrame(r));
    document.readyState === "complete" ? go() : addEventListener("load", go, { once: true });
  });
  settled.then(() => gsap.timeline()
    .add(drawUp(2.6), 0)
    .add(() => ready.then(prepLoad).then(() => gsap.timeline({ onComplete: () => loader.remove() })
      // The figure's line flows on upward and off its own end (dash slides past), the backdrop dissolves into the
      // hero's same dark tone, and the hero letters pick the line up
      .to(".loader__line", { attr: { "stroke-dashoffset": -1 }, duration: 1.1, ease: "power2.in" })
      .to(loader, { autoAlpha: 0, duration: 0.9, ease: "power1.inOut", onStart: () => { finishLoad(); heroIntro(); } }, 0.5)), "+=0.7")); // hold the finished drawing
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

  // Pause: the window opens to full screen while the photo settles, then the line rises word by word
  $$("[data-pause]").forEach((sec) => {
    const line = SplitText.create($(".pause__line", sec), { type: "words", mask: "words" });
    gsap.timeline({ scrollTrigger: { trigger: sec, start: "top top", end: "bottom bottom", scrub: 1 } })
      .fromTo($(".pause__frame", sec), { clipPath: innerWidth < 720 ? "inset(26% 18% 26% 18%)" : "inset(24% 34% 24% 34%)" }, { clipPath: "inset(0% 0% 0% 0%)", ease: "power2.inOut", duration: 1 }, 0)
      .to($(".pause__frame img", sec), { scale: 1, ease: "power2.out", duration: 1 }, 0)
      .from(line.words, { yPercent: 110, stagger: 0.04, duration: 0.4, ease: "power3.out" }, 0.45);
  });
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

  // Girls: on desktop the section pins and the rail travels sideways with the scroll; photos drift against it
  const girlsSec = $("[data-girls]");
  if (girlsSec) gsap.matchMedia().add("(min-width: 1024px) and (pointer: fine)", () => {
    const track = $(".rail__track", girlsSec);
    girlsSec.classList.add("is-pinned");
    track.scrollLeft = 0;
    const dist = () => track.scrollWidth - track.clientWidth;
    const travel = gsap.to(track, { x: () => -dist(), ease: "none", scrollTrigger: { trigger: girlsSec, start: "top top", end: () => `+=${dist()}`,
      pin: true, scrub: 1, anticipatePin: 1, invalidateOnRefresh: true, refreshPriority: 1 } }); // refresh first: its spacer shifts every trigger below
    gsap.to($(".girls__progress span", girlsSec), { scaleX: 1, ease: "none", scrollTrigger: { trigger: girlsSec, start: "top top", end: () => `+=${dist()}`, scrub: true } });
    $$(".card--g img", track).forEach((img) => gsap.fromTo(img, { xPercent: -7, scale: 1.16 }, { xPercent: 7, ease: "none",
      scrollTrigger: { trigger: img.closest(".card"), containerAnimation: travel, start: "left right", end: "right left", scrub: true } }));
    return () => girlsSec.classList.remove("is-pinned");
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

  // Marquee: two rows drift slowly in opposite ways; scrolling nudges them a little, then they settle back
  $$("[data-marquee]").forEach((m) => {
    const rows = $$(".marquee__track", m).map((t, i) =>
      gsap.fromTo(t, { xPercent: i ? -50 : 0 }, { xPercent: i ? 0 : -50, duration: 240, ease: "none", repeat: -1 }));
    ScrollTrigger.create({ trigger: m, start: "top bottom", end: "bottom top", onUpdate: (s) => {
      const dir = s.direction || 1, boost = 1 + Math.min(Math.abs(s.getVelocity()) / 1500, 1);
      rows.forEach((r) => gsap.to(r, { timeScale: boost * dir, duration: 0.6, overwrite: true,
        onComplete: () => gsap.to(r, { timeScale: dir, duration: 1.6, ease: "power2.out" }) }));
    } });
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

/* ---------- Tabs ---------- */
$$(".tabs").forEach((list) => {
  const tabs = $$("[data-tab]", list), panels = $$("[data-panel]", list.parentElement);
  tabs.forEach((t) => t.addEventListener("click", () => {
    tabs.forEach((x) => x.setAttribute("aria-selected", x === t));
    panels.forEach((p) => (p.hidden = p.dataset.panel !== t.dataset.tab));
    const shown = panels.find((p) => !p.hidden);
    $(".rail__track", shown).scrollLeft = 0;
    if (!reduce) gsap.from($$(".card", shown).slice(0, 5), { autoAlpha: 0, x: 60, stagger: 0.06, duration: 0.8, ease: "expo.out" });
  }));
});

/* ---------- Rails: drag with inertia-free pointer scroll + buttons ---------- */
$$("[data-rail]").forEach((rail) => {
  const track = $(".rail__track", rail);
  const step = () => (track.firstElementChild?.offsetWidth || 300) * 2;
  $("[data-prev]", rail).addEventListener("click", () => track.scrollBy({ left: -step(), behavior: "smooth" }));
  $("[data-next]", rail).addEventListener("click", () => track.scrollBy({ left: step(), behavior: "smooth" }));
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

/* ---------- Stage: next frame opens in columns, alternating from top and bottom ---------- */
const stage = $("[data-stage]");
if (stage && !reduce) {
  const layers = $$(".stage__layer", stage), texts = $$(".stage__text", stage), segs = $$(".stage__bar span", stage);
  const N = innerWidth < 720 ? 5 : 6;
  layers.forEach((layer, i) => {
    layer.style.zIndex = i;
    if (!i) return layer.classList.add("is-base");
    for (let c = 0; c < N; c++) {
      // 0.05% overlap hides hairline seams between neighbouring columns
      const l = Math.max(0, (c * 100) / N - 0.05), r = Math.max(0, 100 - ((c + 1) * 100) / N - 0.05);
      const col = document.createElement("div");
      col.className = "col";
      col.style.clipPath = c % 2 ? `inset(0% ${r}% 100% ${l}%)` : `inset(100% ${r}% 0% ${l}%)`;
      col.dataset.to = `inset(0% ${r}% 0% ${l}%)`;
      layer.append(col);
    }
  });
  const STEP = 1.5;
  const tl = gsap.timeline({
    scrollTrigger: { trigger: stage, start: "top top", end: "bottom bottom", scrub: 0.6 },
    onUpdate() {
      const p = this.progress() * segs.length;
      segs.forEach((s, i) => s.style.setProperty("--p", gsap.utils.clamp(0, 1, p - i)));
    },
  });
  layers.slice(1).forEach((layer, k) => {
    const at = k * STEP + 0.3;
    tl.to($$(".col", layer), { clipPath: (j, el) => el.dataset.to, duration: 1, ease: "power2.inOut", stagger: { each: 0.06, from: "edges" } }, at)
      .to(texts[k], { autoAlpha: 0, y: -24, duration: 0.3 }, at)
      .fromTo(texts[k + 1], { autoAlpha: 0, y: 24 }, { autoAlpha: 1, y: 0, duration: 0.4 }, at + 0.45);
  });
  tl.to({}, { duration: 0.4 });
} else if (stage) {
  stage.classList.add("is-static");
}

/* ---------- Booking: choices -> live summary, price and a prefilled WhatsApp message ---------- */
const bookEl = $("[data-book]");
if (bookEl) {
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
      photo.src = `img/${ev.target.value.toLowerCase()}.webp`;
      if (!reduce) gsap.fromTo(photo, { autoAlpha: 0, scale: 1.06 }, { autoAlpha: 1, scale: 1, duration: 0.8, ease: "expo.out" });
    }
    update(true);
  });
  fillDurs();
  update(false);
}
