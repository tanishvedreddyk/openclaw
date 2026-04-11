#!/bin/bash
set -e

# If encryption is enabled, decrypt any other sensitive files (like router.js)
if [ -n "$ENCRYPTION_KEY" ]; then
    echo "Decrypting custom router if present..."
    if [ -f "${OPENCLAW_STATE_DIR}/router.js.enc" ]; then
        node /app/encrypt-utils.js decrypt "${OPENCLAW_STATE_DIR}/router.js.enc" "${OPENCLAW_STATE_DIR}/router.js"
    fi
    if [ -f "${OPENCLAW_STATE_DIR}/models.json.enc" ]; then
        node /app/encrypt-utils.js decrypt "${OPENCLAW_STATE_DIR}/models.json.enc" "${OPENCLAW_STATE_DIR}/models.json"
    fi
fi

# Start OpenClaw gateway in background (listens on 127.0.0.1:18789)
echo "Starting OpenClaw gateway..."
node /app/dist/gateway.js &
GATEWAY_PID=$!

# Wait a few seconds for gateway to be ready
sleep 5

# Start the auth proxy (runs on PORT 8080)
echo "Starting auth proxy..."
exec node /app/auth-proxy.js