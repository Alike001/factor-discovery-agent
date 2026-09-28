# Vercel deployment preflight

Snapshot: 2026-09-28

## Resolved project layout

- Repository root: project checkout root
- Vercel Root Directory: `web`
- Framework: Next.js `16.3.6`, App Router
- Package manager: npm, pinned by `web/package-lock.json`
- Install command: `npm ci`
- Build command: `npm run build`
- Output: standard Next.js `.next` server build; this is not a static export
- Node runtime used in preflight: `24.14.1`

Vercel should be configured with **Root Directory = `web`**. Framework detection can remain Next.js. No second frontend or repository-root build wrapper is required.

## Runtime architecture

Public mode is `READ_ONLY_EVIDENCE_MODE`.

The product has no API routes, Server Actions, public mutation controls, research trigger, paper trigger, or trade trigger. Server components read JSON from committed `web/public/evidence/` files. They do not connect to PostgreSQL and do not make Qwen, Bitget, or other network requests while rendering.

The eleven files in `web/public/evidence/latest/` are Git-tracked. Next.js output-file tracing includes them for server-rendered routes such as `/ledger`. The older factor records used by `/factors` are also committed public artifacts.

No environment variable is required to view the judge product. In particular, production does not require:

- `BITGET_QWEN_API_KEY`
- Bitget API key, secret, or passphrase
- Demo credentials
- `DATABASE_URL`

`.env.example` contains names only. Do not configure secrets merely to deploy this read-only build.

## Build verification

A clean dependency installation and production build completed with:

```bash
cd web
npm ci
npm run lint
npx tsc --noEmit
npm run build
npm audit --omit=dev
```

The build generated 17 pages, including static, statically generated, and search-parameter server-rendered routes. Dependency audit reported zero vulnerabilities. Production browser source maps remain disabled and the configured CSP, frame, content-type, referrer, and permissions headers remain enabled.

## Vercel state and handoff

Vercel CLI `59.26.0` is installed and authenticated. The repository is not linked: neither the repository root nor `web/` contains `.vercel/project.json`, and no existing account project could be selected without user intent.

Per the deployment prompt, project creation/selection is left to the user. Run from the repository root:

```bash
vercel link --cwd web
vercel deploy --prod --cwd web
```

During `vercel link`, create or select the intended hackathon project and confirm that the linked directory is `web`. Do not add production secrets. After the production URL exists, execute the live checks recorded in `PUBLIC_DEPLOYMENT_REHEARSAL.md`.
