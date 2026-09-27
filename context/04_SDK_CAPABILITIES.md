# SDK Capabilities - Source-Level Snapshot

Repo: `Bitget-AI/agent-sdk`
Snapshot: 2026-09-27
GitHub `main` package version: 3.0.0

## Generated catalog

`src/generated/catalog.ts` declares:

```text
CATALOG_SPEC_VERSION = 3.0.0
CATALOG_OPERATION_COUNT = 109
```

Counts extracted from the checked-in generated source:

| Module | Operations |
|---|---:|
| account | 39 |
| trade | 17 |
| market | 16 |
| strategy | 5 |
| broker | 11 |
| cryptoloans | 11 |
| instloan | 9 |
| tax | 1 |
| Total | 109 |

Other extracted totals:

- read operations: 70
- write operations: 39
- public operations: 16
- private operations: 93

## Composite intent tools

`src/tools/composites/index.ts` currently declares 16 names:

```text
market
order
position
strategy_order
account_overview
account_config
repayment
transfer_funds
deposit
withdraw
funds_records
subaccount
broker
loan
inst_loan
tax
```

Public README/docs still often say 14 curated intent verbs, so count exact loaded tools at runtime instead of hardcoding the older number.

## Capability assembly

`src/tools/build.ts` creates:

- optional full 1:1 operation tools when `surface === "full"`
- composite intent tools
- `raw`
- `discover`

`readOnly` filters generated write tools and also blocks writes inside composites through the shared safety gate.

## Safety controls

Built-in controls seen in source:

- `readOnly`
- `paperTrading`
- `dryRun`
- risk grading: `read`, `write`, `high`
- `confirm` for high-risk operations

Examples classified high-risk in tests include:

- cancel all orders
- close all positions
- withdrawal

## Testing / developer ergonomics

The SDK exposes an in-memory mock server through its testing subpath. This is useful for building higher-level middleware without touching real funds.

The SDK uses generated OpenAPI/catalog data, typed errors, `safeInvoke`, and zero runtime dependencies on the GitHub 3.0.0 line.

## Capabilities not found as first-class SDK primitives in the inspected public source

Searches across the Bitget-AI public org did not surface first-class implementations for:

- scheduler / cron runtime
- webhook trigger engine
- WebSocket/streaming agent runtime
- portfolio VaR or drawdown engine
- persistent policy DSL
- per-strategy budgets
- symbol allowlists / deny lists at middleware level
- workflow-level audit receipts
- replayable execution plans
- multi-agent orchestration
- quorum approvals

Absence in public source does not prove Bitget has no internal implementation. It means these are not visible as reusable primitives in the public Agent Hub code inspected here.
