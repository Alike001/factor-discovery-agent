import fs from "node:fs";
import path from "node:path";

export type FdpV3Trial = {
  slot: "A" | "B";
  family: string;
  trial_number: number | null;
  recipe: Record<string, unknown> | null;
  compiled: { signal?: Record<string, unknown> } | null;
  report: {
    aggregate: string;
    first_hard_fail: string | null;
    gates: Array<{ name: string; outcome: string; reason: string }>;
    dsr?: { status: string; probability: number | null };
    stability?: { status: string };
  } | null;
};

export type FdpV3Evidence = {
  decision: {
    protocol_version: string;
    protocol_hash: string;
    search_n_after: number;
    logical_calls: number;
    http_attempts: number;
    charged_tokens: number;
    candidates: number;
    certified: number;
    recommendation: string;
  };
  budget: { hard_limit: number };
  trials: FdpV3Trial[];
};

export function readFdpV3(): FdpV3Evidence {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), "public/evidence/fdp-v3-batch.json"), "utf8")) as FdpV3Evidence;
}
