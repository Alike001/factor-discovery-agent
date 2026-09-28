import fs from "node:fs";
import path from "node:path";

export type Gate = { name: string; outcome: "PASS" | "FAIL" | "INCONCLUSIVE"; reason: string };
export type Expression = { op: string; args?: Expression[]; symbol?: string; field?: string; lookback?: number; threshold?: number; sessions?: string[] };
export type Factor = {
  trial_number: number;
  name: string;
  thesis: string;
  canonical_identity_hash: string;
  duplicate_of: string | null;
  factor_version_id: string | null;
  lifecycle_state: string | null;
  canonical_spec_json: {
    universe: string[]; session_filter: string[]; signal: Expression; horizon_bars: number; rebalance_bars: number;
  } | null;
  metrics_json: {
    aggregate: string; split_timestamp: string; dataset_hash: string;
    metrics: { gross: Metric; net: Metric; is_net: Metric; oos_net: Metric; buy_hold: number };
    data_contract: { start: string; end: string; latest_included_timestamp: string; cost_model_version: string; session_classification_version: string };
  } | null;
  data_contract_json: Record<string, unknown> | null;
  report_hash: string | null;
  created_at: string | null;
  gates: Gate[];
};
type Metric = { total_return: number; sharpe: number | null; max_drawdown: number; fills: number; observations: number };
export type Summary = {
  generated_at: string; protocol: string; protocol_hash: string;
  cycles: { cycle_number: number; status: string; as_of: string; manifest_hash: string; error_code: string | null }[];
  factors: Factor[];
  qwen_runs: { role: string; model: string; endpoint_path: string; token_usage: Record<string, number | string>; latency_ms: number; attempt_count: number; status: string }[];
};

export function readPhase2(): Summary {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), "public/evidence/phase2-summary.json"), "utf8")) as Summary;
}

export function expressionText(node: Expression): string {
  if (node.op === "source") return `${node.symbol}.${node.field}`;
  if (node.op === "signal") return "signal";
  if (node.op === "session_in") return `session ∈ ${(node.sessions ?? []).join("|")}`;
  const args = (node.args ?? []).map(expressionText);
  if (["add", "sub", "mul", "div"].includes(node.op)) return `(${args.join(` ${node.op} `)})`;
  if (["gt", "gte", "lt", "lte"].includes(node.op)) return `${args[0]} ${node.op} ${node.threshold}`;
  return `${node.op}(${args.join(", ")}${node.lookback ? `, ${node.lookback}` : ""})`;
}

export const pct = (value: number) => `${(value * 100).toFixed(2)}%`;
