import fs from "node:fs";
import path from "node:path";

export type Dsr = { status: "PASS" | "FAIL" | "INCONCLUSIVE"; reason_code: string; probability: number | null; benchmark_sharpe?: number; observed_sharpe?: number | null; threshold: number; search_n: number };
export type StabilityBlock = { start: string; end: string; observations: number; fills: number; net_return: number; payoff_sign: number; evaluable: boolean; absolute_pnl_contribution: number | null };
export type HardenedFactor = { trial_number: number; name: string; terminal_phase2_state: string; scope: string; first_hard_fail: string | null; dsr: Dsr; stability: { status: "PASS" | "FAIL" | "INCONCLUSIVE"; reason_code: string; evaluable_blocks: number; session_purity: boolean; blocks: StabilityBlock[] } };
export type Phase3Summary = { method_version: string; qwen_http_attempts_phase3: number; search_n: number; search_hurdle: { sr_star: number; sigma_sr: number }; gate_distribution: Record<string, number>; recommendation: string; factors: HardenedFactor[] };

export function readPhase3(): Phase3Summary {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), "public/evidence/phase3-replay-summary.json"), "utf8")) as Phase3Summary;
}
