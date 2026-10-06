import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createOrderIntent, currentResearchGate, executeOrderIntent } from "./bitget-agent.ts";

const summary = JSON.parse(readFileSync(new URL("../public/evidence/latest/RESEARCH_SUMMARY.json", import.meta.url), "utf8"));
const sdkStatus = JSON.parse(readFileSync(new URL("../public/evidence/BITGET_AGENT_SDK_STATUS.json", import.meta.url), "utf8"));
const fixture = Object.freeze({
  label: "TEST_ONLY_SYNTHETIC_CANDIDATE",
  factorId: "TEST_ONLY_SYNTHETIC_CANDIDATE",
  lifecycle: "CANDIDATE",
  evidenceGatesPassed: true,
  capitalGateOpen: true,
  symbol: "RAMDUSDT",
  supportedSymbols: ["RAMDUSDT"],
  direction: "BUY",
  quantity: 1,
  notionalUsdt: 100,
  maxNotionalUsdt: 100,
  evidenceAsOf: "2026-10-06T10:00:00.000Z",
  now: "2026-10-06T10:01:00.000Z",
  maxEvidenceAgeMs: 300000,
  riskChecksPassed: true,
});

test("real frozen research state blocks before OrderIntent and SDK write", async () => {
  assert.equal(summary.candidates, 0);
  const bridge = currentResearchGate(summary);
  assert.deepEqual(bridge, { status: "BLOCKED_NO_CANDIDATE", intent: null });
  let calls = 0;
  const result = await executeOrderIntent(bridge, "PAPER_DRY_RUN", { authenticated: true, riskChecksPassed: true, allowPaperDryRun: true }, async () => { calls++; throw Error("write must not be reached"); });
  assert.deepEqual(result, { status: "BLOCKED_NO_CANDIDATE", sdkInvoked: false });
  assert.equal(calls, 0);
  assert.deepEqual(summary.paper, { capital_usdt: 0, fills: 0, orders: 0, positions: 0 });
});

test("separate public SDK status is read-only, credential-free, and not research evidence", () => {
  assert.equal(sdkStatus.mode, "READ_ONLY");
  assert.equal(sdkStatus.connection_status, "VERIFIED_READ_ONLY");
  assert.equal(sdkStatus.rtoken_probe.symbol, "RAMDUSDT");
  assert.equal(sdkStatus.rtoken_probe.matchingRows, 1);
  assert.equal(sdkStatus.current_order, "BLOCKED_NO_CANDIDATE");
  assert.equal(sdkStatus.account_write_calls, 0);
  assert.equal(sdkStatus.real_orders, 0);
  assert.equal(sdkStatus.historical_research_source, "UNCHANGED_COMMITTED_BITGET_REALITY_EVIDENCE");
  assert.doesNotMatch(JSON.stringify(sdkStatus), /api[_-]?key|secret|passphrase|authorization|bearer|database_url|\/home\//i);
});

test("synthetic qualified Candidate yields deterministic bounded intent and mocked dry-run", async () => {
  const bridge = createOrderIntent(fixture);
  assert.equal(bridge.status, "READY");
  assert.deepEqual(bridge, createOrderIntent(fixture));
  assert.equal(bridge.intent.factorId, "TEST_ONLY_SYNTHETIC_CANDIDATE");
  let received;
  const result = await executeOrderIntent(bridge, "PAPER_DRY_RUN", { authenticated: true, riskChecksPassed: true, allowPaperDryRun: true, qualification: fixture, now: fixture.now }, async (tool, args) => {
    received = { tool: tool.name, args };
    return { ok: true, data: { dryRun: true }, endpoint: "MOCK_ONLY", requestTime: fixture.now };
  });
  assert.equal(result.status, "DRY_RUN_PREVIEW");
  assert.deepEqual(received, { tool: "order", args: { action: "place", category: "SPOT", symbol: "RAMDUSDT", side: "buy", orderType: "market", qty: "1", dryRun: true } });
});

test("synthetic invalid inputs fail closed", () => {
  for (const [change, status] of [
    [{ lifecycle: "REJECTED" }, "BLOCKED_NO_CANDIDATE"],
    [{ evidenceGatesPassed: false }, "BLOCKED_EVIDENCE"],
    [{ capitalGateOpen: false }, "BLOCKED_CAPITAL_GATE"],
    [{ symbol: "FAKEUSDT" }, "BLOCKED_UNSUPPORTED_SYMBOL"],
    [{ direction: "HOLD" }, "BLOCKED_INVALID_DIRECTION"],
    [{ quantity: 0 }, "BLOCKED_INVALID_SIZE"],
    [{ notionalUsdt: 101 }, "BLOCKED_INVALID_SIZE"],
    [{ evidenceAsOf: "2026-10-05T10:00:00.000Z" }, "BLOCKED_STALE_EVIDENCE"],
    [{ riskChecksPassed: false }, "BLOCKED_RISK"],
  ]) assert.deepEqual(createOrderIntent({ ...fixture, ...change }), { status, intent: null });
});

test("adapter refuses read-only, live-disabled, absent auth, and failed risk", async () => {
  const bridge = createOrderIntent(fixture);
  let calls = 0;
  const mock = async () => { calls++; throw Error("must not invoke"); };
  for (const [mode, guard, expected] of [
    ["READ_ONLY", { authenticated: true, riskChecksPassed: true, allowPaperDryRun: true }, "BLOCKED_MODE"],
    ["LIVE_DISABLED", { authenticated: true, riskChecksPassed: true, allowPaperDryRun: true }, "BLOCKED_MODE"],
    ["PAPER_DRY_RUN", { authenticated: false, riskChecksPassed: true, allowPaperDryRun: true }, "BLOCKED_AUTH"],
    ["PAPER_DRY_RUN", { authenticated: true, riskChecksPassed: false, allowPaperDryRun: true }, "BLOCKED_RISK"],
  ]) assert.equal((await executeOrderIntent(bridge, mode, guard, mock)).status, expected);
  assert.equal(calls, 0);
});

test("adapter revalidates intent hash, symbol policy, and freshness before dry-run", async () => {
  const bridge = createOrderIntent(fixture);
  let calls = 0;
  const mock = async () => { calls++; throw Error("must not invoke"); };
  const base = { authenticated: true, riskChecksPassed: true, allowPaperDryRun: true, qualification: fixture, now: fixture.now };
  for (const guard of [
    { ...base, qualification: { ...fixture, supportedSymbols: [] } },
    { ...base, qualification: { ...fixture, maxNotionalUsdt: 99 } },
    { ...base, now: "2026-10-06T10:06:00.000Z" },
    { ...base, qualification: { ...fixture, symbol: "RQQQUSDT", supportedSymbols: ["RQQQUSDT"] } },
  ]) assert.equal((await executeOrderIntent(bridge, "PAPER_DRY_RUN", guard, mock)).status, "BLOCKED_RISK");
  assert.equal(calls, 0);
});
