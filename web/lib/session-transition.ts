import fs from "node:fs";
import path from "node:path";

export type SessionTransitionClosure = {
  closure: {
    recommendation: string;
    recipe_schema_version: string;
    compiler_version: string;
    ready_families: string[];
    not_ready_families: string[];
    contract_version: string;
    contract_hash: string;
    search_n_after: number;
    qwen_http_attempts_phase: number;
    golden_valid_passed: number;
    golden_invalid_passed: number;
  };
};

export function readSessionTransitionClosure(): SessionTransitionClosure {
  return JSON.parse(
    fs.readFileSync(path.join(process.cwd(), "public/evidence/session-transition-closure.json"), "utf8"),
  ) as SessionTransitionClosure;
}
