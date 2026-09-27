# Revised Gap Map After S1/S2 Scan

| Original gap | Status | Why | Narrow space that may remain |
|---|---|---|---|
| A Stateful Policy Governor | Crowded broadly | Many projects already have caps, vetoes, kill switches and drawdown rules | Shared cross-asset state, per-agent permissions, durable budgets |
| B Durable Watch/Trigger Runtime | Partial | Many apps have polling/cron/WebSocket loops | Persisted watches, dedupe, restart recovery, idempotent Agent Hub execution |
| C Workflow Plan/Preflight/Receipt | Crowded broadly | VEIL, Flight Recorder, BitgetBench and signed logs cover much of it | Recovery-aware multi-step workflows with consequential intermediate state |
| D Multi-Agent Portfolio Desk | Crowded at council level | AgentBus, Trading Council, Vector | Shared portfolio state, budgets and conflict resolution across agents |
| E Signal Evaluation/Shadow Trading | Very crowded | Backtest/paper/evaluation products are common | Narrow autonomous factor falsification tied to S2 market structure |
| F SDK Capability Inspector | Niche | Version drift is real but few products focus on it | Useful developer tooling, weak S2 product fit |

Next research questions:
- What public Cross-Asset Execution entries already exist?
- Are any Factor Discovery entries genuinely autonomous from hypothesis through falsification and paper deployment?
- Does any project offer reusable, restart-safe event execution on top of Agent Hub?
- What rToken microstructure failure modes are unique to 7x24 trading?
