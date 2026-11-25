// Full booking form from contact.html (incall or outcall) -> email to the salon through Gmail SMTP.
// Same env vars as api/book.js: GMAIL_USER, GMAIL_APP_PASSWORD (BOOK_TO overrides the recipient).
const nodemailer = require("nodemailer");

const TO = process.env.BOOK_TO || "erotic.sweettouch@gmail.com";
const FIELDS = [["type", "Type"], ["girl", "Masseuse"], ["massage", "Massage"], ["date", "Date"], ["time", "Time"], ["duration", "Duration"],
  ["city", "City"], ["first", "First name"], ["last", "Last name"], ["phone", "Phone"], ["email", "Email"],
  ["place", "Outcall place"], ["hotel", "Hotel name"], ["room", "Room number"], ["address", "Address"], ["zip", "Zip code"],
  ["door", "Door code"], ["interphone", "Interphone"], ["floor", "Floor"], ["flat", "Flat number"], ["comment", "Comment"]];
const REQUIRED = ["type", "girl", "massage", "date", "duration", "city", "first", "phone"];
const clean = (v, max = 200) => String(v ?? "").replace(/[\r\n]+/g, " ").trim().slice(0, max);
const esc = (v) => v.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ ok: false });
  const b = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  if (b.website) return res.json({ ok: true }); // honeypot
  const o = Object.fromEntries(FIELDS.map(([k]) => [k, clean(b[k], k === "comment" ? 1000 : 200)]));
  if (REQUIRED.some((k) => !o[k]) || !["Incall", "Outcall"].includes(o.type)) return res.status(400).json({ ok: false, error: "missing" });
  if (!process.env.GMAIL_USER || !process.env.GMAIL_APP_PASSWORD) return res.status(503).json({ ok: false });
  const rows = FIELDS.filter(([k]) => o[k]);
  try {
    await nodemailer.createTransport({ service: "gmail", auth: { user: process.env.GMAIL_USER, pass: process.env.GMAIL_APP_PASSWORD } }).sendMail({
      from: `SweetTouch website <${process.env.GMAIL_USER}>`,
      to: TO,
      replyTo: /@/.test(o.email) ? o.email : undefined,
      subject: `${o.type} booking: ${o.massage} with ${o.girl}, ${o.date}`,
      text: rows.map(([k, l]) => `${l}: ${o[k]}`).join("\n"),
      html: `<table cellpadding="6">${rows.map(([k, l]) => `<tr><td><b>${l}</b></td><td>${esc(o[k])}</td></tr>`).join("")}</table>`,
    });
    res.json({ ok: true });
  } catch (e) {
    console.error("contact mail failed:", e.message);
    res.status(502).json({ ok: false });
  }
};
