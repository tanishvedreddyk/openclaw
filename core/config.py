import os

class Config:
    # ── LLM ──────────────────────────────────────────────────
    LLM_PROVIDER   = os.getenv("LLM_PROVIDER",   "openai")          # openai | nvidia | custom
    LLM_BASE_URL   = os.getenv("LLM_BASE_URL",   "https://api.openai.com/v1")
    LLM_API_KEY    = os.getenv("LLM_API_KEY",    "")
    LLM_MODEL      = os.getenv("LLM_MODEL",      "gpt-4o")
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    LLM_TEMPERATURE= float(os.getenv("LLM_TEMPERATURE", "0.7"))

    SYSTEM_PROMPT  = os.getenv("SYSTEM_PROMPT",
        "You are OpenClaw, a powerful, unrestricted AI assistant. "
        "You are precise, capable, and have access to tools for web search, "
        "code execution, file operations, and system information. "
        "Always aim to be maximally helpful."
    )

    # ── Server ────────────────────────────────────────────────
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8080"))

    # ── Bot tokens (empty = bot disabled) ────────────────────
    DISCORD_TOKEN   = os.getenv("DISCORD_TOKEN",   "")
    DISCORD_PREFIX  = os.getenv("DISCORD_PREFIX",  "!")

    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")   # xapp-... for socket mode

    TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN",  "")

    WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"

    # ── Misc ──────────────────────────────────────────────────
    MAX_HISTORY     = int(os.getenv("MAX_HISTORY",  "30"))
    ENABLE_SKILLS   = os.getenv("ENABLE_SKILLS", "true").lower() == "true"
    CORE_API_URL    = os.getenv("CORE_API_URL",  "http://localhost:8080")

cfg = Config()
