# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS builder

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Pin to a specific release (change as needed)
ARG OPENCLAW_VERSION=v2026.4.12
WORKDIR /build
RUN git clone --depth 1 --branch ${OPENCLAW_VERSION} https://github.com/openclaw/openclaw.git . \
    && npm install -g pnpm \
    && pnpm install \
    && pnpm run build

# Debug: list built files to help find the entry point
RUN echo "=== Contents of /build/dist ===" && ls -la /build/dist/ || true
RUN echo "=== Looking for possible entry points ===" && \
    find /build/dist -name "*.js" -type f | head -20 || true

# -----------------------------------------------------------------------------

FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install gosu with retry for keyserver
RUN set -eux; \
    GOSU_VERSION=1.17; \
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"; \
    curl -o /usr/local/bin/gosu -fSL "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch"; \
    curl -o /usr/local/bin/gosu.asc -fSL "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch.asc"; \
    export GNUPGHOME="$(mktemp -d)"; \
    for i in 1 2 3; do \
        gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 && break || sleep 5; \
    done; \
    gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu; \
    rm -rf "$GNUPGHOME" /usr/local/bin/gosu.asc; \
    chmod +x /usr/local/bin/gosu; \
    gosu --version

# Rename existing 'node' user to 'openclaw'
RUN groupmod -n openclaw node && \
    usermod -d /app -s /bin/bash -l openclaw node && \
    mkdir -p /app /data/.openclaw /data/workspace /data/config && \
    chown -R openclaw:openclaw /app /data

# Copy built application
COPY --from=builder --chown=openclaw:openclaw /build/dist /app/dist
COPY --from=builder --chown=openclaw:openclaw /build/package*.json /app/
COPY --from=builder --chown=openclaw:openclaw /build/node_modules /app/node_modules

# Copy scripts
COPY --chown=openclaw:openclaw docker-entrypoint.sh /usr/local/bin/
COPY --chown=openclaw:openclaw configurator.js /app/
COPY --chown=openclaw:openclaw encrypt-utils.js /app/
COPY --chown=openclaw:openclaw auth-proxy.js /app/
COPY --chown=openclaw:openclaw start.sh /app/

RUN chmod +x /usr/local/bin/docker-entrypoint.sh /app/start.sh

ENV NODE_ENV=production \
    OPENCLAW_STATE_DIR=/data/.openclaw \
    OPENCLAW_WORKSPACE_DIR=/data/workspace \
    OPENCLAW_CONFIG_PATH=/data/.openclaw/openclaw.json \
    OPENCLAW_GATEWAY_PORT=18789 \
    OPENCLAW_GATEWAY_BIND=127.0.0.1 \
    PORT=8080 \
    WEBUI_USERNAME=admin \
    ENCRYPTION_KEY="" \
    AUTH_ENABLED=true

EXPOSE 8080
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

USER openclaw

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["/app/start.sh"]
