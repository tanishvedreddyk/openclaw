const http = require('http');
const httpProxy = require('http-proxy');
const url = require('url');

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://127.0.0.1:18789';
const AUTH_ENABLED = process.env.AUTH_ENABLED !== 'false';
const WEBUI_USERNAME = process.env.WEBUI_USERNAME || 'admin';
const WEBUI_PASSWORD = process.env.WEBUI_PASSWORD || '';

if (AUTH_ENABLED && !WEBUI_PASSWORD) {
    console.error('ERROR: AUTH_ENABLED=true but WEBUI_PASSWORD not set');
    process.exit(1);
}

// Simple rate limiting (optional)
const rateLimit = new Map();
const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute
const RATE_LIMIT_MAX = 30; // 30 attempts per minute

function isRateLimited(ip) {
    const now = Date.now();
    const record = rateLimit.get(ip) || { count: 0, reset: now + RATE_LIMIT_WINDOW };
    if (now > record.reset) {
        record.count = 1;
        record.reset = now + RATE_LIMIT_WINDOW;
        rateLimit.set(ip, record);
        return false;
    }
    record.count++;
    rateLimit.set(ip, record);
    return record.count > RATE_LIMIT_MAX;
}

const proxy = httpProxy.createProxyServer({ target: GATEWAY_URL, changeOrigin: true });

// Handle proxy errors without crashing
proxy.on('error', (err, req, res) => {
    console.error('Proxy error:', err.message);
    if (!res.headersSent) {
        res.writeHead(502, { 'Content-Type': 'text/plain' });
        res.end('Gateway unavailable');
    }
});

const server = http.createServer((req, res) => {
    // Health check endpoint (no auth)
    if (req.url === '/healthz') {
        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end('OK');
        return;
    }

    if (AUTH_ENABLED) {
        const ip = req.socket.remoteAddress;
        if (isRateLimited(ip)) {
            res.writeHead(429, { 'Content-Type': 'text/plain' });
            res.end('Too many authentication attempts');
            return;
        }

        const authHeader = req.headers.authorization;
        if (!authHeader) {
            res.writeHead(401, {
                'WWW-Authenticate': 'Basic realm="OpenClaw Gateway"',
                'Content-Type': 'text/html'
            });
            res.end('<html><body>Access denied. Please provide credentials.</body></html>');
            return;
        }

        // Validate header format
        const parts = authHeader.split(' ');
        if (parts.length !== 2 || parts[0] !== 'Basic') {
            res.writeHead(400, { 'Content-Type': 'text/plain' });
            res.end('Malformed Authorization header');
            return;
        }

        let decoded;
        try {
            decoded = Buffer.from(parts[1], 'base64').toString();
        } catch (e) {
            res.writeHead(400, { 'Content-Type': 'text/plain' });
            res.end('Invalid base64 in Authorization header');
            return;
        }

        const colonIndex = decoded.indexOf(':');
        if (colonIndex === -1) {
            res.writeHead(400, { 'Content-Type': 'text/plain' });
            res.end('Missing colon in credentials');
            return;
        }

        const user = decoded.substring(0, colonIndex);
        const pass = decoded.substring(colonIndex + 1);
        if (user !== WEBUI_USERNAME || pass !== WEBUI_PASSWORD) {
            res.writeHead(403, { 'Content-Type': 'text/html' });
            res.end('<html><body>Invalid username or password.</body></html>');
            return;
        }
    }

    proxy.web(req, res, {}, (err) => {
        // This callback handles errors during proxying
        console.error('Proxy request error:', err.message);
        if (!res.headersSent) {
            res.writeHead(502, { 'Content-Type': 'text/plain' });
            res.end('Gateway unavailable');
        }
    });
});

server.on('error', (err) => {
    console.error('Proxy server error:', err);
});

const PORT = process.env.PORT || 8080;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`Auth proxy listening on port ${PORT}`);
    console.log(`Proxying to ${GATEWAY_URL}`);
    if (AUTH_ENABLED) {
        console.log(`Basic auth enabled for user: ${WEBUI_USERNAME}`);
    } else {
        console.log('Authentication disabled');
    }
});
