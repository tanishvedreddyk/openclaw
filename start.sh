#!/bin/bash
set -e

trap 'kill -TERM $GATEWAY_PID 2>/dev/null; wait $GATEWAY_PID; exit 0' TERM INT

# Auto‑detect the gateway entry point
GATEWAY_CMD=""
if [ -f "/app/dist/gateway.js" ]; then
    GATEWAY_CMD="node /app/dist/gateway.js"
elif [ -f "/app/dist/index.js" ]; then
    GATEWAY_CMD="node /app/dist/index.js"
elif [ -f "/app/dist/cli.js" ]; then
    # OpenClaw CLI expects a subcommand, e.g., "gateway start"
    GATEWAY_CMD="node /app/dist/cli.js gateway start"
elif [ -f "/app/dist/main.js" ]; then
    GATEWAY_CMD="node /app/dist/main.js"
else
    echo "ERROR: Cannot find gateway entry point in /app/dist/"
    ls -la /app/dist/ || echo "dist folder missing"
    exit 1
fi

echo "Starting gateway with: $GATEWAY_CMD"
$GATEWAY_CMD &
GATEWAY_PID=$!

# Wait for gateway to become healthy (up to 30 seconds)
echo "Waiting for gateway to become healthy..."
for i in {1..30}; do
    if curl -s -f http://127.0.0.1:18789/healthz > /dev/null 2>&1; then
        echo "Gateway is healthy"
        break
    fi
    if ! kill -0 $GATEWAY_PID 2>/dev/null; then
        echo "Gateway process died unexpectedly"
        exit 1
    fi
    sleep 1
done

# Final health check
if ! curl -s -f http://127.0.0.1:18789/healthz > /dev/null 2>&1; then
    echo "Gateway failed to become healthy within 30 seconds"
    exit 1
fi

# Start auth proxy (replaces shell, becomes PID 1)
exec node /app/auth-proxy.js
