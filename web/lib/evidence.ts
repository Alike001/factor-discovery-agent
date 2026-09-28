import fs from "node:fs";
import path from "node:path";

const ROOT = path.join(process.cwd(), "public/evidence/latest");

export type Outcome = "PASS" | "FAIL" | "INCONCLUSIVE" | "NOT RUN";
export type Gate = { name: string; outcome: Outcome; reason: string; value?: unknown };
export type Trial = {
  slot: string; trial_number: number; protocol: string; family: string; outcome: string;
  first_hard_fail: string; recipe: Record<string, unknown>; executable_hypothesis: string;
  qwen_rationale: string; semantic_lint: string[]; compiled: Record<string, unknown> | null;
  gates: Gate[]; metrics: Record<string, any> | null; data_contract: Record<string, any>;
  dsr: Record<string, any> | null; stability: Record<string, any> | null;
  permutation: Record<string, any> | null; lifecycle: Record<string, any> | null;
  recipe_hash: string | null; ast_hash: string | null; report_hash: string; dataset_hash: string;
  search_n: number; qwen_metadata: Record<string, unknown>;
};
export type Summary = {
  generated_at: string; source_commit: string; search_program: string; protocol: string;
  discovery_status: string; discovery_reason: string; global_search_n: number; trials: number;
  candidates: number; certified: number; paper_eligible: number;
  paper: { capital_usdt: number; positions: number; orders: number; fills: number };
  execution_mode: string; paper_engine: string; live_execution: string;
  latest_verified_source_timestamp: string; additional_discovery: string;
  qwen_http_attempts_total: number; controlled_batch: { logical_calls: number; http_attempts: number };
  truth_line: string;
};
export type ChainSummary = {
  event_count: number; events_exported: number; head_hash: string; source: string;
  status: "PASS" | "FAIL"; verified_at: string;
};

export function evidence<T>(name: string): T {
  return JSON.parse(fs.readFileSync(path.join(ROOT, name), "utf8")) as T;
}

export const summary = () => evidence<Summary>("RESEARCH_SUMMARY.json");
export const chainSummary = () => evidence<ChainSummary>("EVIDENCE_CHAIN_SUMMARY.json");
export const trials = () => [evidence<Trial>("TRIAL_8.json"), evidence<Trial>("TRIAL_9.json")];
export const formatPct = (value: number | null | undefined) => value == null ? "—" : `${(value * 100).toFixed(2)}%`;
export const shortHash = (value: string | null | undefined) => value ? `${value.slice(0, 12)}…${value.slice(-6)}` : "—";

export function expression(node: any): string {
  if (!node) return "NOT COMPILED";
  if (node.op === "source") return `${node.symbol}.${node.field}`;
  if (node.op === "signal") return "signal";
  const args = (node.args ?? []).map(expression);
  if (["gt", "gte", "lt", "lte"].includes(node.op)) return `${args[0]} ${node.op} ${node.threshold}`;
  return `${node.op}(${args.join(", ")}${node.lookback ? `, ${node.lookback}` : ""})`;
}
