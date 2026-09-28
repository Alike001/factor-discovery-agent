import fs from "node:fs";
import path from "node:path";

export type ProtocolReview = {
  review: {
    status: string;
    qwen_http_attempts_phase: number;
    search_n_after: number;
    recipe_schema_version: string;
    compiler_version: string;
    ready_families: string[];
    golden_fixtures_passed: number;
    generated_prompt_estimated_tokens: number;
    fdp_v3_draft_active: boolean;
    recommendation: string;
    reason: string;
  };
};

export function readProtocolReview(): ProtocolReview {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), "public/evidence/protocol-review-v3.json"), "utf8")) as ProtocolReview;
}
