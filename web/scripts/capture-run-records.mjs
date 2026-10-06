import { readFileSync, writeFileSync } from "node:fs";
import { captureCheckpoint, assertFrozenState, toCsv, trial8Supplement, verifyHistoricalManifest } from "../server/run-records.ts";

const evidence = name => JSON.parse(readFileSync(new URL(`../public/evidence/latest/${name}`, import.meta.url), "utf8"));
const initial = evidence("RESEARCH_SUMMARY.json");
const chain = evidence("EVIDENCE_CHAIN_SUMMARY.json");
assertFrozenState(initial, chain);
verifyHistoricalManifest();
const trial8 = trial8Supplement(evidence("TRIAL_8.json"));

const startedAt = new Date().toISOString();
const rows = [];
const checkpoints = 4;
const intervalMs = 15_000;
for (let index = 0; index < checkpoints; index++) {
  if (index > 0) await new Promise(resolve => setTimeout(resolve, intervalMs));
  const current = evidence("RESEARCH_SUMMARY.json");
  assertFrozenState(current, evidence("EVIDENCE_CHAIN_SUMMARY.json"));
  rows.push(await captureCheckpoint(current));
  console.log(`checkpoint ${index + 1}/${checkpoints}: ${rows.at(-1).timestamp} · RAMDUSDT ${rows.at(-1).observed_market_price} USDT · ${rows.at(-1).execution_state}`);
}
if (new Set(rows.map(row => row.timestamp)).size !== checkpoints) throw new Error("Checkpoint timestamps are not distinct");
assertFrozenState(evidence("RESEARCH_SUMMARY.json"), evidence("EVIDENCE_CHAIN_SUMMARY.json"));
verifyHistoricalManifest();

const artifact = {
  schema: "factor-discovery-agent-paper-decision-run-v1",
  label: "ACTUAL_PAPER_DECISION_NO_ORDER_RUN",
  explanation: "Four actual, timestamped public RAMDUSDT ticker observations. At each checkpoint the frozen research gate was evaluated before the market read and refused to produce an OrderIntent. This is not executed trading, a paper portfolio, or a profitability claim.",
  started_at: startedAt,
  completed_at: new Date().toISOString(),
  sdk: { package: "@bitget-ai/bitget-agent-sdk", version: "3.3.1", tool: "market", action: "tickers", category: "SPOT", mode: "READ_ONLY", credentials_used: false },
  market_price_field: "lastPrice",
  price_unit: "USDT per RAMDUSDT",
  timestamp_semantics: "timestamp is local UTC observation completion; market_timestamp is the Bitget ticker ts; sdk_request_time is the SDK response requestTime. The three are not interchangeable.",
  account_balance_change_semantics: "0 means this system made no order or account mutation at any checkpoint. No private account balance was queried; unrelated external account activity is not measured.",
  frozen_research: { protocol: initial.protocol, search_n: initial.global_search_n, candidates: initial.candidates, certified: initial.certified, paper_positions: initial.paper.positions, paper_orders: initial.paper.orders, paper_fills: initial.paper.fills, capital_gate: "CLOSED", ledger_events: chain.event_count, evidence_chain: chain.status, research_status: initial.discovery_status },
  checkpoints: rows,
  supplementary_validation: { ...trial8, clarification: "Historical deterministic backtest only; 10 fills are not paper or live orders. The 30-day OOS slice had zero fills and the factor was rejected." },
  source_code: ["web/scripts/capture-run-records.mjs", "web/server/run-records.ts", "web/server/bitget-agent.ts"],
  historical_evidence_manifest_modified: false,
  qwen_calls: 0,
  write_capable_sdk_calls: 0,
  paper_rows_inserted: 0,
};

writeFileSync(new URL("../public/evidence/AGENTIC_TRADING_RUN_RECORD.json", import.meta.url), JSON.stringify(artifact, null, 2) + "\n");
writeFileSync(new URL("../public/evidence/AGENTIC_TRADING_RUN_RECORD.csv", import.meta.url), toCsv(rows));
console.log("wrote public JSON and CSV run records; no order intent or SDK write call");
