import 'dotenv/config';
import { z } from 'zod';
import { createHash } from 'crypto';
import { readSync } from 'fs';

// ═══════════════════════════════════════════════════════════════════════════
// ADMIN PASSWORD GATE
// ═══════════════════════════════════════════════════════════════════════════
// Purpose: If this codebase is released, it is inoperable without the
// admin password. Even with correct env vars, credentials are gated.
//
// To set your own password:
//   node -e "console.log(require('crypto').createHash('sha256').update('YOUR_PASS').digest('hex'))"
// Then replace ADMIN_PASSWORD_HASH below.
// ───────────────────────────────────────────────────────────────────────────
const ADMIN_PASSWORD_HASH = '1f34adb50429071ba3d9bee229b22b1c09c2d82aee19b31ec394218f87e5fd19';

function promptPassword(query) {
  process.stdout.write(query);
  const buf = Buffer.alloc(1024);
  const n = readSync(0, buf, 0, 1024);
  return buf.toString('utf8', 0, n).trim();
}

function verifyPassword() {
  // Non-interactive bypass for emergency/automation (not for production release)
  if (process.env.STACK_PASSWORD) {
    const hash = createHash('sha256').update(process.env.STACK_PASSWORD).digest('hex');
    if (hash === ADMIN_PASSWORD_HASH) return true;
    console.error('❌ Invalid STACK_PASSWORD hash');
    return false;
  }

  // Skip password check in test environments if explicitly requested
  if (process.env.SKIP_PASSWORD_CHECK === '1') {
    console.warn('⚠️  SKIP_PASSWORD_CHECK=1 — bypassing admin password gate');
    return true;
  }

  const password = promptPassword('🔐 Admin password: ');
  const hash = createHash('sha256').update(password).digest('hex');
  return hash === ADMIN_PASSWORD_HASH;
}

// ═══════════════════════════════════════════════════════════════════════════
// ENV SCHEMA
// ═══════════════════════════════════════════════════════════════════════════
const EnvSchema = z.object({
  // Linear API
  LINEAR_API_KEY: z.string().min(1, 'LINEAR_API_KEY is required'),
  LINEAR_TEAM_ID: z.string().optional().default('3c8c51e6-3f24-4999-8fe6-3e097468bf6c'),

  // Notion API
  NOTION_API_KEY: z.string().min(1, 'NOTION_API_KEY is required'),
  NOTION_DATABASE_ID: z.string().min(1, 'NOTION_DATABASE_ID is required'),

  // ENE Security
  ENE_SECRET_KEY: z.string().min(1, 'ENE_SECRET_KEY is required'),
  ENE_ENCRYPTION_KEY: z.string().optional(),

  // Environment
  NODE_ENV: z.enum(['development', 'production', 'test']).optional().default('development'),
});

let env = null;

export function loadConfig() {
  if (env) return env;

  const ok = verifyPassword();
  if (!ok) {
    console.error('❌ Admin password verification failed');
    console.error('   This stack requires a local password to load credentials.');
    console.error('   If you are not the stack operator, this system is inoperable.');
    process.exit(1);
  }

  try {
    env = EnvSchema.parse(process.env);
    console.log('✅ Configuration loaded successfully');
    return env;
  } catch (error) {
    console.error('❌ Configuration error:');
    if (error.errors) {
      error.errors.forEach((err) => {
        console.error(`  - ${err.path.join('.')}: ${err.message}`);
      });
    } else {
      console.error(error);
    }
    console.error('\n💡 Set the required environment variables in your .env file');
    console.error('   Copy .env.example to .env and add your API keys');
    process.exit(1);
  }
}

export function getConfig() {
  if (!env) {
    return loadConfig();
  }
  return env;
}

export default getConfig;
