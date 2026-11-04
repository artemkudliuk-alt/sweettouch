// Booking request from the home page -> email to the salon through Gmail SMTP.
// Needs two Vercel env vars: GMAIL_USER (the sending Gmail) and GMAIL_APP_PASSWORD (a Google app password, not the account password).
const nodemailer = require("nodemailer");

const TO = process.env.BOOK_TO || "erotic.sweettouch@gmail.com";
const FIELDS = ["Masseuse", "Massage", "Duration", "Price", "Name", "Contact"];
const clean = (v) => String(v ?? "").replace(/[\r\n]+/g, " ").trim().slice(0, 200);
const esc = (v) => v.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

module.exports = async (req, res) => {
  const mailer = () => nodemailer.createTransport({ service: "gmail", auth: { user: process.env.GMAIL_USER, pass: process.env.GMAIL_APP_PASSWORD } });
  // GET = health check: logs in to Gmail without sending anything
  if (req.method === "GET") return res.json({ smtp: await mailer().verify().then(() => true, (e) => e.code || "fail") });
  if (req.method !== "POST") return res.status(405).json({ ok: false });
  const b = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  if (b.website) return res.json({ ok: true }); // honeypot: bots fill every field
  const o = Object.fromEntries(FIELDS.map((k) => [k, clean(b[k])]));
  if (!o.Contact || !o.Massage) return res.status(400).json({ ok: false });
  if (!process.env.GMAIL_USER || !process.env.GMAIL_APP_PASSWORD) return res.status(503).json({ ok: false });
  try {
    await mailer().sendMail({
      from: `SweetTouch website <${process.env.GMAIL_USER}>`,
      to: TO,
      replyTo: /@/.test(o.Contact) ? o.Contact : undefined,
      subject: `Booking: ${o.Massage} with ${o.Masseuse}`,
      text: FIELDS.map((k) => `${k}: ${o[k] || "-"}`).join("\n"),
      html: `<table cellpadding="6">${FIELDS.map((k) => `<tr><td><b>${k}</b></td><td>${esc(o[k] || "-")}</td></tr>`).join("")}</table>`,
    });
    res.json({ ok: true });
  } catch (e) {
    console.error("book mail failed:", e.message);
    res.status(502).json({ ok: false });
  }
};
