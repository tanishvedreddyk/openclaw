#!/bin/bash
set -e

# Fix permissions if running as root
if [ "$(id -u)" = "0" ]; then
    echo "Fixing permissions on /data (running as root)"
    chown -R openclaw:openclaw /data
    echo "Dropping privileges to openclaw user"
    exec gosu openclaw "$0" "$@"
fi

echo "Running as user: $(id -u)"

# Create required directories
mkdir -p "$OPENCLAW_STATE_DIR" "$OPENCLAW_WORKSPACE_DIR" "$OPENCLAW_WORKSPACE_DIR/shared"

# Decrypt configuration if ENCRYPTION_KEY is set
if [ -n "$ENCRYPTION_KEY" ] && [ -f "${OPENCLAW_CONFIG_PATH}.enc" ]; then
    echo "Decrypting configuration..."
    node /app/encrypt-utils.js decrypt "$OPENCLAW_CONFIG_PATH.enc" "$OPENCLAW_CONFIG_PATH"
fi

# Generate/merge config from environment variables (this writes plaintext then re-encrypts)
node /app/configurator.js

# Re-encrypt config if ENCRYPTION_KEY is set
if [ -n "$ENCRYPTION_KEY" ]; then
    echo "Encrypting configuration..."
    node /app/encrypt-utils.js encrypt "$OPENCLAW_CONFIG_PATH" "$OPENCLAW_CONFIG_PATH.enc"
    rm -f "$OPENCLAW_CONFIG_PATH"  # remove plaintext
fi

# Persistent memory files – unencrypted (workspace data)
if [ ! -f "$OPENCLAW_WORKSPACE_DIR/shared/GOALS.md" ]; then
    echo "Initializing memory files (first start)"
    touch "$OPENCLAW_WORKSPACE_DIR/shared/GOALS.md"
    touch "$OPENCLAW_WORKSPACE_DIR/shared/DECISIONS.md"
    touch "$OPENCLAW_WORKSPACE_DIR/shared/MEMORY.md"
    touch "$OPENCLAW_WORKSPACE_DIR/shared/PROJECT_STATUS.md"
else
    echo "Memory files already exist – preserving previous state"
fi

# Copy custom router / models (also encrypt if key present)
if [ -f "/data/config/router.js" ]; then
    cp /data/config/router.js "$OPENCLAW_STATE_DIR/router.js"
    echo "Custom router.js loaded"
    if [ -n "$ENCRYPTION_KEY" ]; then
        node /app/encrypt-utils.js encrypt "$OPENCLAW_STATE_DIR/router.js" "$OPENCLAW_STATE_DIR/router.js.enc"
        rm -f "$OPENCLAW_STATE_DIR/router.js"
    fi
fi

if [ -f "/data/config/models.json" ]; then
    cp /data/config/models.json "$OPENCLAW_STATE_DIR/models.json"
    echo "Custom models.json loaded"
    if [ -n "$ENCRYPTION_KEY" ]; then
        node /app/encrypt-utils.js encrypt "$OPENCLAW_STATE_DIR/models.json" "$OPENCLAW_STATE_DIR/models.json.enc"
        rm -f "$OPENCLAW_STATE_DIR/models.json"
    fi
fi

exec "$@"