import json
from pathlib import Path

from app.product.hardening import executable_hypothesis, public_package_errors, semantic_lint

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "web/public/evidence/latest"


def load(name: str):
    return json.loads((PUBLIC / name).read_text())


def test_canonical_description_is_deterministic_and_recipe_driven():
    recipe = load("TRIAL_8.json")["recipe"]
    assert executable_hypothesis(recipe) == executable_hypothesis(dict(reversed(list(recipe.items()))))
    assert "positive" in executable_hypothesis(recipe).lower()
    assert "continuation" in executable_hypothesis(recipe).lower()


def test_rationale_never_drives_execution_and_mismatch_is_visible():
    trial = load("TRIAL_8.json")
    changed = {**trial["recipe"], "thesis": "Completely different prose"}
    assert executable_hypothesis(changed) == trial["executable_hypothesis"]
    assert "RATIONALE_RECIPE_DIRECTION_MISMATCH" in semantic_lint(trial["recipe"])


def test_invalid_recipe_never_gets_fabricated_executable_description():
    recipe = {"family": "session_transition", "invalid": True}
    assert executable_hypothesis(recipe) == "Executable hypothesis unavailable because no valid structured recipe compiled."


def test_public_package_is_sanitized_and_frozen():
    files = {path.name: json.loads(path.read_text()) for path in PUBLIC.glob("*.json") if path.name != "MANIFEST.json"}
    assert public_package_errors(files) == []
    text = json.dumps(files).lower()
    for forbidden in ("authorization", "api_secret", "passphrase", "raw_prompt", "reasoning_content", "database_url"):
        assert f'"{forbidden}"' not in text


def test_proof_data_matches_committed_evidence():
    source = json.loads((ROOT / "evidence/fdp-v3-batch/decision.json").read_text())
    public = load("RESEARCH_SUMMARY.json")
    assert public["global_search_n"] == source["search_n_after"] == 9
    assert public["candidates"] == source["candidates"] == 0
    assert public["certified"] == source["certified"] == 0


def test_paper_is_locked_and_empty_without_candidate():
    summary = load("RESEARCH_SUMMARY.json")
    assert summary["paper_engine"] == "LOCKED_NO_CANDIDATE"
    assert summary["candidates"] == 0
    assert summary["paper"] == {"capital_usdt": 0, "fills": 0, "orders": 0, "positions": 0}


def test_replay_is_stored_only_and_chain_summary_matches():
    replay = load("REPLAY_TRIAL_8.json")
    chain = load("EVIDENCE_CHAIN_SUMMARY.json")
    decision = json.loads((ROOT / "evidence/fdp-v3-batch/decision.json").read_text())["evidence_chain"]
    assert replay["qwen_calls"] == replay["network_calls"] == 0
    assert all(step["status"] in {"AVAILABLE", "UNAVAILABLE"} for step in replay["steps"])
    assert chain["event_count"] == decision["event_count"] == 190
    assert chain["head_hash"] == decision["head_hash"]


def test_landing_page_is_evidence_backed_and_routes_to_real_surfaces():
    page = (ROOT / "web/app/page.tsx").read_text()
    summary = load("RESEARCH_SUMMARY.json")
    chain = load("EVIDENCE_CHAIN_SUMMARY.json")

    assert "redirect(" not in page
    assert "chainSummary()" in page and "summary()" in page and "trials()" in page
    assert "AI proposes the trade. " in page
    assert "Zero trades is an outcome," in page
    for href in ("/lab", "/proof", "/replay?trial=8", "/paper", "/factors/trial-8", "/factors/trial-9", "/ledger", "/system"):
        assert f'href="{href}"' in page

    assert summary["trials"] == 9
    assert summary["candidates"] == summary["certified"] == summary["paper_eligible"] == 0
    assert summary["paper"] == {"capital_usdt": 0, "fills": 0, "orders": 0, "positions": 0}
    assert chain["event_count"] == 190 and chain["status"] == "PASS"
    assert "LIVE TRADING" not in page and "profitable" not in page.lower()
