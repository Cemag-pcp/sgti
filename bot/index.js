const express = require("express");
const qrcode = require("qrcode-terminal");
const QRCodeImage = require("qrcode");
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} = require("@whiskeysockets/baileys");

const PORT = process.env.PORT || 3333;
const BACKEND_WEBHOOK_URL =
  process.env.BACKEND_WEBHOOK_URL || "http://backend:8000/api/whatsapp/webhook/";
const BACKEND_WEBHOOK_TOKEN = process.env.BACKEND_WEBHOOK_TOKEN || "";
const FORWARD_INCOMING_TO_BACKEND = String(
  process.env.FORWARD_INCOMING_TO_BACKEND ?? "true"
).toLowerCase() === "true";

let sock = null;
let connectionStatus = "starting"; // starting | open | close
let lastQrAt = null;
let lastQrCode = null; // raw QR string

function normalizePhoneToJid(phone) {
  const digits = String(phone).replace(/\D/g, "");
  if (!digits) throw new Error("phone invalido");
  return `${digits}@s.whatsapp.net`;
}

function normalizeTargetToJid(target) {
  const raw = String(target || "").trim();
  if (!raw) throw new Error("destino invalido");
  if (raw.includes("@")) return raw;
  return normalizePhoneToJid(raw);
}

async function forwardIncomingMessageToBackend({ from, text }) {
  if (!FORWARD_INCOMING_TO_BACKEND || !BACKEND_WEBHOOK_URL) return;

  const headers = { "Content-Type": "application/json" };
  if (BACKEND_WEBHOOK_TOKEN) {
    headers["X-Webhook-Token"] = BACKEND_WEBHOOK_TOKEN;
  }

  const payload = {
    event: "message",
    payload: {
      fromMe: false,
      type: "chat",
      from,
      body: text,
    },
  };

  const response = await fetch(BACKEND_WEBHOOK_URL, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Webhook HTTP ${response.status}: ${body}`);
  }
}

async function startBaileys() {
  const { state, saveCreds } = await useMultiFileAuthState("auth_info");
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: false,
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      lastQrCode = qr;
      lastQrAt = new Date().toISOString();
      qrcode.generate(qr, { small: true });
      console.log("Escaneie o QR no WhatsApp > Aparelhos conectados.");
    }

    if (connection) {
      connectionStatus = connection;
      console.log("connection:", connection);
      if (connection === "open") lastQrCode = null;
    }

    if (connection === "close") {
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

      console.log("Conexao fechou. Reconectar?", shouldReconnect);

      if (shouldReconnect) {
        setTimeout(() => startBaileys().catch(console.error), 1500);
      } else {
        console.log("Logged out. Apague auth_info e escaneie novamente.");
      }
    }
  });

  sock.ev.on("messages.upsert", async ({ messages }) => {
    const msg = messages?.[0];
    if (!msg?.message) return;
    if (msg.key.fromMe) return;

    const from = msg.key.remoteJid;
    const text =
      msg.message.conversation ||
      msg.message.extendedTextMessage?.text ||
      "";

    console.log("msg", from, "->", text);

    if (!from) return;
    if (!text.trim()) return;

    if (text.trim().toLowerCase() === "ping") {
      await sock.sendMessage(from, { text: "pong" });
      return;
    }

    try {
      await forwardIncomingMessageToBackend({ from, text });
    } catch (err) {
      console.error("Erro ao encaminhar para backend:", err?.message || err);
    }
  });
}

async function main() {
  await startBaileys();

  const app = express();
  app.use(express.json({ limit: "1mb" }));

  app.get("/health", (req, res) => {
    res.json({
      ok: true,
      connectionStatus,
      hasSocket: !!sock,
      lastQrAt,
      backendWebhookUrl: BACKEND_WEBHOOK_URL,
      forwardIncomingToBackend: FORWARD_INCOMING_TO_BACKEND,
      now: new Date().toISOString(),
    });
  });

  // Body: { "phone": "5581999999999", "text": "Ola" }
  app.post("/send", async (req, res) => {
    try {
      if (!sock || connectionStatus !== "open") {
        return res.status(503).json({
          ok: false,
          error: "WhatsApp nao conectado ainda",
          connectionStatus,
        });
      }

      const { phone, to, jid, text } = req.body || {};
      const target = jid ?? to ?? phone;
      if (!target) return res.status(400).json({ ok: false, error: "Informe phone ou to" });
      if (!text) return res.status(400).json({ ok: false, error: "Informe text" });

      const targetJid = normalizeTargetToJid(target);
      const result = await sock.sendMessage(targetJid, { text: String(text) });

      return res.json({ ok: true, jid: targetJid, messageId: result?.key?.id || null });
    } catch (err) {
      return res.status(500).json({ ok: false, error: String(err?.message || err) });
    }
  });

  app.post("/send-text", async (req, res) => {
    req.url = "/send";
    app.handle(req, res);
  });

  app.get("/qr", async (req, res) => {
    try {
      if (!lastQrCode) {
        return res.json({ ok: true, qr: null, connected: connectionStatus === "open", connectionStatus });
      }
      const dataUrl = await QRCodeImage.toDataURL(lastQrCode, { width: 300, margin: 2 });
      return res.json({ ok: true, qr: dataUrl, connected: false, connectionStatus });
    } catch (err) {
      return res.status(500).json({ ok: false, error: String(err?.message || err) });
    }
  });

  app.post("/logout", async (req, res) => {
    try {
      if (sock) {
        await sock.logout();
        sock = null;
      }
      connectionStatus = "close";
      lastQrCode = null;
      return res.json({ ok: true, detail: "Desconectado. Reiniciando para gerar novo QR..." });
    } catch (err) {
      return res.status(500).json({ ok: false, error: String(err?.message || err) });
    } finally {
      setTimeout(() => startBaileys().catch(console.error), 1500);
    }
  });

  app.post("/reconnect", async (req, res) => {
    try {
      if (sock) {
        sock.end(new Error("manual reconnect"));
        sock = null;
      }
      connectionStatus = "close";
      lastQrCode = null;
      setTimeout(() => startBaileys().catch(console.error), 500);
      return res.json({ ok: true, detail: "Reconexao iniciada." });
    } catch (err) {
      return res.status(500).json({ ok: false, error: String(err?.message || err) });
    }
  });

  app.listen(PORT, () => {
    console.log(`API do bot em http://localhost:${PORT}`);
    console.log("  GET  /health");
    console.log("  POST /send { phone/to, text }");
    console.log(`  backend webhook: ${BACKEND_WEBHOOK_URL}`);
  });
}

main().catch((err) => {
  console.error("Erro fatal:", err);
  process.exit(1);
});
