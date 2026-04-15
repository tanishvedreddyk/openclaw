#!/usr/bin/env node
const crypto = require('crypto');
const fs = require('fs');

const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 12;

function validateKey(key) {
    const keyBuf = Buffer.from(key, 'base64');
    if (keyBuf.length !== 32) {
        throw new Error(`Invalid encryption key length: expected 32 bytes, got ${keyBuf.length}. Generate with: openssl rand -base64 32`);
    }
    return keyBuf;
}

function encrypt(text, key) {
    const keyBuf = validateKey(key);
    const iv = crypto.randomBytes(IV_LENGTH);
    const cipher = crypto.createCipheriv(ALGORITHM, keyBuf, iv);
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    const authTag = cipher.getAuthTag();
    return JSON.stringify({
        iv: iv.toString('hex'),
        authTag: authTag.toString('hex'),
        data: encrypted
    });
}

function decrypt(encryptedJson, key) {
    const keyBuf = validateKey(key);
    const obj = JSON.parse(encryptedJson);
    const iv = Buffer.from(obj.iv, 'hex');
    const authTag = Buffer.from(obj.authTag, 'hex');
    const decipher = crypto.createDecipheriv(ALGORITHM, keyBuf, iv);
    decipher.setAuthTag(authTag);
    let decrypted = decipher.update(obj.data, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
}

function encryptFile(inputFile, outputFile, key) {
    const plaintext = fs.readFileSync(inputFile, 'utf8');
    const encrypted = encrypt(plaintext, key);
    fs.writeFileSync(outputFile, encrypted, 'utf8');
}

function decryptFile(inputFile, outputFile, key) {
    const encrypted = fs.readFileSync(inputFile, 'utf8');
    const decrypted = decrypt(encrypted, key);
    fs.writeFileSync(outputFile, decrypted, 'utf8');
}

if (require.main === module) {
    const [,, cmd, input, output, keyArg] = process.argv;
    const key = keyArg || process.env.ENCRYPTION_KEY;
    if (!key) {
        console.error('ENCRYPTION_KEY not set');
        process.exit(1);
    }
    try {
        if (cmd === 'encrypt') {
            encryptFile(input, output, key);
            console.log(`Encrypted ${input} -> ${output}`);
        } else if (cmd === 'decrypt') {
            decryptFile(input, output, key);
            console.log(`Decrypted ${input} -> ${output}`);
        } else {
            console.error('Usage: encrypt-utils.js encrypt|decrypt <input> <output>');
            process.exit(1);
        }
    } catch (err) {
        console.error('Encryption error:', err.message);
        process.exit(1);
    }
}

module.exports = { encrypt, decrypt, encryptFile, decryptFile, validateKey };
