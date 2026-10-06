// Server-side readiness boundary. Never import this module from a client component.
import { createHash } from "node:crypto";
import {
  BitgetRestClient, buildTools, loadConfig, safeInvoke,
  type SafeResult, type ToolSpec,
} from "@bitget-ai/bitget-agent-sdk";

export type ExecutionMode = "READ_ONLY" | "PAPER_DRY_RUN" | "LIVE_DISABLED";
export type Direction = "BUY" | "SELL";
export type GateInput = Readonly<{
  factorId: string;
  lifecycle: "CANDIDATE" | "CERTIFIED" | "REJECTED";
  evidenceGatesPassed: boolean;
  capitalGateOpen: boolean;
  symbol: string;
  supportedSymbols: readonly string[];
  direction: Direction;
  quantity: number;
  notionalUsdt: number;
  maxNotionalUsdt: number;
  evidenceAsOf: string;
  now: string;
  maxEvidenceAgeMs: number;
  riskChecksPassed: boolean;
}>;
export type BlockReason =
  | "BLOCKED_NO_CANDIDATE" | "BLOCKED_EVIDENCE" | "BLOCKED_CAPITAL_GATE"
  | "BLOCKED_UNSUPPORTED_SYMBOL" | "BLOCKED_INVALID_DIRECTION"
  | "BLOCKED_INVALID_SIZE" | "BLOCKED_STALE_EVIDENCE" | "BLOCKED_RISK";
export type OrderIntent = Readonly<{
  kind: "ORDER_INTENT_V1";
  factorId: string;
  symbol: string;
  category: "SPOT";
  direction: Direction;
  quantity: number;
  notionalUsdt: number;
  evidenceAsOf: string;
  intentHash: string;
}>;
export type BridgeResult = { status: "READY"; intent: OrderIntent } | { status: BlockReason; intent: null };

function validPositive(value: number): boolean { return Number.isFinite(value) && value > 0; }

export function createOrderIntent(input: GateInput): BridgeResult {
  if (input.lifecycle !== "CANDIDATE" && input.lifecycle !== "CERTIFIED") return { status: "BLOCKED_NO_CANDIDATE", intent: null };
  if (!input.evidenceGatesPassed) return { status: "BLOCKED_EVIDENCE", intent: null };
  if (!input.capitalGateOpen) return { status: "BLOCKED_CAPITAL_GATE", intent: null };
  if (!input.supportedSymbols.includes(input.symbol) || !/^R[A-Z0-9]+USDT$/.test(input.symbol)) return { status: "BLOCKED_UNSUPPORTED_SYMBOL", intent: null };
  if (input.direction !== "BUY" && input.direction !== "SELL") return { status: "BLOCKED_INVALID_DIRECTION", intent: null };
  if (!validPositive(input.quantity) || !validPositive(input.notionalUsdt) || !validPositive(input.maxNotionalUsdt) || input.notionalUsdt > input.maxNotionalUsdt) return { status: "BLOCKED_INVALID_SIZE", intent: null };
  const asOf = Date.parse(input.evidenceAsOf);
  const now = Date.parse(input.now);
  if (!Number.isFinite(asOf) || !Number.isFinite(now) || !validPositive(input.maxEvidenceAgeMs) || asOf > now || now - asOf > input.maxEvidenceAgeMs) return { status: "BLOCKED_STALE_EVIDENCE", intent: null };
  if (!input.riskChecksPassed) return { status: "BLOCKED_RISK", intent: null };
  const fields = { kind: "ORDER_INTENT_V1" as const, factorId: input.factorId, symbol: input.symbol, category: "SPOT" as const, direction: input.direction, quantity: input.quantity, notionalUsdt: input.notionalUsdt, evidenceAsOf: input.evidenceAsOf };
  if (!fields.factorId.trim()) return { status: "BLOCKED_RISK", intent: null };
  return { status: "READY", intent: { ...fields, intentHash: createHash("sha256").update(JSON.stringify(fields)).digest("hex") } };
}

export function currentResearchGate(state: { candidates: number; certified: number; paper_eligible: number; latest_verified_source_timestamp: string }): BridgeResult {
  // The snapshot has no qualified factor or per-factor execution authorization.
  // Do not synthesize those fields from trial records.
  if (state.candidates === 0 && state.certified === 0 && state.paper_eligible === 0) return { status: "BLOCKED_NO_CANDIDATE", intent: null };
  return { status: "BLOCKED_CAPITAL_GATE", intent: null };
}

export type ExecutionResult =
  | { status: "BLOCKED_NO_CANDIDATE" | "BLOCKED_MODE" | "BLOCKED_AUTH" | "BLOCKED_RISK"; sdkInvoked: false }
  | { status: "DRY_RUN_PREVIEW" | "SDK_REFUSED"; sdkInvoked: true; result: SafeResult };

type Invoke = (tool: ToolSpec, args: Record<string, unknown>) => Promise<SafeResult>;
type ExecutionGuard = {
  authenticated: boolean;
  riskChecksPassed: boolean;
  allowPaperDryRun: boolean;
  qualification?: GateInput;
  now?: string;
};

export async function executeOrderIntent(
  bridge: BridgeResult,
  mode: ExecutionMode,
  guard: ExecutionGuard,
  invoke?: Invoke,
): Promise<ExecutionResult> {
  if (bridge.status !== "READY") return { status: "BLOCKED_NO_CANDIDATE", sdkInvoked: false };
  if (mode !== "PAPER_DRY_RUN" || !guard.allowPaperDryRun) return { status: "BLOCKED_MODE", sdkInvoked: false };
  if (!guard.authenticated) return { status: "BLOCKED_AUTH", sdkInvoked: false };
  if (!guard.riskChecksPassed) return { status: "BLOCKED_RISK", sdkInvoked: false };
  const intent = bridge.intent;
  if (!guard.qualification || !guard.now) return { status: "BLOCKED_RISK", sdkInvoked: false };
  const refreshed = createOrderIntent({ ...guard.qualification, now: guard.now });
  if (refreshed.status !== "READY" || refreshed.intent.intentHash !== intent.intentHash) return { status: "BLOCKED_RISK", sdkInvoked: false };
  const args = { action: "place", category: intent.category, symbol: intent.symbol, side: intent.direction.toLowerCase(), orderType: "market", qty: String(intent.quantity), dryRun: true };
  if (invoke) {
    const result = await invoke({ name: "order" } as ToolSpec, args);
    return { status: result.ok ? "DRY_RUN_PREVIEW" : "SDK_REFUSED", sdkInvoked: true, result };
  }
  // An explicit paper dry-run only. No live mode or non-dry-run order path exists.
  const config = loadConfig({ modules: "all", paperTrading: true });
  const tool = buildTools(config).find(item => item.name === "order");
  if (!tool || !config.hasAuth) return { status: "BLOCKED_AUTH", sdkInvoked: false };
  const result = await safeInvoke(tool, args, { config, client: new BitgetRestClient(config) });
  return { status: result.ok ? "DRY_RUN_PREVIEW" : "SDK_REFUSED", sdkInvoked: true, result };
}

export async function verifyPublicMarket(symbol: string): Promise<{ ok: boolean; resultClass: string; tool: string; symbol: string; category: "SPOT"; matchingRows: number }> {
  const config = loadConfig({ modules: "all", readOnly: true });
  const tool = buildTools(config).find(item => item.name === "market");
  if (!tool) return { ok: false, resultClass: "MARKET_TOOL_UNAVAILABLE", tool: "market", symbol, category: "SPOT", matchingRows: 0 };
  const result = await safeInvoke(tool, { action: "tickers", category: "SPOT", symbol }, { config, client: new BitgetRestClient(config) });
  const matchingRows = result.ok && Array.isArray(result.data) ? result.data.filter(row => row && typeof row === "object" && row.symbol === symbol).length : 0;
  // Deliberately return no raw response, private account data, or error text.
  return { ok: result.ok && matchingRows > 0, resultClass: result.ok ? (matchingRows > 0 ? "MATCHING_TICKER" : "NO_MATCHING_TICKER") : "SDK_ERROR", tool: tool.name, symbol, category: "SPOT", matchingRows };
}
