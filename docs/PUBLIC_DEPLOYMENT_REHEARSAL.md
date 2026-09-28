# Public deployment rehearsal

Snapshot: 2026-09-28

## Deployment result

- Deployment root: `web`
- Install command: `npm ci`
- Build command: `npm run build`
- Public mode: `READ_ONLY_EVIDENCE_MODE`
- Secret names required: none
- Deployment URL: unavailable; Vercel project selection/linking requires user input
- Production deployment: not attempted

The exact handoff is:

```bash
vercel link --cwd web
vercel deploy --prod --cwd web
```

## Local production smoke test

The production Next.js server was exercised without a database or application secrets.

| Route | Result | Truth check |
|---|---:|---|
| `/` | PASS | Product-first redirect into `/lab` |
| `/lab` | PASS | Discovery CLOSED; 9 trials; 0 Candidate; 0 Certified |
| `/factors` | PASS | Nine committed records; rejection-first ordering |
| `/factors/trial-8` | PASS | Structured continuation recipe, rationale mismatch, Stability first failure |
| `/factors/trial-9` | PASS | Syntax failure; repair budget refusal; executable hypothesis unavailable |
| `/paper` | PASS | Locked; 0 eligible, capital, positions, orders, and fills |
| `/ledger` | PASS | 190 events; verified chain head |
| `/system` | PASS | Cached snapshot, research-only, paper locked, live execution disabled |
| `/proof` | PASS | Six-step judge story and five exact truth badges |
| `/replay?trial=8` | PASS | Seven stored steps; 0 network calls; 0 model calls |

Required JSON evidence links also resolve from the local production server. Next output-file tracing contains the committed public artifacts, including the ledger and Trial 8/9 files.

## Mobile and accessibility check

A headless Chromium check at `390 × 844` verified every required route plus Trial 8 and Trial 9 details:

- document and body width remained exactly 390 pixels
- no horizontal page overflow
- mobile bottom navigation rendered as `flex`
- proof badges and evidence cards stacked cleanly
- Paper retained the locked state and all zero counters
- status text remained present alongside semantic colors

Desktop captures at `1440 × 1000` verified the left rail, global truth strip, side-by-side Trial 8/9 evidence, controlled density, and readable Proof sequence. Visible focus styles, reduced-motion handling, minimum navigation touch targets, and non-color state labels remain in CSS.

Screenshot checkpoints A–G were inspected locally from `/proof`, Trial 8, `/paper`, Trial 9, `/ledger`, and the Proof close. Temporary screenshots contain no private path or credential and were not committed.

## Proof and evidence consistency

- Proof sequence: bounded Qwen FactorRecipe → deterministic compiler → frozen evidence gates → zero capital → hard budget blocks a repair → append-only audit chain.
- Trial 8: REJECTED; `FIRST_HARD_FAIL = Stability`; DSR `0.629643` versus `0.90`; permutation `p=0.2029`; OOS fills `0`; lifecycle `ABANDON`.
- Trial 8’s Qwen rationale says mean reversion/decay while the recipe specifies `positive_continuation`. Both remain preserved and the mismatch is visible.
- Trial 9: REJECTED at Syntax with `NO_RUN_PROJECTED_BUDGET_EXHAUSTED_AFTER_INVALID_OUTPUT`; no compiled AST, anchor result, or fabricated metric is shown.
- Paper: `LOCKED_NO_CANDIDATE`; 0 eligible factors; 0 USDT; 0 positions/orders/fills.
- Search N: 9.
- Evidence chain: PASS; 190 events; head `3393199128eccbffc99ff9554b205179202412c1eef4a484711390aec5fb216b`.

## Secret and public-package checks

The public package manifest hashes verify. Scans found no API key, authorization header, exchange secret, passphrase, database URL, bearer token, model reasoning content, or local `/home` path in public evidence. The browser bundle has no `NEXT_PUBLIC_*` secret and requires no runtime environment variable.

## Masayume-derived UX check

The implementation retains principles, not identity or code:

- product-first shell: `/` goes directly to the Lab
- restrained dark financial UI with one mint accent
- green/red/amber reserved for semantic facts and always paired with text
- large display hierarchy plus compact mono metadata and tabular numerals
- hairline borders, controlled density, and minimal shadow
- honest cached, unavailable, inconclusive, not-run, and error states
- persistent desktop rail and purpose-built mobile bottom navigation
- first-class System and Ledger surfaces
- raw evidence and proof links adjacent to decisions

No Masayume name, illustration, vermilion identity, game, contract, marketplace, or source code appears in the application.

## Demo rehearsal

The dry-run path is:

`/proof` → Trial 8 → `/paper` → Trial 9 → `/ledger` → `/proof`

Target narration duration is **2:50**, inside the required 2:40–2:55 window. The narration says that Qwen proposed a bounded recipe, the recipe was committed before performance, deterministic gates rejected it, zero factors qualified for capital, Trial 9’s repair was blocked before HTTP, and every decision is chained into the ledger. It makes no alpha, live-trading, or paper-performance claim.

## Remaining blockers before recording

1. User must create/select and link the intended Vercel project with `vercel link --cwd web`.
2. User or Codex must run `vercel deploy --prod --cwd web` after linkage.
3. Repeat the route, evidence-link, security-header, mobile-width, and truth checks against the resulting public URL.
4. Review the live URL before recording.

No video was recorded and no submission was made.
