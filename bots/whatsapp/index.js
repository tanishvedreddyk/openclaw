/**
 * OpenClaw WhatsApp Bot (Baileys)
 * First run: scan the QR code printed to the console.
 * Auth state is saved in /app/bots/whatsapp/auth_state/
 */

const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require("@whiskeysockets/baileys");
const qrcode  = require("qrcode-terminal");
const axios   = require("axios");
const pino    = require("pino");

const CORE_URL     = process.env.CORE_API_URL || "http://localhost:8080";
const AUTH_DIR     = "/app/bots/whatsapp/auth_state";
const WA_ENABLED   = (process.env.WHATSAPP_ENABLED || "false").toLowerCase() === "true";
const PREFIX       = process.env.WA_PREFIX || "";   // optional command prefix

if (!WA_ENABLED) {
  console.log("[whatsapp] WHATSAPP_ENABLED is not true — bot disabled.");
  process.exit(0);
}

const logger = pino({ level: "silent" });

async function askOpenClaw(message, sessionId) {
  const r = await axios.post(`${CORE_URL}/api/chat`, {
    message,
    session_id: sessionId,
    platform: "whatsapp",
  }, { timeout: 120000 });
  return r.data.reply;
}

async function startBot() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version }          = await fetchLatestBaileysVersion();

  const sock = makeWASocket({
    version,
    logger,
    auth: state,
    printQRInTerminal: false,      // we handle it below
    browser: ["OpenClaw", "Chrome", "1.0.0"],
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log("\n[whatsapp] Scan this QR code with WhatsApp:\n");
      qrcode.generate(qr, { small: true });
    }

    if (connection === "close") {
      const code = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = code !== DisconnectReason.loggedOut;
      console.log(`[whatsapp] Connection closed (code ${code}). Reconnect: ${shouldReconnect}`);
      if (shouldReconnect) setTimeout(startBot, 5000);
    } else if (connection === "open") {
      console.log("[whatsapp] ✅ WhatsApp connected!");
    }
  });

  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    if (type !== "notify") return;

    for (const msg of messages) {
      if (msg.key.fromMe) continue;
      if (!msg.message)   continue;

      const from = msg.key.remoteJid;
      const body = (
        msg.message.conversation ||
        msg.message.extendedTextMessage?.text ||
        ""
      ).trim();

      if (!body) continue;

      // Optional prefix filtering
      if (PREFIX && !body.startsWith(PREFIX)) continue;
      const text = PREFIX ? body.slice(PREFIX.length).trim() : body;

      if (!text) continue;

      // Handle reset command
      if (text.toLowerCase() === "!reset") {
        await axios.delete(`${CORE_URL}/api/chat/whatsapp-${from}`).catch(() => {});
        await sock.sendMessage(from, { text: "🔄 Conversation reset." });
        continue;
      }

      // Send typing indicator
      await sock.sendPresenceUpdate("composing", from);

      try {
        const reply = await askOpenClaw(text, `whatsapp-${from}`);
        await sock.sendPresenceUpdate("paused", from);
        await sock.sendMessage(from, { text: reply }, { quoted: msg });
      } catch (err) {
        await sock.sendPresenceUpdate("paused", from);
        await sock.sendMessage(from, { text: `❌ Error: ${err.message}` });
      }
    }
  });
}

startBot().catch(console.error);
