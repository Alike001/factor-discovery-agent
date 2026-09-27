# AI Context - Bitget Agent Hub

You are working with the Bitget Agent Hub ecosystem as of 2026-09-27.

## Core mental model

Bitget Agent Hub is an agent-facing access layer over Bitget trading and market infrastructure.

- Reasoning stays in the external AI host or model.
- `bitget-agent-sdk` is the foundation execution/tool layer.
- `bitget-agent-cli` (`bgc`) is the terminal surface for Claude Code, Codex CLI, OpenClaw, etc.
- `bitget-agent-mcp` is the MCP surface for desktop/GUI agents.
- `bitget-agent-skill` teaches an agent how and when to invoke the trading tools.
- `bitget-signal` supplies no-key market-analysis skills and a public data MCP.
- `agent_hub` is the ecosystem entrypoint plus installer/meta-tool, not the main execution implementation.

## Current architecture

```text
LLM / Agent Host
   |
   | natural-language intent / tool call
   v
CLI (bgc) OR MCP adapter
   |
   v
@bitget-ai/bitget-agent-sdk
   |- generated UTA catalog
   |- intent/composite verbs
   |- discover
   |- raw escape hatch
   |- HMAC request signing
   |- rate limiting / typed errors
   |- dry-run
   |- read-only mode
   |- paper trading
   |- high-risk confirmation gate
   v
Bitget UTA v3 REST API
```

`bitget-signal` is mostly parallel to that execution stack:

```text
Agent -> Signal Skills -> public Bitget data MCP -> analysis by agent
```

## Important source-level facts

Do not rely blindly on the marketing count of 89 operations / 14 verbs.

The checked-in `agent-sdk` generated catalog on GitHub `main` declares:

- 109 operations total
- 39 write operations
- 70 read operations
- 93 private operations
- 16 public operations
- 8 SDK modules: account, trade, market, strategy, broker, cryptoloans, instloan, tax
- 9 agent-facing domains: market, trade, account, funds, subaccount, broker, loan, instloan, tax
- 16 composite intent tools in `src/tools/composites/index.ts`

Operation distribution in the generated catalog:

- account: 39
- trade: 17
- market: 16
- strategy: 5
- broker: 11
- cryptoloans: 11
- instloan: 9
- tax: 1

Broker and institutional-loan modules are intentionally hidden from the general surface and must be requested explicitly.

## Safety model in source

All writes pass through `executeWithSafety()` in `agent-sdk/src/tools/safety.ts`.

Order of gates:

1. `dryRun` returns the would-send request and makes no network call.
2. `readOnly` rejects writes.
3. operations graded `high` return `confirmationRequired` unless `confirm: true` is supplied.
4. otherwise the operation is sent to the Bitget client.

This is a per-operation safety chokepoint. The inspected public SDK does not expose a general persistent policy engine for things like daily loss budget, max leverage, symbol allowlists, max notional, strategy cooldowns, mandatory stop-loss rules, or multi-step workflow approval.

## Agentic Account

Bitget's September 2026 Agentic Account flow adds OAuth-based authorization and fund isolation. The Agentic account is separate from the main account, and withdrawals are excluded. Newer docs instruct agents to trigger authorization through provided MCP tools instead of constructing OAuth URLs themselves.

Treat the Agentic Account as an account-level blast-radius boundary, not a replacement for strategy-level policy controls.

## Version drift warning

GitHub `main` package files for SDK/CLI/MCP/Skill show 3.0.0, while published npm/docs have moved ahead:

- MCP package observed on npm: 3.3.0
- Skill package observed on npm: 3.3.1
- September Agentic Account docs require Agentic Skill >= 3.3.0

Therefore, before implementing against auth, OAuth, or newly added operation behavior, verify the currently published npm package and do not assume GitHub `main` is the full latest runtime source.

## Existing/crowded patterns

Generic "AI reads market data and places a Bitget order" is crowded.

Bitget already provides:

- five Signal analysis skills: macro, market-intel, sentiment, technical, news
- full trading/account execution surfaces
- strategy orders and TP/SL support in the current UTA-oriented surface
- paper trading, dry-run, read-only mode, confirmation gates
- Agentic Account fund isolation
- a separate read-only US equities/ETF/fundamentals MCP

Community proposals/integrations seen in the public org include:

- BotIndex: structured external intelligence feeding Bitget execution
- AlgoVault: composite signal/confidence/regime output feeding Bitget
- Fly Marketing Agent: social/content automation plus Bitget signals/trading

Avoid rebuilding these shapes without a sharper primitive.

## Strong gap hypotheses

### 1. Policy / Risk Governor

A deterministic middleware layer that evaluates proposed Bitget actions before the SDK executes them.

Possible controls:

- max order notional
- max leverage per symbol
- symbol allow/deny list
- max portfolio exposure
- daily realized/unrealized loss budget
- cooldown after losses
- mandatory TP/SL before position opening
- permission by strategy or agent identity
- separate limits per Agentic account/subaccount

Why it is distinct: current source has operation-level `readOnly`, `dryRun`, and `confirm`, but no general policy DSL or persistent risk budget found in the public org search.

### 2. Durable Condition / Event Engine

A first-class service for "watch until condition X, then execute Y" using durable state, WebSocket/streaming data, restart recovery, and exact trigger semantics.

The Bitget product page advertises continuous monitoring use cases, but the inspected Agent SDK is REST-oriented and public org searches did not reveal a scheduler, webhook, cron, or WebSocket runtime inside the Agent Hub packages. Today this behavior appears likely to depend on the host agent or an external runtime.

### 3. Workflow Plan + Execution Receipt

Compile a multi-step agent intent into a stable plan before execution:

```text
intent -> exact action plan -> dry-run -> policy check -> approval -> execute -> receipt
```

Useful receipt fields:

- normalized inputs
- tool/operation IDs
- market snapshot used
- policy decisions
- approvals
- request/response identifiers
- resulting positions/balances
- retry/recovery history

Current `dryRun` previews one operation. A workflow-level deterministic plan, audit receipt, replay, and recovery layer was not found in the public org source search.

### 4. Multi-Agent Trading Desk

Specialized agents for research, risk, execution, and review sharing one bounded portfolio state.

Bitget has explicitly promoted multi-agent collaboration in earlier Agent Hub challenges, but the public SDK is primarily an execution/tool library. Shared policy state, role separation, quorum approval, and task orchestration are not first-class SDK concepts in the inspected source.

### 5. Signal-to-Strategy Evaluation Layer

A product that turns Signal outputs into testable rules before live use:

- signal normalization
- historical replay/backtest
- confidence calibration
- regime tagging
- paper-trading shadow mode
- live-vs-simulated drift reporting

This is more differentiated than another chatbot analyst because Bitget Signal already covers basic market intelligence.

## Research rule before choosing a product

A candidate idea should answer all of these:

- Which missing primitive does it add?
- Why cannot `agent-sdk + Signal + ordinary agent prompting` already do it safely?
- Is the missing layer reusable by many agents, not one strategy?
- Can it be implemented as a clean SDK/MCP/Skill extension?
- Can the demo prove deterministic behavior, not just an LLM conversation?
- Does it still matter when the model changes?
