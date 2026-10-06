import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { assertFrozenState, recordFromTicker, toCsv, trial8Supplement, verifyHistoricalManifest } from "./run-records.ts";

const artifact = JSON.parse(readFileSync(new URL("../public/evidence/AGENTIC_TRADING_RUN_RECORD.json", import.meta.url), "utf8"));
const csv = readFileSync(new URL("../public/evidence/AGENTIC_TRADING_RUN_RECORD.csv", import.meta.url), "utf8");
const state = JSON.parse(readFileSync(new URL("../public/evidence/latest/RESEARCH_SUMMARY.json", import.meta.url), "utf8"));
const chain = JSON.parse(readFileSync(new URL("../public/evidence/latest/EVIDENCE_CHAIN_SUMMARY.json", import.meta.url), "utf8"));
const trial8 = JSON.parse(readFileSync(new URL("../public/evidence/latest/TRIAL_8.json", import.meta.url), "utf8"));

test("actual run record is separate, timestamped, and no-order only", () => {
  assert.equal(artifact.label, "ACTUAL_PAPER_DECISION_NO_ORDER_RUN");
  assert.equal(artifact.checkpoints.length, 4);
  assert.equal(new Set(artifact.checkpoints.map(row => row.timestamp)).size, 4);
  assert.ok(Date.parse(artifact.checkpoints.at(-1).timestamp) - Date.parse(artifact.checkpoints[0].timestamp) >= 45_000);
  for (const row of artifact.checkpoints) {
    assert.equal(row.instrument, "RAMDUSDT");
    assert.ok(Number(row.observed_market_price) > 0);
    assert.equal(row.direction, "NO_ORDER");
    assert.equal(row.quantity, 0);
    assert.equal(row.account_balance_change, 0);
    assert.equal(row.candidate_count, 0);
    assert.equal(row.capital_gate_state, "CLOSED");
    assert.equal(row.execution_state, "BLOCKED_NO_CANDIDATE");
    assert.equal(row.sdk_mode, "READ_ONLY");
    assert.ok(row.decision_reason.includes("NO_ACCOUNT_READ"));
    assert.ok(Date.parse(row.market_timestamp) <= Date.parse(row.timestamp));
    assert.ok(Date.parse(row.sdk_request_time) <= Date.parse(row.timestamp));
  }
  assert.equal(artifact.sdk.credentials_used, false);
  assert.equal(artifact.write_capable_sdk_calls, 0);
  assert.equal(artifact.qwen_calls, 0);
  assert.equal(artifact.paper_rows_inserted, 0);
  assert.match(artifact.account_balance_change_semantics, /No private account balance was queried/);
  assert.doesNotMatch(JSON.stringify(artifact), /sk-[A-Za-z0-9]{20,}|postgresql:\/\/|\/home\/ali|passphrase|authorization|bearer/i);
});

test("CSV is an exact row projection of public JSON", () => {
  assert.equal(csv, toCsv(artifact.checkpoints));
  assert.equal(csv.trimEnd().split("\n").length, artifact.checkpoints.length + 1);
});

test("frozen evidence and Trial 8 supplementary panel match their sources", () => {
  assertFrozenState(state, chain);
  verifyHistoricalManifest();
  assert.deepEqual(artifact.supplementary_validation, {
    ...trial8Supplement(trial8),
    clarification: "Historical deterministic backtest only; 10 fills are not paper or live orders. The 30-day OOS slice had zero fills and the factor was rejected.",
  });
  assert.deepEqual(artifact.frozen_research, {
    protocol: "fdp-v3", search_n: 9, candidates: 0, certified: 0,
    paper_positions: 0, paper_orders: 0, paper_fills: 0,
    capital_gate: "CLOSED", ledger_events: 190, evidence_chain: "PASS", research_status: "CLOSED",
  });
});

test("malformed ticker and changed frozen truth fail closed", () => {
  const ticker = { category: "SPOT", symbol: "RAMDUSDT", lastPrice: "641.34", ts: "1791281925000" };
  assert.equal(recordFromTicker(state, ticker, "2026-10-06T10:18:47.466Z", "2026-10-06T10:18:47.466Z").direction, "NO_ORDER");
  assert.throws(() => recordFromTicker(state, { ...ticker, lastPrice: "invalid" }, "2026-10-06T10:18:47.466Z", "2026-10-06T10:18:47.466Z"));
  assert.throws(() => recordFromTicker(state, { ...ticker, symbol: "BTCUSDT" }, "2026-10-06T10:18:47.466Z", "2026-10-06T10:18:47.466Z"));
  assert.throws(() => recordFromTicker(state, { ...ticker, ts: "1791280000000" }, "2026-10-06T10:18:47.466Z", "2026-10-06T10:18:47.466Z"));
  assert.throws(() => assertFrozenState({ ...state, candidates: 1 }, chain));
});
