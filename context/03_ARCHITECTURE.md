# Agent Hub Architecture

## Execution path

```text
User instruction
  -> external LLM / agent host
  -> MCP tool call or shell command
  -> MCP adapter / bgc CLI
  -> agent-sdk ToolSpec
  -> shared safety chokepoint
  -> BitgetRestClient
  -> signed UTA v3 REST request
  -> Bitget
```

## Tool-surface design

The SDK uses progressive disclosure so the model does not need every endpoint schema loaded into context.

Conceptually:

```text
discover()
  -> domains
  -> intent tool
  -> action
  -> exact arguments
  -> execute
```

The source also includes `raw`, which can reach catalog operations directly by operation ID.

## Source-level module model

`src/constants.ts` defines 8 modules:

```text
account
trade
market
strategy
broker
cryptoloans
instloan
tax
```

Default modules:

```text
account, trade, market
```

Hidden modules:

```text
broker, instloan
```

Hidden means not included by the generic `modules: all` general surface. They are deliberate opt-ins for To-B / institutional scenarios.

## Agent-facing domain model

`src/tools/domains.ts` defines 9 business domains:

```text
market
trade
account
funds
subaccount
broker
loan
instloan
tax
```

This is intentionally different from raw OpenAPI modules because an agent reasons about business intents, not API tags.

## Safety boundary

The key source function is `executeWithSafety()`.

It implements:

```text
if dryRun:
    preview, no network
else if readOnly and write:
    reject
else if high-risk and not confirm:
    return confirmationRequired
else:
    call client
```

This is strong for individual tool calls but does not by itself create:

- a stateful risk budget
- multi-operation atomic plans
- retry-safe workflow semantics
- persistent approvals
- per-agent policy identities
- portfolio-wide constraints

## Authentication boundaries

### Manual API keys

Traditional SDK/CLI path:

- key/secret/passphrase from local environment/config
- requests signed locally with HMAC-SHA256
- secrets are not supposed to be put in the model conversation

### Agentic Account

Newer September 2026 docs add an OAuth onboarding path:

- browser OAuth
- credentials issued/stored locally by the MCP/SDK flow
- dedicated isolated fund domain
- user manually funds the Agentic account from web
- agent cannot withdraw from the Agentic account

This controls account blast radius, but strategy-level permissions still need a separate policy layer if an application wants finer rules.

## Market-analysis path

`bitget-signal` is not the same execution path:

```text
Agent
  -> local Signal skill instructions
  -> remote/public Bitget data MCP
  -> returned market data
  -> model analysis
```

A separate Bitget-hosted MCP also covers US equities/ETFs/fundamentals and analyst data.
