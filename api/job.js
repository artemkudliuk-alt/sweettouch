// Job application from job-offers.html -> email to the salon through Gmail SMTP, photos attached.
// Same env vars as api/book.js: GMAIL_USER, GMAIL_APP_PASSWORD (BOOK_TO overrides the recipient).
const nodemailer = require("nodemailer");

const TO = process.env.BOOK_TO || "erotic.sweettouch@gmail.com";
const FIELDS = [["name", "Name"], ["age", "Age"], ["country", "Country"], ["city", "City"], ["languages", "Languages spoken"],
  ["dress", "Dress size"], ["phone", "Phone number"], ["email", "Email"], ["whatsapp", "WhatsApp"], ["instagram", "Instagram"],
  ["location", "Own private location for in-call"], ["outcall_only", "Only outcall"], ["escort", "Escort companion"], ["experience", "Experience"]];
const REQUIRED = ["name", "age", "country", "city", "languages", "dress", "phone", "email", "whatsapp", "instagram", "experience"];
const clean = (v, max = 200) => String(v ?? "").replace(/\r/g, "").trim().slice(0, max);
const esc = (v) => v.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ ok: false });
  const b = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  if (b.website) return res.json({ ok: true }); // honeypot
  // one-line fields lose their line breaks; the experience text keeps them
  const o = Object.fromEntries(FIELDS.map(([k]) => [k, k === "experience" ? clean(b[k], 3000) : clean(b[k]).replace(/\n/g, " ")]));
  if (REQUIRED.some((k) => !o[k])) return res.status(400).json({ ok: false, error: "missing" });
  // Photos arrive already shrunk by the browser as data URLs; keep at most 6 JPEG/PNG images
  const photos = (Array.isArray(b.photos) ? b.photos : []).slice(0, 6)
    .map((p, i) => /^data:image\/(jpeg|png);base64,/.test(p?.data || "") && { filename: `photo-${i + 1}.${p.data.includes("png") ? "png" : "jpg"}`, path: p.data })
    .filter(Boolean);
  if (!photos.length) return res.status(400).json({ ok: false, error: "photos" });
  if (!process.env.GMAIL_USER || !process.env.GMAIL_APP_PASSWORD) return res.status(503).json({ ok: false });
  try {
    await nodemailer.createTransport({ service: "gmail", auth: { user: process.env.GMAIL_USER, pass: process.env.GMAIL_APP_PASSWORD } }).sendMail({
      from: `SweetTouch website <${process.env.GMAIL_USER}>`,
      to: TO,
      replyTo: /@/.test(o.email) ? o.email : undefined,
      subject: `Job application: ${o.name}, ${o.age}, ${o.city}`,
      text: FIELDS.map(([k, l]) => `${l}: ${o[k] || "-"}`).join("\n"),
      html: `<table cellpadding="6">${FIELDS.map(([k, l]) => `<tr><td valign="top"><b>${l}</b></td><td>${esc(o[k] || "-").replace(/\n/g, "<br>")}</td></tr>`).join("")}</table>`,
      attachments: photos,
    });
    res.json({ ok: true });
  } catch (e) {
    console.error("job mail failed:", e.message);
    res.status(502).json({ ok: false });
  }
};
