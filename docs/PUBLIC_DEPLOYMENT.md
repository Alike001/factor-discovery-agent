# Public deployment

Deploy the Next.js app in judge-safe `READ_ONLY_EVIDENCE_SNAPSHOT` mode. The browser receives committed sanitized JSON only. No public endpoint runs Qwen, starts research, mutates the database, places paper orders, or trades.

The deployment must not claim the local PostgreSQL instance is an online managed service. `/system` labels it as a last-verified exported snapshot.

## Build

```bash
cd web
npm ci
npm run lint
npx tsc --noEmit
npm run build
npm audit --omit=dev
```

Deploy `web/` with Node.js support for Next.js 16. Root redirects to `/lab`. Security headers are defined in `next.config.ts`; production browser source maps are disabled.

## Environment

No secret is required to serve the public snapshot. `.env.example` lists development names only. Never expose any `BITGET_*`, Qwen, database, Demo, or exchange credential through `NEXT_PUBLIC_*` variables.

Regenerate evidence in a trusted local environment only:

```bash
python3 scripts/export_public_evidence.py
```

Review `web/public/evidence/latest/MANIFEST.json`, run the backend sanitization tests, and commit the generated package. Do not run the generator in an untrusted public request path.

Every main route shows the last verified timestamp. Loading and error states never invent fallback values. No backend is deployed in this build, so a production health endpoint is not claimed.
