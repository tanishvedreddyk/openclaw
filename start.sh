#!/bin/bash
set -e

echo "======================================"
echo "   🐾 OpenClaw Starting Up"
echo "======================================"

# ── Create workspace ──────────────────────────────────────────────────────────
mkdir -p /workspace
echo "[startup] Workspace: /workspace"

# ── Install WhatsApp node deps if not installed ───────────────────────────────
if [ ! -d "/app/bots/whatsapp/node_modules" ]; then
  echo "[startup] Installing WhatsApp bot Node.js dependencies…"
  cd /app/bots/whatsapp && npm install --silent && cd /app
fi

# ── Print config summary ──────────────────────────────────────────────────────
echo ""
echo "Provider  : ${LLM_PROVIDER:-ollama}"
echo "Base URL  : ${LLM_BASE_URL:-http://localhost:11434/v1}"
echo "Model     : ${LLM_MODEL:-llama3.2}"
echo "Port      : ${PORT:-8080}"
echo ""
[ -n "$DISCORD_TOKEN"   ] && echo "  ✅ Discord bot enabled"   || echo "  ⬜ Discord bot disabled (set DISCORD_TOKEN)"
[ -n "$SLACK_BOT_TOKEN" ] && echo "  ✅ Slack bot enabled"     || echo "  ⬜ Slack bot disabled (set SLACK_BOT_TOKEN + SLACK_APP_TOKEN)"
[ -n "$TELEGRAM_TOKEN"  ] && echo "  ✅ Telegram bot enabled"  || echo "  ⬜ Telegram bot disabled (set TELEGRAM_TOKEN)"
[ "$WHATSAPP_ENABLED" = "true" ] && echo "  ✅ WhatsApp bot enabled" || echo "  ⬜ WhatsApp bot disabled (set WHATSAPP_ENABLED=true)"
echo ""

# ── Start all processes via supervisord ───────────────────────────────────────
echo "[startup] Launching supervisor…"
exec supervisord -c /app/supervisord.conf
