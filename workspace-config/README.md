# workspace-config

**Purpose:** IDE configuration, environment files, tooling setup.

## Contents (Target)

| Source | Destination |
|--------|-------------|
| `.env` | `workspace-config/.env` |
| `.env.example` | `workspace-config/.env.example` |
| `package.json` | `workspace-config/package.json` |

## Notes

- Keep sensitive values (API keys) in `.env` only
- `package.json` is for workspace tooling, not application dependencies
