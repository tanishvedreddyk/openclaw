"""
OpenClaw Slack Bot (Socket Mode — no public URL needed)
Listens for:
  - Direct messages
  - @mentions in channels
"""
import os, sys, httpx
sys.path.insert(0, "/app")
from core.config import cfg

if not cfg.SLACK_BOT_TOKEN or not cfg.SLACK_APP_TOKEN:
    print("[slack] SLACK_BOT_TOKEN or SLACK_APP_TOKEN not set — bot disabled.")
    sys.exit(0)

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=cfg.SLACK_BOT_TOKEN)
CORE = cfg.CORE_API_URL


def ask_openclaw(message: str, session_id: str) -> str:
    with httpx.Client(timeout=120) as c:
        r = c.post(f"{CORE}/api/chat",
                   json={"message": message, "session_id": session_id, "platform": "slack"})
        r.raise_for_status()
        return r.json()["reply"]


def slack_to_plain(text: str, client) -> str:
    """Remove Slack mention markup."""
    import re
    return re.sub(r'<@[A-Z0-9]+>', '', text).strip()


# ── Mention in channel ────────────────────────────────────────────────────────
@app.event("app_mention")
def handle_mention(event, say, client):
    text  = slack_to_plain(event.get("text", ""), client)
    sid   = f"slack-{event['channel']}"
    if not text:
        say("Hey! Ask me anything 🐾")
        return
    say(":hourglass: Thinking…")
    reply = ask_openclaw(text, sid)
    say(reply)


# ── DMs ───────────────────────────────────────────────────────────────────────
@app.event("message")
def handle_dm(event, say):
    if event.get("channel_type") != "im":
        return
    if event.get("subtype"):          # bot message, file share, etc
        return
    text = event.get("text", "").strip()
    if not text:
        return
    sid = f"slack-{event['user']}"
    say(":hourglass: Thinking…")
    reply = ask_openclaw(text, sid)
    say(reply)


# ── Slash command /openclaw ───────────────────────────────────────────────────
@app.command("/openclaw")
def handle_slash(ack, respond, command):
    ack()
    text = command.get("text", "").strip()
    if not text:
        respond("Usage: `/openclaw <your message>`")
        return
    sid = f"slack-{command['channel_id']}"
    respond(":hourglass: Thinking…")
    reply = ask_openclaw(text, sid)
    respond(reply)


if __name__ == "__main__":
    print("[slack] Starting Slack bot via Socket Mode…")
    handler = SocketModeHandler(app, cfg.SLACK_APP_TOKEN)
    handler.start()
