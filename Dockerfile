# ──────────────────────────────────────────────────────────────────────────────
# OpenClaw — ghcr.io/tanishvedreddyk/openclaw
# Ubuntu 24.04 · Python 3.12 · Node.js 22
# Runs as root · No permission restrictions
# LLM backend: set via env vars (OpenAI, Nvidia NIM, or any OpenAI-compatible)
# ──────────────────────────────────────────────────────────────────────────────
FROM ubuntu:24.04

LABEL org.opencontainers.image.title="OpenClaw"
LABEL org.opencontainers.image.description="Powerful multi-platform AI assistant"
LABEL org.opencontainers.image.source="https://github.com/tanishvedreddyk/openclaw"
LABEL org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── System packages ───────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python
    python3.12 python3-pip python3.12-dev python3-venv \
    # Node.js setup
    curl ca-certificates gnupg \
    # Tools
    git wget zip unzip jq htop ffmpeg nmap \
    netcat-openbsd iputils-ping dnsutils \
    build-essential supervisor \
    && rm -rf /var/lib/apt/lists/*

# ── Node.js 22 ────────────────────────────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# ── App code ──────────────────────────────────────────────────────────────────
WORKDIR /app
COPY . /app

# Pre-install WhatsApp node deps at build time
RUN cd /app/bots/whatsapp && npm install --silent && cd /app

# ── Workspace for file operations ─────────────────────────────────────────────
RUN mkdir -p /workspace

# ── Make startup script executable ───────────────────────────────────────────
RUN chmod +x /app/start.sh

# ── Expose port ───────────────────────────────────────────────────────────────
EXPOSE 8080

# ── Healthcheck ───────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:8080/api/health || exit 1

# ── Run ───────────────────────────────────────────────────────────────────────
CMD ["/app/start.sh"]
