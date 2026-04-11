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

const proxy = httpProxy.createProxyServer({ target: GATEWAY_URL, changeOrigin: true });

const server = http.createServer((req, res) => {
    // Health check endpoint (no auth)
    if (req.url === '/healthz') {
        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end('OK');
        return;
    }

    if (AUTH_ENABLED) {
        const authHeader = req.headers.authorization;
        if (!authHeader) {
            res.writeHead(401, {
                'WWW-Authenticate': 'Basic realm="OpenClaw Gateway"',
                'Content-Type': 'text/html'
            });
            res.end('<html><body>Access denied. Please provide credentials.</body></html>');
            return;
        }

        const base64 = authHeader.split(' ')[1];
        const [user, pass] = Buffer.from(base64, 'base64').toString().split(':');
        if (user !== WEBUI_USERNAME || pass !== WEBUI_PASSWORD) {
            res.writeHead(403, { 'Content-Type': 'text/html' });
            res.end('<html><body>Invalid username or password.</body></html>');
            return;
        }
    }

    // Proxy to OpenClaw gateway
    proxy.web(req, res, {}, (err) => {
        console.error('Proxy error:', err);
        res.writeHead(502, { 'Content-Type': 'text/plain' });
        res.end('Gateway unavailable');
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