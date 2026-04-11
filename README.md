# OpenClaw Docker – Secure, Encrypted, Production‑Ready

**Run OpenClaw anywhere – especially on ClawCloud Run – with built‑in HTTP Basic Auth (popup login) and full data encryption at rest.**

## 🔐 Security Features

- **Web UI password popup** – no hardcoded tokens, simple login page.
- **AES‑256‑GCM encryption** for all configuration and sensitive data (`openclaw.json`, custom routers, models). Encryption key is passed via `ENCRYPTION_KEY` environment variable.
- **Non‑root user** (UID 1000) – follows Docker best practices.
- **Automatic permission fixing** on volumes – works flawlessly on ClawCloud Run.
- **Gateway bound to localhost** – only the auth proxy is exposed.

## 🚀 Quick Start

```bash
# Clone your repo
git clone https://github.com/tanishvedreddyk/openclaw.git
cd openclaw

# Copy and edit environment variables
cp .env.example .env
# Generate an encryption key (optional but recommended)
openssl rand -base64 32 >> .env   # append as ENCRYPTION_KEY=...

# Start the container
docker-compose up -d