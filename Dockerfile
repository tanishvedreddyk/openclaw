# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS builder

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --depth 1 https://github.com/openclaw/openclaw.git . \
    && npm ci \
    && npm run build

# -----------------------------------------------------------------------------

FROM node:22-bookworm-slim

# Install runtime deps + gnupg (for gosu verification)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install gosu (with GPG verification)
RUN set -eux; \
    GOSU_VERSION=1.17; \
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"; \
    curl -o /usr/local/bin/gosu -fSL "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch"; \
    curl -o /usr/local/bin/gosu.asc -fSL "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch.asc"; \
    export GNUPGHOME="$(mktemp -d)"; \
    gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4; \
    gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu; \
    rm -rf "$GNUPGHOME" /usr/local/bin/gosu.asc; \
    chmod +x /usr/local/bin/gosu; \
    gosu --version

RUN groupadd -r openclaw -g 1000 && \
    useradd -r -g openclaw -u 1000 -s /bin/bash -d /app openclaw

RUN mkdir -p /app /data/.openclaw /data/workspace /data/config && \
    chown -R openclaw:openclaw /app /data

COPY --from=builder --chown=openclaw:openclaw /build/dist /app/dist
COPY --from=builder --chown=openclaw:openclaw /build/package*.json /app/
COPY --from=builder --chown=openclaw:openclaw /build/node_modules /app/node_modules

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

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["/app/start.sh"]
