# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS builder

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

ARG OPENCLAW_VERSION=v2026.4.12
WORKDIR /build
RUN git clone --depth 1 --branch ${OPENCLAW_VERSION} https://github.com/openclaw/openclaw.git . \
    && npm install -g pnpm \
    && pnpm install \
    && pnpm run build

# -----------------------------------------------------------------------------

FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install gosu with retry
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

RUN groupmod -n openclaw node && \
    usermod -d /app -s /bin/bash -l openclaw node && \
    mkdir -p /app /data/.openclaw /data/workspace /data/config && \
    chown -R openclaw:openclaw /app /data

COPY --from=builder --chown=openclaw:openclaw /build/dist /app/dist
COPY --from=builder --chown=openclaw:openclaw /build/package*.json /app/
COPY --from=builder --chown=openclaw:openclaw /build/node_modules /app/node_modules

COPY --chown=openclaw:openclaw docker-entrypoint.sh /usr/local/bin/
COPY --chown=openclaw:openclaw configurator.js /app/
COPY --chown=openclaw:openclaw encrypt-utils.js /app/

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV NODE_ENV=production \
    OPENCLAW_STATE_DIR=/data/.openclaw \
    OPENCLAW_WORKSPACE_DIR=/data/workspace \
    OPENCLAW_CONFIG_PATH=/data/.openclaw/openclaw.json \
    OPENCLAW_GATEWAY_PORT=18789 \
    OPENCLAW_GATEWAY_BIND=lan \
    PORT=8080 \
    WEBUI_USERNAME=admin \
    ENCRYPTION_KEY=""

EXPOSE 8080
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:18789/healthz || exit 1

USER openclaw

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["node", "/app/dist/index.js", "gateway", "start"]
