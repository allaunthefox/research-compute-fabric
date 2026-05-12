# PRIVATE Wolfram Alpha Connector Surface

Bounded computational oracle for Research Stack.

## Authority boundary

- Wolfram Alpha = computational check / external calculation surface
- Graph.lean = canonical proof / graph authority
- ENE = provenance / archive authority
- FAMM = route-memory outcome layer after authority gating

Wolfram can check, simplify, solve, numerically probe, and produce external calculation receipts. It cannot certify proof, empirical validity, or basin promotion.

## Security rule

This connector must never be public.

Allowed exposure:

- localhost
- VPN
- tailnet
- SSH tunnel
- private reverse proxy

Forbidden exposure:

- public internet
- public OpenAPI action
- unauthenticated HTTP
- public webhook

## Environment

```bash
export WOLFRAM_CONNECTOR_TOKEN="YOUR_WOLFRAM_CONNECTOR_TOKEN"
export WOLFRAM_APP_ID="your-private-wolfram-alpha-app-id"
export WOLFRAM_MAX_QUERY_CHARS=1600
export WOLFRAM_TIMEOUT_MS=15000
```

Never store `WOLFRAM_APP_ID` or `WOLFRAM_CONNECTOR_TOKEN` in GitHub, Notion, Drive, Obsidian, or logs.

## Mount

In `server.js`:

```js
import wolframRouter from "./connectors/wolfram/wolfram_alpha_connector_router.js";
app.use("/wolfram", wolframRouter);
```

## Endpoints

Mounted under `/wolfram`:

```text
GET  /wolfram/health
POST /wolfram/short
POST /wolfram/query
POST /wolfram/validate-equation
POST /wolfram/numeric-probe
```

## Smoke tests

```bash
curl -H "Authorization: Bearer $WOLFRAM_CONNECTOR_TOKEN" \
  http://127.0.0.1:3000/wolfram/health
```

```bash
curl -X POST http://127.0.0.1:3000/wolfram/short \
  -H "Authorization: Bearer $WOLFRAM_CONNECTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"integral of x^2 from 0 to 1"}'
```

```bash
curl -X POST http://127.0.0.1:3000/wolfram/validate-equation \
  -H "Authorization: Bearer $WOLFRAM_CONNECTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"equation":"m*a = -k*x", "variable":"a", "domain":"coupled oscillator"}'
```

```bash
curl -X POST http://127.0.0.1:3000/wolfram/numeric-probe \
  -H "Authorization: Bearer $WOLFRAM_CONNECTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"expression":"0.5*6^2.4"}'
```

## Research Stack path

```text
equation / motif / numeric probe
→ Wolfram computational check
→ receipt hash
→ ENE provenance record
→ Graph.lean / independent derivation gate
→ torsion / FAMM outcome
```

## Basin rule

```text
Wolfram result → HOLD computational witness
```

Never:

```text
Wolfram result → direct proof
Wolfram result → direct basin
```

A Wolfram hit can only reduce review cost or create a computational witness pending canonical audit.
