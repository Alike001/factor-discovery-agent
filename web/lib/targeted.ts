import fs from "node:fs";
import path from "node:path";

export type TargetedTrial = {
  slot: "A" | "B" | "C";
  family: string;
  trial_number: number | null;
  proposal: null | { name?: string; thesis?: string; economic_mechanism?: string; session_filter?: string[] };
  report: null | { aggregate: string; first_hard_fail: string | null; gates: { name: string; outcome: string; reason: string }[] };
  state?: string;
};
export type TargetedBatch = {
  plan: { slots: Record<string, { title: string; requirements: string[] }>; planned_unique_trials: number };
  trials: TargetedTrial[];
  gate_summary: { gate_distribution: Record<string, number>; outcomes: Record<string, string> };
  diversity: { accepted: boolean; reason: string; families_planned: string[] };
  budget: { logical_calls: number; http_attempts: number; measured_tokens: number; conservative_tokens: number; search_n_before: number; search_n_after: number };
  decision: { status: string; recommendation: string; candidate_count: number; certified_count: number; committed_trials: number; paper_trading_started: boolean; contradiction: string };
};

export function readTargetedBatch(): TargetedBatch {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), "public/evidence/targeted-batch-v2.json"), "utf8")) as TargetedBatch;
}
