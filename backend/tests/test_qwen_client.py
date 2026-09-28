from __future__ import annotations

import json

import httpx
import pytest

from app.qwen.client import probe_factor_proposal_compat
from app.qwen.models import FactorProposal


def valid_proposal() -> dict:
    return {
        "name": "Overnight relative return probe",
        "thesis": "A transport-only price hypothesis for schema validation.",
        "universe": ["RNVDAUSDT", "RQQQUSDT"],
        "session_filter": ["overnight"],
        "signal": {
            "op": "sub",
            "args": [
                {
                    "op": "ret",
                    "lookback": 12,
                    "args": [{"op": "source", "symbol": "RNVDAUSDT", "field": "close"}],
                },
                {
                    "op": "ret",
                    "lookback": 12,
                    "args": [{"op": "source", "symbol": "RQQQUSDT", "field": "close"}],
                },
            ],
        },
        "entry_condition": {"op": "gt", "threshold": 1.0, "args": [{"op": "signal"}]},
        "exit_condition": {"op": "lte", "threshold": 0.0, "args": [{"op": "signal"}]},
        "horizon_bars": 12,
        "rebalance_bars": 1,
        "direction": "long_flat",
        "rationale": "Transport probe only; this is not discovered alpha.",
    }


@pytest.mark.asyncio
async def test_factor_proposal_uses_dedicated_chat_profile() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": "qwen3.8-max",
                "choices": [
                    {
                        "message": {"content": json.dumps(valid_proposal()), "reasoning_content": "hidden"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 200,
                    "total_tokens": 300,
                    "completion_tokens_details": {"reasoning_tokens": 50},
                },
            },
        )

    async with httpx.AsyncClient(
        base_url="https://example.test/v1", transport=httpx.MockTransport(handler)
    ) as client:
        result = await probe_factor_proposal_compat(
            client,
            model="qwen3.8-max",
            api_key="test-only",
            schema=FactorProposal,
        )

    assert captured["reasoning_effort"] == "low"
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["max_tokens"] == 2400
    assert captured["temperature"] == 0
    assert "enable_thinking" not in captured
    assert result["validation"]["valid"] is True
    assert result["response_metadata"]["reasoning_length"] == 6
    assert result["response_metadata"]["usage"]["reasoning_tokens"] == 50
    assert "hidden" not in json.dumps(result)


@pytest.mark.asyncio
async def test_http_200_empty_final_is_classified_without_repair() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "model": "qwen3.8-max",
                "choices": [{"message": {"content": ""}, "finish_reason": "stop"}],
            },
        )

    async with httpx.AsyncClient(
        base_url="https://example.test/v1", transport=httpx.MockTransport(handler)
    ) as client:
        result = await probe_factor_proposal_compat(
            client,
            model="qwen3.8-max",
            api_key="test-only",
            schema=FactorProposal,
        )

    assert calls == 1
    assert result["error_code"] == "EMPTY_FINAL_CONTENT"
    assert result["repair_attempts"] == 0
    assert result["response_metadata"]["usage"]["output_tokens"] == "UNMEASURED"
