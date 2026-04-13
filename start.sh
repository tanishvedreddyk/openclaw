#!/bin/bash
set -e

# Trap SIGTERM and SIGINT for graceful shutdown
trap 'kill -TERM $GATEWAY_PID 2>/dev/null; wait $GATEWAY_PID; exit 0' TERM INT

# Start gateway in background
node /app/dist/gateway.js &
GATEWAY_PID=$!

# Wait for gateway to be healthy (up to 30 seconds)
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

# If gateway not healthy after loop, fail
if ! curl -s -f http://127.0.0.1:18789/healthz > /dev/null 2>&1; then
    echo "Gateway failed to become healthy within 30 seconds"
    exit 1
fi

# Start auth proxy (replaces shell, becomes PID 1)
exec node /app/auth-proxy.js
