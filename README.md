# Bitget rToken Factor Research Lab

An evidence-first tracer for an autonomous, session-aware Qwen researcher on Bitget Reality tokenized equities.

The current implementation is intentionally limited to Phase 0 preflight and the Phase 1 `Overnight Relative Return Z-Score` tracer. It uses real public Bitget market data and never places real orders.

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

