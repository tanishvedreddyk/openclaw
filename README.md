```markdown
# OpenClaw Docker

Production-ready Docker container for OpenClaw - an open-source AI assistant with persistent memory, encryption at rest, and built-in authentication.

## What is OpenClaw?

**OpenClaw** is an open-source AI assistant that enables you to interact with advanced language models through a unified interface. With OpenClaw, you can:

- **Centralize AI interactions**: Access Claude (Anthropic), GPT-4 (OpenAI), Gemini (Google), Groq, Mistral, and xAI through a single gateway
- **Connect multiple platforms**: Use the same assistant on Discord, Telegram, Slack, or through the secure web interface
- **Maintain persistent memory**: Agent memory survives container restarts through Markdown-based memory files
- **Deploy securely**: Built-in HTTP Basic Auth, AES-256-GCM encryption at rest, and non-root container execution
- **Self-host with confidence**: Production-ready with automatic permission fixing, health checks, and multi-architecture support

### Key Features

- **Secure by Default**: HTTP Basic Authentication with browser popup (no tokens in URLs)
- **Encryption at Rest**: AES-256-GCM encryption for sensitive configuration files
- **Persistent Memory**: GOALS.md, DECISIONS.md, MEMORY.md, and PROJECT_STATUS.md survive restarts
- **Permission Fixing**: Automatic volume ownership correction for root-mounted volumes (ClawCloud Run/Kubernetes compatible)
- **Multi-Architecture**: Supports both `linux/amd64` and `linux/arm64`
- **Multi-Provider**: Compatible with Anthropic, OpenAI, OpenRouter, Gemini, Groq, Mistral, xAI, and NVIDIA
- **CI/CD Ready**: GitHub Actions workflow for automated builds to GitHub Container Registry

## About this Docker Setup

This Docker configuration provides a production-hardened deployment of OpenClaw with features designed for serverless platforms and persistent volumes:

- **Auth Proxy Layer**: HTTP Basic Auth in front of the OpenClaw gateway (port 8080)
- **AES-256-GCM Encryption**: Optional encryption for API keys and configuration files
- **State Persistence**: Memory files and configuration stored in `/data` volume
- **Root-to-User Privilege Drop**: Entrypoint fixes permissions then runs as non-root `openclaw` user (UID 1000)
- **Multi-stage Build**: Optimized image size (~400MB) with Node.js 22 on Debian Bookworm
- **Health Checks**: Built-in `/healthz` endpoint for orchestration platforms

## Requirements

- Docker 20.10+ or Docker Compose v2+
- 2GB RAM minimum (4GB+ recommended for large model contexts)
- 10GB storage for image and persistent data
- At least one AI provider API key (Anthropic, OpenAI, OpenRouter, etc.)

## Quick Start

```bash
# 1. Clone the repository
git clone <your-repo> openclaw && cd openclaw

# 2. Configure environment variables
cp .env.example .env

# 3. Generate encryption key (optional but recommended)
openssl rand -base64 32
# Add to .env: ENCRYPTION_KEY=<generated-key>

# 4. Edit .env and add required settings:
# - WEBUI_PASSWORD (REQUIRED for Basic Auth)
# - ANTHROPIC_API_KEY or other provider API key
# - ENCRYPTION_KEY (optional, for config encryption)

# 5. Start the container
docker compose up -d

# 6. Access the web interface
open http://localhost:8080
# Login with username: admin (or WEBUI_USERNAME)
# Password: your WEBUI_PASSWORD from .env
```

> **Important:**
>
> - `WEBUI_PASSWORD` is **required**. The container will fail to start if `AUTH_ENABLED=true` (default) and password is empty
> - If you lose the `ENCRYPTION_KEY`, encrypted data cannot be recovered
> - The OpenClaw gateway runs internally on port 18789; only port 8080 (auth proxy) is exposed

## Project Structure

```
.
├── Dockerfile                    # Multi-stage build with gosu and security hardening
├── docker-compose.yml            # Service orchestration with resource limits
├── docker-entrypoint.sh          # Permission fixing, encryption, and initialization
├── start.sh                      # Process manager (gateway + auth proxy)
├── configurator.js               # Environment variable to JSON config merger
├── encrypt-utils.js              # AES-256-GCM encryption/decryption utility
├── auth-proxy.js                 # HTTP Basic Auth proxy server
├── .env.example                  # Environment variables template
├── .dockerignore                 # Build context exclusions
├── .github/
│   └── workflows/
│       └── docker-build.yml      # CI/CD pipeline for GHCR
└── README.md                     # This file
```

### Key Files

- **Dockerfile**: Multi-stage build compiling OpenClaw from source, installing `gosu` for privilege dropping, and setting up security layers
- **docker-entrypoint.sh**: Initialization script that fixes volume permissions (root→openclaw), handles encryption lifecycle, creates memory files, and merges environment configuration
- **configurator.js**: Translates environment variables (API keys, model settings) into OpenClaw's JSON configuration format
- **encrypt-utils.js**: Provides CLI and programmatic AES-256-GCM encryption for sensitive files
- **auth-proxy.js**: Node.js HTTP proxy providing Basic Auth on port 8080, forwarding to gateway on 127.0.0.1:18789
- **start.sh**: Process supervisor that starts the gateway in background then executes the auth proxy as PID 1

## How it Works

### Architecture Flow

The container uses a layered security architecture:

1. **Entrypoint Initialization** (`docker-entrypoint.sh`):
   - If running as root, `chown`s `/data` to `openclaw:openclaw` and re-executes as non-root user
   - Decrypts existing config (`openclaw.json.enc`) if `ENCRYPTION_KEY` is set
   - Runs `configurator.js` to merge environment variables into `openclaw.json`
   - Re-encrypts config and removes plaintext if encryption enabled
   - Creates memory files (`GOALS.md`, `DECISIONS.md`, `MEMORY.md`, `PROJECT_STATUS.md`) if missing

2. **Process Startup** (`start.sh`):
   - Decrypts custom `router.js` or `models.json` if encrypted
   - Starts OpenClaw gateway on `127.0.0.1:18789` (background)
   - Waits 5 seconds for gateway readiness
   - Executes auth proxy on `0.0.0.0:8080` (PID 1)

3. **Request Flow**:
   - User → Port 8080 → Auth Proxy → Basic Auth Check → Gateway (18789)
   - Health checks bypass auth at `/healthz`

### Security Model

- **Network Isolation**: Gateway binds only to localhost; external access via auth proxy
- **File Permissions**: All persistent data owned by `openclaw` user (UID 1000)
- **Encryption**: Sensitive configs encrypted with AES-256-GCM using 32-byte base64 key
- **Authentication**: HTTP Basic Auth (fail-safe: container exits if password empty)

## Configuration

### Environment Variables

Edit the `.env` file with your credentials:

#### Web UI Authentication (REQUIRED)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEBUI_PASSWORD` | **Yes** | - | Password for Basic Auth popup |
| `WEBUI_USERNAME` | No | `admin` | Username for Basic Auth |
| `AUTH_ENABLED` | No | `true` | Set to `false` to disable auth (not recommended) |

#### AI Providers (at least one required)

| Variable | Provider | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic | Claude API access |
| `OPENAI_API_KEY` | OpenAI | GPT-4/GPT-3.5 access |
| `OPENROUTER_API_KEY` | OpenRouter | Multi-model proxy access |
| `GEMINI_API_KEY` | Google | Gemini models |
| `GROQ_API_KEY` | Groq | Fast inference API |
| `MISTRAL_API_KEY` | Mistral | Mistral models |
| `XAI_API_KEY` | xAI | Grok models |
| `NVIDIA_API_KEY` | NVIDIA | NIM models |

#### Encryption & Security

| Variable | Required | Description |
|----------|----------|-------------|
| `ENCRYPTION_KEY` | No | Base64-encoded 32-byte key for AES-256-GCM |
| `OPENCLAW_GATEWAY_TOKEN` | No | Internal gateway token (auto-generated if empty) |

#### Model Configuration

| Variable | Description |
|----------|-------------|
| `OPENCLAW_PRIMARY_MODEL` | Default model (e.g., `anthropic/claude-sonnet-4`) |
| `OPENCLAW_MODELS_MODE` | `merge` or `replace` for custom models |

#### Channel Integrations (optional)

| Variable | Platform |
|----------|----------|
| `DISCORD_BOT_TOKEN` | Discord bot token |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `SLACK_BOT_TOKEN` | Slack bot OAuth token |
| `SLACK_APP_TOKEN` | Slack app-level token |

### Custom Configuration Files

You can mount custom files to `/data/config` (read-only):

- `router.js` - Custom routing logic
- `models.json` - Custom model definitions

These will be copied to the state directory and encrypted if `ENCRYPTION_KEY` is set.

## Security Features

### Encryption at Rest

When `ENCRYPTION_KEY` is provided:

1. Configuration files are encrypted with AES-256-GCM after each modification
2. Plaintext files exist only briefly during startup (in memory)
3. Files encrypted: `openclaw.json`, `router.js`, `models.json`
4. Files NOT encrypted: Memory markdown files (intentionally human-readable)

Generate a key:
```bash
openssl rand -base64 32
```

### Authentication Flow

The auth proxy (`auth-proxy.js`) provides:

- Browser Basic Auth popup (standard HTTP 401 with `WWW-Authenticate` header)
- Credentials verified against `WEBUI_USERNAME` and `WEBUI_PASSWORD`
- Health check endpoint `/healthz` accessible without auth
- Failsafe: Container exits on startup if `AUTH_ENABLED=true` and `WEBUI_PASSWORD` is empty

## Persistent Memory

OpenClaw maintains agent state through Markdown files in `/data/workspace/shared/`:

| File | Purpose |
|------|---------|
| `GOALS.md` | Long-term objectives and mission |
| `DECISIONS.md` | Architectural decisions and reasoning |
| `MEMORY.md` | Conversational context and facts |
| `PROJECT_STATUS.md` | Current project state and progress |

These files are created once and never overwritten by the container. They persist across restarts, allowing the AI to maintain long-term memory even if the container is destroyed and recreated.

## Accessing the Web Interface

### Standard Access

1. Navigate to `http://localhost:8080` (or your server URL)
2. Browser will show Basic Auth popup automatically
3. Enter username (default: `admin`) and your `WEBUI_PASSWORD`
4. Interface loads with persistent memory intact

### Health Checks

The container exposes an unauthenticated health endpoint:

```bash
curl http://localhost:8080/healthz
# Returns: 200 OK
```

Use this for Docker health checks, Kubernetes liveness probes, or load balancer checks.

## Deployment on ClawCloud Run

This image is optimized for ClawCloud Run and similar serverless container platforms:

1. **Create App**: Choose "Deploy from container registry"
   - Image: `ghcr.io/tanishvedreddyk/openclaw:latest`
   - Port: `8080`

2. **Environment Variables**:
   - Set `WEBUI_PASSWORD` (required)
   - Set at least one AI provider API key
   - Optionally set `ENCRYPTION_KEY`

3. **Persistent Storage**:
   - Add volume mounted at `/data`
   - Recommended size: 10GB

4. **Deploy**: Platform will automatically use the health check endpoint

The entrypoint automatically handles root-mounted volumes (common in serverless platforms) by fixing permissions before dropping to the `openclaw` user.

## Monitoring and Logs

### View Logs

```bash
# Real-time logs
docker logs -f openclaw

# View only auth proxy logs
docker logs openclaw | grep "Auth proxy"

# Check gateway logs
docker logs openclaw | grep "gateway"
```

### Check Health

```bash
# Docker healthcheck
docker inspect --format='{{.State.Health.Status}}' openclaw

# Manual health check
curl -f http://localhost:8080/healthz || echo "Unhealthy"
```

### Enter Container

```bash
# Shell as openclaw user
docker exec -it openclaw bash

# View memory files
docker exec openclaw cat /data/workspace/shared/MEMORY.md
```

## Useful Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Restart with fresh build
docker compose up -d --build

# View running processes
docker exec openclaw ps aux

# Backup persistent data
docker run --rm -v openclaw-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/openclaw-backup.tar.gz -C /data .

# Restore from backup
docker run --rm -v openclaw-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/openclaw-backup.tar.gz -C /data

# Force recreate with new image
docker compose pull && docker compose up -d --force-recreate
```

## Setting Up Integrations

### Discord

1. Go to https://discord.com/developers/applications
2. Create application → Bot → Reset Token
3. Enable intents: Message Content, Server Members, Presence
4. Add to `.env`: `DISCORD_BOT_TOKEN=your_token`
5. Restart container: `docker compose restart`

### Telegram

1. Message @BotFather on Telegram
2. Send `/newbot` and follow instructions
3. Copy the token to `.env`: `TELEGRAM_BOT_TOKEN=your_token`
4. Restart container

### Slack

1. Go to https://api.slack.com/apps and create app
2. OAuth & Permissions: Add scopes `chat:write`, `channels:history`, `users:read`
3. Install to workspace
4. Add to `.env`:
   - `SLACK_BOT_TOKEN=xoxb-...`
   - `SLACK_APP_TOKEN=xapp-...`
5. Restart container

## Volumes and Persistence

| Volume | Container Path | Description |
|--------|---------------|-------------|
| `openclaw-data` | `/data` | All persistent state (config, workspace, memory) |
| `./config` | `/data/config` | Optional custom configs (router.js, models.json) |

The `/data` directory structure:
```
/data/
├── .openclaw/          # State directory (config, encrypted files)
├── workspace/
│   └── shared/         # Memory files (GOALS.md, etc.)
└── config/             # Custom router/models (optional)
```

### Backup Strategy

Since all state is in `/data`, simply backup this volume:

```bash
# Automated backup script
docker run --rm -v openclaw-data:/data -v /backups:/backup alpine \
  tar czf "/backup/openclaw-$(date +%Y%m%d).tar.gz" -C /data .
```

## Updating OpenClaw

Images are built automatically every 6 hours and pushed to GitHub Container Registry:

```bash
# Pull latest image
docker compose pull

# Recreate container with new image
docker compose up -d --force-recreate

# Verify new version
docker logs openclaw | grep "OpenClaw"
```

To use a specific version:
```bash
# Use a dated tag (YYYYMMDD format)
docker pull ghcr.io/tanishvedreddyk/openclaw:20260411
```

## Ports

| Port | Description |
|------|-------------|
| 8080 | HTTP Web Interface (Auth Proxy) - Expose this |
| 18789 | OpenClaw Gateway (internal only, localhost) |

## Troubleshooting

### Container exits immediately

**Cause**: Missing `WEBUI_PASSWORD` or invalid `ENCRYPTION_KEY`
**Solution**:
```bash
# Check logs
docker logs openclaw

# Ensure WEBUI_PASSWORD is set in .env
# If using encryption, generate valid key: openssl rand -base64 32
```

### "Unauthorized" or auth popup keeps reappearing

**Cause**: Wrong username/password or browser caching
**Solution**:
- Verify `WEBUI_USERNAME` (default: `admin`) and `WEBUI_PASSWORD` in `.env`
- Clear browser cache or use incognito mode
- Check that `AUTH_ENABLED` is not set to `false` unexpectedly

### "502 Bad Gateway" error

**Cause**: OpenClaw gateway failed to start
**Solution**:
```bash
# Check gateway logs
docker logs openclaw | grep -i error

# Verify API keys are valid
# Ensure sufficient memory (check container limits)
```

### Memory files reset on restart

**Cause**: Volume not persisted or fresh volume mounted
**Solution**:
- Ensure named volume `openclaw-data` is mounted at `/data`
- Check that memory files exist: `docker exec openclaw ls /data/workspace/shared/`
- Files are only created on first start; existing files are never overwritten

### Encryption errors

**Cause**: Key mismatch or data corruption
**Solution**:
- If `ENCRYPTION_KEY` is lost, you cannot recover encrypted data
- To start fresh: Remove `.enc` files from the volume and restart
- To disable encryption: Unset `ENCRYPTION_KEY` and delete `.enc` files

### Permission denied on ClawCloud Run

**Cause**: Volume mounted as root, but entrypoint didn't fix permissions
**Solution**:
- Verify entrypoint is running as root initially (check logs for "Fixing permissions")
- Ensure `gosu` is installed in image (should be in Dockerfile)
- Check that volume mount path is exactly `/data`

## Resources

- [OpenClaw GitHub](https://github.com/your-repo/openclaw)
- [GitHub Container Registry](https://github.com/tanishvedreddyk/openclaw/pkgs/container/openclaw)
- [ClawCloud Run Documentation](https://run.claw.cloud/docs)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [AES-256-GCM Encryption](https://developer.mozilla.org/en-US/docs/Web/API/AesGcmParams)

## License

This Docker packaging project is provided as-is under the MIT License. OpenClaw is an open-source project with its own license terms.
```

This README follows the structure and style of the reference, with clear sections for Quick Start, Configuration tables, Troubleshooting specific errors, and Deployment guides. It emphasizes your project's unique features: encryption at rest, persistent memory files, and the auth proxy layer.
