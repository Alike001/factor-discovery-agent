import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { BitgetRestClient, buildTools, loadConfig, safeInvoke } from "@bitget-ai/bitget-agent-sdk";
import { currentResearchGate, executeOrderIntent } from "./bitget-agent.ts";

export const RUN_RECORD_FIELDS = [
  "timestamp", "instrument", "observed_market_price", "direction", "quantity",
  "account_balance_change", "candidate_count", "capital_gate_state",
  "execution_state", "sdk_mode", "decision_reason",
] as const;

export type RunRecord = {
  timestamp: string;
  instrument: "RAMDUSDT";
  observed_market_price: string;
  direction: "NO_ORDER";
  quantity: 0;
  account_balance_change: 0;
  candidate_count: 0;
  capital_gate_state: "CLOSED";
  execution_state: "BLOCKED_NO_CANDIDATE";
  sdk_mode: "READ_ONLY";
  decision_reason: "NO_QUALIFIED_CANDIDATE; NO_ORDER_INTENT; NO_ACCOUNT_READ";
  market_timestamp: string;
  sdk_request_time: string;
};

type FrozenSummary = {
  protocol: string; global_search_n: number; candidates: number; certified: number;
  paper_eligible: number; paper: { positions: number; orders: number; fills: number; capital_usdt: number };
  discovery_status: string; paper_engine: string; latest_verified_source_timestamp: string;
};

export function assertFrozenState(state: FrozenSummary, chain: { status: string; event_count: number }): void {
  if (state.protocol !== "fdp-v3" || state.global_search_n !== 9 || state.candidates !== 0 || state.certified !== 0 || state.paper_eligible !== 0 ||
      state.paper.positions !== 0 || state.paper.orders !== 0 || state.paper.fills !== 0 || state.paper.capital_usdt !== 0 ||
      state.discovery_status !== "CLOSED" || state.paper_engine !== "LOCKED_NO_CANDIDATE" || chain.status !== "PASS" || chain.event_count !== 190) {
    throw new Error("Frozen research truth mismatch; refusing run-record capture");
  }
}

export function verifyHistoricalManifest(): void {
  const manifest = JSON.parse(readFileSync(new URL("../public/evidence/latest/MANIFEST.json", import.meta.url), "utf8")) as { files: Record<string, { sha256: string }> };
  for (const [name, item] of Object.entries(manifest.files)) {
    if (!/^[A-Z0-9_]+\.json$/.test(name)) throw new Error("Unexpected evidence filename");
    const bytes = readFileSync(new URL(`../public/evidence/latest/${name}`, import.meta.url));
    if (createHash("sha256").update(bytes).digest("hex") !== item.sha256) throw new Error(`Historical manifest mismatch: ${name}`);
  }
}

export function trial8Supplement(trial: { trial_number: number; outcome: string; gates: Array<{ name: string; reason: string }>; metrics: { net: { fills: number }; oos_net: { fills: number } } }) {
  const coverage = trial.gates.find(gate => gate.name === "Coverage")?.reason ?? "";
  const days = Number(coverage.match(/([\d.]+) certified days/)?.[1]);
  if (trial.trial_number !== 8 || trial.outcome !== "REJECTED" || days !== 118.1 || trial.metrics.net.fills !== 10 || trial.metrics.oos_net.fills !== 0) {
    throw new Error("Trial 8 supplementary evidence mismatch");
  }
  return { trial: 8, status: "REJECTED", certified_history_days: days, historical_backtest_fills: 10, oos_window_days: 30, oos_fills: 0, source: "web/public/evidence/latest/TRIAL_8.json", oos_policy_source: "backend/app/research/protocol.py" };
}

export function recordFromTicker(
  state: FrozenSummary,
  ticker: { category?: unknown; symbol?: unknown; lastPrice?: unknown; ts?: unknown },
  requestTime: string,
  observedAt: string,
): RunRecord {
  if (ticker.category !== "SPOT" || ticker.symbol !== "RAMDUSDT") throw new Error("Ticker does not match requested rToken SPOT symbol");
  if (typeof ticker.lastPrice !== "string" || !/^(?:0|[1-9]\d*)(?:\.\d+)?$/.test(ticker.lastPrice) || Number(ticker.lastPrice) <= 0) throw new Error("Invalid observed ticker price");
  const marketMs = Number(ticker.ts);
  if (!Number.isFinite(marketMs) || marketMs <= 0 || !Number.isFinite(Date.parse(requestTime)) || !Number.isFinite(Date.parse(observedAt))) throw new Error("Invalid observation timestamp");
  if (marketMs > Date.parse(observedAt) + 60_000) throw new Error("Future ticker timestamp");
  if (Date.parse(observedAt) - marketMs > 5 * 60_000) throw new Error("Stale ticker timestamp");
  if (state.candidates !== 0) throw new Error("Candidate count changed during capture");
  return {
    timestamp: observedAt, instrument: "RAMDUSDT", observed_market_price: ticker.lastPrice,
    direction: "NO_ORDER", quantity: 0, account_balance_change: 0, candidate_count: 0,
    capital_gate_state: "CLOSED", execution_state: "BLOCKED_NO_CANDIDATE", sdk_mode: "READ_ONLY",
    decision_reason: "NO_QUALIFIED_CANDIDATE; NO_ORDER_INTENT; NO_ACCOUNT_READ",
    market_timestamp: new Date(marketMs).toISOString(), sdk_request_time: requestTime,
  };
}

export function toCsv(records: readonly RunRecord[]): string {
  const cell = (value: string | number) => `"${String(value).replaceAll('"', '""')}"`;
  return [RUN_RECORD_FIELDS.join(","), ...records.map(record => RUN_RECORD_FIELDS.map(field => cell(record[field])).join(","))].join("\n") + "\n";
}

export async function captureCheckpoint(state: FrozenSummary): Promise<RunRecord> {
  const bridge = currentResearchGate(state);
  const execution = await executeOrderIntent(bridge, "READ_ONLY", { authenticated: false, riskChecksPassed: false, allowPaperDryRun: false });
  if (bridge.status !== "BLOCKED_NO_CANDIDATE" || bridge.intent !== null || execution.status !== "BLOCKED_NO_CANDIDATE" || execution.sdkInvoked) throw new Error("Execution boundary did not block order");

  // Explicit empty credentials override any local environment; no account read is made.
  const config = loadConfig({ modules: "all", readOnly: true, apiKey: "", secretKey: "", passphrase: "" });
  if (!config.readOnly || config.hasAuth) throw new Error("Public SDK request is not credential-free/read-only");
  const tool = buildTools(config).find(item => item.name === "market");
  if (!tool) throw new Error("Official SDK market tool unavailable");
  const response = await safeInvoke(tool, { action: "tickers", category: "SPOT", symbol: "RAMDUSDT" }, { config, client: new BitgetRestClient(config) });
  if (!response.ok || !Array.isArray(response.data)) throw new Error("Official SDK market request failed");
  const matched = response.data.filter(row => row && typeof row === "object" && row.symbol === "RAMDUSDT");
  if (matched.length !== 1) throw new Error("Expected exactly one RAMDUSDT ticker");
  return recordFromTicker(state, matched[0], response.requestTime, new Date().toISOString());
}
