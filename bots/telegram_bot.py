"""
OpenClaw Telegram Bot
Commands:
  /start  — greeting
  /reset  — clear conversation
  /help   — show capabilities
  Any other message → chat
"""
import sys, httpx
sys.path.insert(0, "/app")
from core.config import cfg

if not cfg.TELEGRAM_TOKEN:
    print("[telegram] TELEGRAM_TOKEN not set — bot disabled.")
    sys.exit(0)

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from telegram.constants import ParseMode, ChatAction

CORE = cfg.CORE_API_URL


async def ask_openclaw(message: str, session_id: str) -> str:
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{CORE}/api/chat",
                         json={"message": message, "session_id": session_id, "platform": "telegram"})
        r.raise_for_status()
        return r.json()["reply"]


# ── Commands ──────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐾 *OpenClaw* is ready\\!\n\n"
        "I'm a powerful AI assistant with web search, code execution, file ops, and more\\.\n\n"
        "Just send me a message or use /help to see what I can do\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐾 *OpenClaw Capabilities*\n\n"
        "🔍 Web Search\n"
        "💻 Code Execution (Python)\n"
        "🐚 Shell Commands\n"
        "📁 File Read/Write\n"
        "🖥️ System Info\n\n"
        "Commands:\n"
        "/start — Welcome\n"
        "/reset — Clear conversation\n"
        "/help — This message",
        parse_mode=ParseMode.MARKDOWN
    )


async def reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sid = f"telegram-{update.effective_chat.id}"
    async with httpx.AsyncClient() as c:
        await c.delete(f"{CORE}/api/chat/{sid}")
    await update.message.reply_text("🔄 Conversation reset.")


async def chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return
    sid = f"telegram-{update.effective_chat.id}"
    await ctx.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    reply = await ask_openclaw(text, sid)
    # Telegram max message length is 4096
    for i in range(0, len(reply), 4000):
        await update.message.reply_text(reply[i:i+4000])


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[telegram] Starting Telegram bot…")
    app = (
        ApplicationBuilder()
        .token(cfg.TELEGRAM_TOKEN)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  help_cmd))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling(drop_pending_updates=True)
