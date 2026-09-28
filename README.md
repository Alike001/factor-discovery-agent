# Bitget rToken Factor Research Lab

An evidence-first autonomous, session-aware Qwen researcher for Bitget Reality tokenized equities. Qwen proposes bounded hypotheses; deterministic code decides whether evidence is strong enough for capital.

The final research state contains nine committed trials, zero Candidates, zero Certified factors, and zero paper trades. Discovery is closed. The public product is a read-only evidence snapshot with Lab, Factors, locked Paper, Ledger, System, Proof, and Replay surfaces.

## Setup

Python 3.12 is the project target:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
python scripts/preflight.py
pytest
```

Frontend commands live in `web/`:

```bash
npm install
npm run build
npm run dev
```

Secrets are optional for public-data preflight. Put local values in `.env`; it is ignored by Git. Without credentials, artifacts explicitly report Qwen, account fee, Demo, and database checks as blocked or unverified.

## Safety and scope

- Paper research only; no real-money execution.
- No arbitrary model-authored Python.
- Missing bars are never forward-filled.
- The tracer proves architecture and is not claimed as discovered alpha.

## Final product state

- Global search N remains 9; total Qwen HTTP attempts remain 20.
- Trial 8 separates its deterministic executable hypothesis from Qwen rationale and flags their semantic mismatch.
- Trial 9 exposes the hard-budget repair refusal without fabricated metrics.
- `/paper` is locked with zero capital, positions, orders, and fills.
- `/ledger` presents the sanitized 190-event verified chain; `/replay` uses stored artifacts only.
- The public evidence package is sanitized, hashed, read-only, and pinned to the final research source commit.

See `docs/PUBLIC_DEPLOYMENT.md` and `docs/DEMO_STORYBOARD.md` for deployment and demo instructions.
