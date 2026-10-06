import { writeFileSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { currentResearchGate, executeOrderIntent, verifyPublicMarket } from "../server/bitget-agent.ts";

const packageVersion = JSON.parse(readFileSync(fileURLToPath(new URL("../node_modules/@bitget-ai/bitget-agent-sdk/package.json", import.meta.url)), "utf8")).version;
const state = JSON.parse(readFileSync(fileURLToPath(new URL("../public/evidence/latest/RESEARCH_SUMMARY.json", import.meta.url)), "utf8"));
const bridge = currentResearchGate(state);
const execution = await executeOrderIntent(bridge, "READ_ONLY", { authenticated: false, riskChecksPassed: false, allowPaperDryRun: false });
if (bridge.status !== "BLOCKED_NO_CANDIDATE" || bridge.intent !== null || execution.sdkInvoked) throw Error("Frozen research state did not fail closed");
const primary = await verifyPublicMarket("RAMDUSDT");
const fallback = primary.ok ? null : await verifyPublicMarket("BTCUSDT");
const artifact = {
  integration_package: "@bitget-ai/bitget-agent-sdk",
  integration_version: packageVersion,
  mode: "READ_ONLY",
  timestamp: new Date().toISOString(),
  connection_status: primary.ok || fallback?.ok ? "VERIFIED_READ_ONLY" : "UNVERIFIED",
  market_tool: primary.ok || fallback?.ok ? "VERIFIED" : "UNVERIFIED",
  rtoken_probe: primary,
  fallback_probe: fallback,
  execution_adapter: "READY_DORMANT",
  execution_mode: "READ_ONLY",
  capital_gate: state.paper_eligible === 0 ? "CLOSED" : "UNVERIFIED",
  current_order: bridge.status,
  historical_research_source: "UNCHANGED_COMMITTED_BITGET_REALITY_EVIDENCE",
  account_write_calls: Number(execution.sdkInvoked),
  real_orders: 0,
};
const output = fileURLToPath(new URL("../public/evidence/BITGET_AGENT_SDK_STATUS.json", import.meta.url));
writeFileSync(output, JSON.stringify(artifact, null, 2) + "\n");
console.log(JSON.stringify({ connection_status: artifact.connection_status, rtoken_result: primary.resultClass, fallback_result: fallback?.resultClass ?? null, output: "web/public/evidence/BITGET_AGENT_SDK_STATUS.json" }));
