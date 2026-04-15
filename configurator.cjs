#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { encryptFile, decryptFile } = require('./encrypt-utils.cjs');

const CONFIG_PATH = process.env.OPENCLAW_CONFIG_PATH || '/data/.openclaw/openclaw.json';
const STATE_DIR = process.env.OPENCLAW_STATE_DIR || '/data/.openclaw';
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY;

if (!fs.existsSync(STATE_DIR)) {
    fs.mkdirSync(STATE_DIR, { recursive: true });
}

let config = {};
if (ENCRYPTION_KEY && fs.existsSync(`${CONFIG_PATH}.enc`)) {
    try {
        const decrypted = decryptFile(`${CONFIG_PATH}.enc`, ENCRYPTION_KEY);
        config = JSON.parse(decrypted);
    } catch (e) {
        console.warn('Could not decrypt existing config, starting fresh');
    }
} else if (fs.existsSync(CONFIG_PATH)) {
    try {
        config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
    } catch (e) {
        console.warn('Could not parse existing config, starting fresh');
    }
}

function setNested(obj, path, value) {
    const keys = path.split('.');
    let current = obj;
    for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {};
        current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = value;
}

// Gateway settings
if (process.env.OPENCLAW_GATEWAY_PORT) {
    setNested(config, 'gateway.port', parseInt(process.env.OPENCLAW_GATEWAY_PORT));
}
if (process.env.OPENCLAW_GATEWAY_BIND) {
    setNested(config, 'gateway.bind', process.env.OPENCLAW_GATEWAY_BIND);
}
if (process.env.OPENCLAW_GATEWAY_PASSWORD) {
    setNested(config, 'gateway.auth.password', process.env.OPENCLAW_GATEWAY_PASSWORD);
}
if (process.env.OPENCLAW_GATEWAY_MODE) {
    setNested(config, 'gateway.mode', process.env.OPENCLAW_GATEWAY_MODE);
}
if (process.env.OPENCLAW_MODELS_MODE) {
    setNested(config, 'models.mode', process.env.OPENCLAW_MODELS_MODE);
}

// AI Providers
const providers = [
    { name: 'anthropic', key: 'ANTHROPIC_API_KEY', baseUrl: 'https://api.anthropic.com', apiType: 'anthropic-messages' },
    { name: 'openai', key: 'OPENAI_API_KEY', baseUrl: 'https://api.openai.com/v1', apiType: 'openai-completions' },
    { name: 'openrouter', key: 'OPENROUTER_API_KEY', baseUrl: 'https://openrouter.ai/api/v1', apiType: 'openai-completions' },
    { name: 'gemini', key: 'GEMINI_API_KEY', baseUrl: 'https://generativelanguage.googleapis.com', apiType: 'openai-completions' },
    { name: 'groq', key: 'GROQ_API_KEY', baseUrl: 'https://api.groq.com/openai/v1', apiType: 'openai-completions' },
    { name: 'mistral', key: 'MISTRAL_API_KEY', baseUrl: 'https://api.mistral.ai/v1', apiType: 'openai-completions' },
    { name: 'xai', key: 'XAI_API_KEY', baseUrl: 'https://api.x.ai/v1', apiType: 'openai-completions' },
    { name: 'nvidia', key: 'NVIDIA_API_KEY', baseUrl: 'https://integrate.api.nvidia.com/v1', apiType: 'openai-completions' }
];

providers.forEach(provider => {
    const apiKey = process.env[provider.key];
    if (apiKey) {
        if (!config.models) config.models = { mode: 'merge', providers: {} };
        if (!config.models.providers) config.models.providers = {};
        config.models.providers[provider.name] = {
            apiKey: apiKey,
            baseUrl: process.env[`${provider.key.replace('_API_KEY', '_BASE_URL')}`] || provider.baseUrl,
            api: provider.apiType,
            models: parseModels(process.env[`${provider.name.toUpperCase()}_MODELS`])
        };
    }
});

if (process.env.OPENCLAW_PRIMARY_MODEL) {
    setNested(config, 'agents.defaults.model.primary', process.env.OPENCLAW_PRIMARY_MODEL);
}
if (process.env.OPENCLAW_WORKSPACE_DIR) {
    setNested(config, 'agents.defaults.workspace', path.join(process.env.OPENCLAW_WORKSPACE_DIR, 'shared'));
}
if (process.env.DISCORD_BOT_TOKEN) {
    setNested(config, 'channels.discord.enabled', true);
    setNested(config, 'channels.discord.botToken', process.env.DISCORD_BOT_TOKEN);
    if (process.env.DISCORD_DM_POLICY) setNested(config, 'channels.discord.dmPolicy', process.env.DISCORD_DM_POLICY);
    if (process.env.DISCORD_ALLOW_FROM) setNested(config, 'channels.discord.allowFrom', process.env.DISCORD_ALLOW_FROM.split(','));
}
if (process.env.TELEGRAM_BOT_TOKEN) {
    setNested(config, 'channels.telegram.enabled', true);
    setNested(config, 'channels.telegram.botToken', process.env.TELEGRAM_BOT_TOKEN);
}
if (process.env.SLACK_BOT_TOKEN) {
    setNested(config, 'channels.slack.enabled', true);
    setNested(config, 'channels.slack.botToken', process.env.SLACK_BOT_TOKEN);
    if (process.env.SLACK_APP_TOKEN) setNested(config, 'channels.slack.appToken', process.env.SLACK_APP_TOKEN);
}

fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
console.log('Configuration written to', CONFIG_PATH);

function parseModels(modelsStr) {
    if (!modelsStr) return [];
    try {
        const parsed = JSON.parse(modelsStr);
        if (Array.isArray(parsed)) {
            return parsed.map(m => {
                if (typeof m === 'string') return { id: m.trim(), name: m.trim() };
                if (m && typeof m === 'object') return { id: m.id, name: m.name || m.id };
                return null;
            }).filter(Boolean);
        }
    } catch (e) {
        // Not JSON, fall through
    }
    return modelsStr.split(',').map(id => ({ id: id.trim(), name: id.trim() })).filter(m => m.id);
}
