# 🐾 OpenClaw

A powerful, unrestricted, multi-platform AI assistant — packaged as a single Docker image.

[![Build & Push](https://github.com/tanishvedreddyk/openclaw/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/tanishvedreddyk/openclaw/actions)

```
docker pull ghcr.io/tanishvedreddyk/openclaw:latest
```

---

## Features

- **Multi-LLM** — Ollama (bundled), OpenAI, Nvidia NIM, or any OpenAI-compatible API
- **Multi-platform** — Discord, Slack, Telegram, WhatsApp, and a built-in web chat UI
- **Skills (function calling)** — Web search, Python execution, shell commands, file ops, system info
- **Root, unrestricted** — no permission drops inside the container
- **2 GB RAM / 4 CPU optimised** — resource limits pre-configured
- **Persistent sessions** — per-user/channel conversation history across all platforms

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/tanishvedreddyk/openclaw
cd openclaw

# 2. Configure
cp .env.example .env
nano .env          # fill in tokens + LLM backend

# 3. Run
docker compose up -d

# Web UI → http://localhost:8080
# Logs   → docker compose logs -f
```

---

## LLM Backends

| Provider | `LLM_BASE_URL` | Notes |
|----------|----------------|-------|
| **Ollama** (default) | `http://localhost:11434/v1` | Set `OLLAMA_ENABLED=true` to auto-start |
| OpenAI | `https://api.openai.com/v1` | Needs `LLM_API_KEY=sk-...` |
| Nvidia NIM | `https://integrate.api.nvidia.com/v1` | Needs `LLM_API_KEY=nvapi-...` |
| Custom | your endpoint | Any OpenAI-compatible API |

---

## Bot Setup

### Discord
1. [Create app](https://discord.com/developers/applications) → Bot → copy token
2. Enable **Message Content Intent**
3. Set `DISCORD_TOKEN=` in `.env`
4. Invite bot with scopes: `bot`, `applications.commands`

### Slack
1. [Create app](https://api.slack.com/apps) → Enable Socket Mode
2. Add scopes: `chat:write`, `app_mentions:read`, `im:history`, `commands`
3. Create slash command `/openclaw`
4. Set `SLACK_BOT_TOKEN` + `SLACK_APP_TOKEN` in `.env`

### Telegram
1. Message [@BotFather](https://t.me/BotFather) → `/newbot`
2. Set `TELEGRAM_TOKEN=` in `.env`

### WhatsApp
1. Set `WHATSAPP_ENABLED=true` in `.env`
2. On first run, scan the QR code printed to the container logs
3. Session is saved in `./auth_state/` — persists across restarts

---

## Skills

| Skill | Description |
|-------|-------------|
| `web_search` | Live internet search via DuckDuckGo |
| `run_code` | Execute Python code, return output |
| `run_shell` | Run bash commands |
| `read_file` | Read files from `/workspace` |
| `write_file` | Write files to `/workspace` |
| `list_files` | List files in workspace |
| `get_system_info` | CPU, RAM, disk, uptime, date |

Disable all skills: `ENABLE_SKILLS=false`

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web chat UI |
| `/api/health` | GET | Health check |
| `/api/models` | GET | List available models |
| `/api/chat` | POST | REST chat |
| `/api/chat/{session_id}` | DELETE | Clear session |
| `/ws/{session_id}` | WS | Streaming chat |

### REST Chat
```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "session_id": "my-session"}'
```

---

## Docker Image

```
ghcr.io/tanishvedreddyk/openclaw:latest   # always latest main
ghcr.io/tanishvedreddyk/openclaw:v1.0.0   # pinned version
ghcr.io/tanishvedreddyk/openclaw:sha-abc123  # specific commit
```

Built automatically via GitHub Actions on every push to `main`.  
Supports: `linux/amd64`, `linux/arm64`

---

## Run without Docker Compose

```bash
docker run -d \
  --name openclaw \
  --restart unless-stopped \
  -p 8080:8080 \
  -m 2g --cpus 4 \
  -v $(pwd)/workspace:/workspace \
  -v $(pwd)/auth_state:/app/bots/whatsapp/auth_state \
  --env-file .env \
  ghcr.io/tanishvedreddyk/openclaw:latest
```

---

## License

MIT
