#!/usr/bin/env node
/**
 * Decrypt Notion/Linear dump files encrypted by the at-rest encryption script.
 * Usage: node scripts/decrypt_dumps.js
 * Requires STACK_PASSWORD env var or interactive admin password.
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { readSync } = require('fs');

function prompt(query) {
  process.stdout.write(query);
  const buf = Buffer.alloc(1024);
  const n = readSync(0, buf, 0, 1024);
  return buf.toString('utf8', 0, n).trim();
}

const password = process.env.STACK_PASSWORD || prompt('🔐 Admin password: ');
const key = crypto.scryptSync(password, 'salt', 32);

const files = [
  'notion_full_dump.txt.enc',
  'notion_full_dump.json.enc',
  'linear_full_dump.txt.enc',
  'linear_full_dump.json.enc',
];

let decryptedCount = 0;

files.forEach((file) => {
  const p = path.join(process.cwd(), file);
  if (!fs.existsSync(p)) {
    console.log('Skipping (not found):', file);
    return;
  }

  const data = fs.readFileSync(p);
  const iv = data.subarray(0, 16);
  const authTag = data.subarray(16, 32);
  const encrypted = data.subarray(32);

  const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
  decipher.setAuthTag(authTag);

  try {
    const plaintext = Buffer.concat([decipher.update(encrypted), decipher.final()]);
    const outPath = p.replace('.enc', '');
    fs.writeFileSync(outPath, plaintext);
    console.log('Decrypted:', file, '→', path.basename(outPath));
    decryptedCount++;
  } catch (err) {
    console.error('❌ Failed to decrypt', file, '- wrong password or corrupted file');
    process.exit(1);
  }
});

console.log(`\n✅ Decrypted ${decryptedCount} file(s)`);
