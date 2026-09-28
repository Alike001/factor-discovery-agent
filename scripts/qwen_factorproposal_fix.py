#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.config import Settings  # noqa: E402
from app.evidence import write_json  # noqa: E402
from app.qwen.client import probe_factor_proposal_compat, probe_schema  # noqa: E402
from app.qwen.models import FactorProposal, LifecycleDecision, PortfolioDecision  # noqa: E402

OUTPUT = ROOT / "evidence" / "preflight-v3"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def passed(probe: dict[str, Any]) -> bool:
    return (
        probe["http_status"] == 200
        and probe["validation"]["valid"]
        and probe["repair_attempts"] <= 1
    )


def public_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": artifact["status"],
        "requested_model": artifact["requested_model"],
        "probes": [
            {
                "purpose": probe["purpose"],
                "endpoint_path": probe["endpoint_path"],
                "http_status": probe["http_status"],
                "latency_ms": probe["latency_ms"],
                "valid": probe["validation"]["valid"],
                "repair_attempts": probe["repair_attempts"],
                "error_code": probe["error_code"],
                "response_metadata": probe["response_metadata"],
            }
            for probe in artifact["probes"]
        ],
    }


def ensure_no_key(artifact: dict[str, Any], api_key: str) -> None:
    if api_key in json.dumps(artifact, sort_keys=True):
        raise RuntimeError("credential exposure guard triggered")


async def compatibility(settings: Settings) -> int:
    async with httpx.AsyncClient(base_url=settings.qwen_base_url, timeout=120.0) as client:
        probe = await probe_factor_proposal_compat(
            client,
            model=settings.qwen_model,
            api_key=settings.qwen_api_key or "",
            schema=FactorProposal,
            max_repair_attempts=0,
        )
    artifact = {
        "generated_at": now_iso(),
        "status": "PASS" if passed(probe) else "FAIL",
        "endpoint": f"{settings.qwen_base_url}/chat/completions",
        "requested_model": settings.qwen_model,
        "observed_models": [probe["observed_model"]] if probe["observed_model"] else [],
        "probe_count": 1,
        "valid_probe_count": int(probe["validation"]["valid"]),
        "probes": [probe],
        "credential_source": "environment",
        "credential_persisted": False,
        "authorization_logged": False,
    }
    ensure_no_key(artifact, settings.qwen_api_key or "")
    write_json(OUTPUT / "factor-proposal-compatibility.json", artifact)
    print(json.dumps(public_summary(artifact), indent=2))
    return 0 if artifact["status"] == "PASS" else 1


async def final_gate(settings: Settings) -> int:
    async with httpx.AsyncClient(base_url=settings.qwen_base_url, timeout=120.0) as client:
        probes = [
            await probe_factor_proposal_compat(
                client,
                model=settings.qwen_model,
                api_key=settings.qwen_api_key or "",
                schema=FactorProposal,
                max_repair_attempts=1,
            ),
            await probe_schema(
                client,
                model=settings.qwen_model,
                api_key=settings.qwen_api_key or "",
                schema=LifecycleDecision,
                purpose="LifecycleDecision",
                prompt_detail=(
                    "This is a schema transport probe. Return ABANDON with a concise reason and "
                    "revision_intent null."
                ),
            ),
            await probe_schema(
                client,
                model=settings.qwen_model,
                api_key=settings.qwen_api_key or "",
                schema=PortfolioDecision,
                purpose="PortfolioDecision",
                prompt_detail=(
                    "This is a schema transport probe. Return HOLD with symbol null, "
                    "factor_version_id null, target_weight 0, a concise reason, and a concise "
                    "invalidation condition."
                ),
            ),
        ]
    gate_passed = len(probes) == 3 and all(passed(probe) for probe in probes)
    artifact = {
        "generated_at": now_iso(),
        "status": "PASS" if gate_passed else "FAIL",
        "endpoints": {
            "FactorProposal": f"{settings.qwen_base_url}/chat/completions",
            "LifecycleDecision": f"{settings.qwen_base_url}/responses",
            "PortfolioDecision": f"{settings.qwen_base_url}/responses",
        },
        "requested_model": settings.qwen_model,
        "observed_models": sorted(
            {probe["observed_model"] for probe in probes if probe["observed_model"]}
        ),
        "probe_count": len(probes),
        "valid_probe_count": sum(probe["validation"]["valid"] for probe in probes),
        "probes": probes,
        "credential_source": "environment",
        "credential_persisted": False,
        "authorization_logged": False,
    }
    ensure_no_key(artifact, settings.qwen_api_key or "")
    write_json(OUTPUT / "qwen.json", artifact)
    print(json.dumps(public_summary(artifact), indent=2))
    return 0 if gate_passed else 1


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("compatibility", "final"))
    args = parser.parse_args()
    settings = Settings.from_env()
    if not settings.qwen_api_key:
        print(json.dumps({"status": "BLOCKED_KEY"}))
        return 2
    if args.mode == "compatibility":
        return await compatibility(settings)
    return await final_gate(settings)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
