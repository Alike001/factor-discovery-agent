from __future__ import annotations

import json
import time
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.evidence import canonical_hash

T = TypeVar("T", bound=BaseModel)
UNMEASURED = "UNMEASURED"


def _parse_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json() if response.content else {}
    except ValueError:
        return {"non_json_response": response.text}
    return payload if isinstance(payload, dict) else {"unexpected_response": payload}


def _usage(payload: dict[str, Any]) -> dict[str, int | str]:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return {
            "input_tokens": UNMEASURED,
            "output_tokens": UNMEASURED,
            "reasoning_tokens": UNMEASURED,
            "total_tokens": UNMEASURED,
        }
    details = usage.get("completion_tokens_details") or usage.get("output_tokens_details") or {}
    return {
        "input_tokens": usage.get("prompt_tokens", usage.get("input_tokens", UNMEASURED)),
        "output_tokens": usage.get("completion_tokens", usage.get("output_tokens", UNMEASURED)),
        "reasoning_tokens": details.get("reasoning_tokens", UNMEASURED),
        "total_tokens": usage.get("total_tokens", UNMEASURED),
    }


def _failure_code(*, status_code: int, final_text: str, finish_reason: str | None) -> str | None:
    if status_code != 200:
        return "PROVIDER_ERROR"
    if not final_text:
        if finish_reason in {"length", "max_tokens"}:
            return "TRUNCATED_BEFORE_FINAL"
        return "EMPTY_FINAL_CONTENT"
    return None


async def _post(
    client: httpx.AsyncClient,
    *,
    path: str,
    api_key: str,
    body: dict[str, Any],
) -> tuple[httpx.Response, dict[str, Any], int]:
    started = time.perf_counter()
    response = await client.post(
        path,
        headers={"Authorization": f"Bearer {api_key}"},
        json=body,
    )
    latency_ms = round((time.perf_counter() - started) * 1000)
    return response, _parse_payload(response), latency_ms


def _responses_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    chunks: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") in {"output_text", "text"}:
                chunks.append(content.get("text", ""))
    return "".join(chunks)


def _responses_metadata(payload: dict[str, Any], final_text: str, max_tokens: int) -> dict[str, Any]:
    output = payload.get("output") if isinstance(payload.get("output"), list) else []
    return {
        "response_top_level_keys": sorted(payload),
        "status": payload.get("status", UNMEASURED),
        "incomplete_details": payload.get("incomplete_details", UNMEASURED),
        "finish_reason": payload.get("finish_reason", UNMEASURED),
        "output_item_types": [item.get("type", "unknown") for item in output if isinstance(item, dict)],
        "final_content_length": len(final_text),
        "reasoning_length": UNMEASURED,
        "usage": _usage(payload),
        "configured_max_output_tokens": max_tokens,
    }


def _chat_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    return content if isinstance(content, str) else ""


def _chat_metadata(payload: dict[str, Any], final_text: str, max_tokens: int) -> dict[str, Any]:
    choices = payload.get("choices")
    choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else {}
    message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
    reasoning = message.get("reasoning_content")
    return {
        "response_top_level_keys": sorted(payload),
        "status": payload.get("status", UNMEASURED),
        "incomplete_details": payload.get("incomplete_details", UNMEASURED),
        "finish_reason": choice.get("finish_reason", UNMEASURED),
        "output_item_types": ["message"] if message else [],
        "final_content_length": len(final_text),
        "reasoning_length": len(reasoning) if isinstance(reasoning, str) else UNMEASURED,
        "usage": _usage(payload),
        "configured_max_tokens": max_tokens,
    }


def _validate(schema: type[T], raw_text: str) -> tuple[bool, str | None]:
    try:
        schema.model_validate_json(raw_text)
    except (ValidationError, ValueError) as exc:
        return False, str(exc)
    return True, None


def _parsed(schema: type[T], raw_text: str) -> dict[str, Any] | None:
    try:
        return schema.model_validate_json(raw_text).model_dump(mode="json")
    except (ValidationError, ValueError):
        return None


async def probe_schema(
    client: httpx.AsyncClient,
    *,
    model: str,
    api_key: str,
    schema: type[T],
    purpose: str,
    prompt_detail: str = "",
) -> dict[str, Any]:
    """Probe the existing Responses profile used by lifecycle and portfolio decisions."""
    prompt = (
        f"Return JSON only for {purpose}. It must validate against this JSON schema: "
        f"{json.dumps(schema.model_json_schema(), separators=(',', ':'))}. {prompt_detail}"
    )
    max_tokens = 900
    body = {"model": model, "input": prompt, "max_output_tokens": max_tokens}
    response, payload, latency_ms = await _post(
        client, path="/responses", api_key=api_key, body=body
    )
    raw_text = _responses_text(payload)
    valid, error = _validate(schema, raw_text)
    repair_attempts = 0
    final_payload = payload
    final_response = response

    if not valid:
        repair_attempts = 1
        repair_body = {
            "model": model,
            "input": (
                f"Repair this invalid {purpose} response and return JSON only. Schema: "
                f"{json.dumps(schema.model_json_schema(), separators=(',', ':'))}. "
                f"Validation error: {error}. Invalid response: {raw_text}"
            ),
            "max_output_tokens": max_tokens,
        }
        final_response, final_payload, repair_latency = await _post(
            client, path="/responses", api_key=api_key, body=repair_body
        )
        latency_ms += repair_latency
        raw_text = _responses_text(final_payload)
        valid, error = _validate(schema, raw_text)

    metadata = _responses_metadata(final_payload, raw_text, max_tokens)
    finish_reason = metadata["finish_reason"]
    return {
        "purpose": purpose,
        "endpoint_path": "/responses",
        "request_hash": canonical_hash(body),
        "response_hash": canonical_hash(final_payload),
        "latency_ms": latency_ms,
        "http_status": final_response.status_code,
        "observed_model": final_payload.get("model"),
        "provider_error": final_payload.get("error") or final_payload.get("non_json_response"),
        "final_text": raw_text,
        "parsed_json": _parsed(schema, raw_text),
        "response_metadata": metadata,
        "error_code": _failure_code(
            status_code=final_response.status_code,
            final_text=raw_text,
            finish_reason=finish_reason if isinstance(finish_reason, str) else None,
        ),
        "validation": {"valid": valid, "error": error},
        "repair_required": repair_attempts > 0,
        "repair_attempts": repair_attempts,
    }


def factor_proposal_prompt(schema: type[BaseModel], research_mandate: str = "") -> str:
    example = {
        "name": "Overnight relative return probe",
        "thesis": "A transport-only price hypothesis for validating the proposal schema.",
        "universe": ["RNVDAUSDT", "RQQQUSDT"],
        "session_filter": ["overnight"],
        "signal": {
            "op": "sub",
            "args": [
                {"op": "ret", "lookback": 12, "args": [{"op": "source", "symbol": "RNVDAUSDT", "field": "close"}]},
                {"op": "ret", "lookback": 12, "args": [{"op": "source", "symbol": "RQQQUSDT", "field": "close"}]},
            ],
        },
        "entry_condition": {"op": "gt", "threshold": 1.0, "args": [{"op": "signal"}]},
        "exit_condition": {"op": "lte", "threshold": 0.0, "args": [{"op": "signal"}]},
        "horizon_bars": 12,
        "rebalance_bars": 1,
        "direction": "long_flat",
        "rationale": "Transport probe only; this is not discovered alpha.",
    }
    return (
        "Create one falsifiable rToken session FactorProposal. "
        "Use only symbols and sessions named by the research mandate and only OHLC price features; volume is forbidden. "
        "Use only operators, lookbacks, thresholds, and fields allowed by the schema. "
        f"JSON schema:{json.dumps(schema.model_json_schema(), separators=(',', ':'))}. "
        f"Research mandate:{research_mandate or 'schema transport probe; do not claim discovered alpha'}. "
        f"Minimal shape example:{json.dumps(example, separators=(',', ':'))}. "
        "Return one JSON object and nothing else."
    )


async def probe_factor_proposal_compat(
    client: httpx.AsyncClient,
    *,
    model: str,
    api_key: str,
    schema: type[T],
    max_repair_attempts: int = 0,
    research_mandate: str = "",
) -> dict[str, Any]:
    """Use the dedicated low-reasoning Chat Completions compatibility profile."""
    prompt = factor_proposal_prompt(schema, research_mandate)
    max_tokens = 2400

    def body_for(user_prompt: str) -> dict[str, Any]:
        return {
            "model": model,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "reasoning_effort": "low",
            "max_tokens": max_tokens,
        }

    body = body_for(prompt)
    response, payload, latency_ms = await _post(
        client, path="/chat/completions", api_key=api_key, body=body
    )
    raw_text = _chat_text(payload)
    valid, error = _validate(schema, raw_text)
    repair_attempts = 0
    final_payload = payload
    final_response = response

    if not valid and max_repair_attempts:
        repair_attempts = 1
        repair_prompt = (
            f"Repair this invalid FactorProposal. Validation error: {error}. "
            f"Invalid JSON:{raw_text}. {prompt}"
        )
        final_response, final_payload, repair_latency = await _post(
            client,
            path="/chat/completions",
            api_key=api_key,
            body=body_for(repair_prompt),
        )
        latency_ms += repair_latency
        raw_text = _chat_text(final_payload)
        valid, error = _validate(schema, raw_text)

    metadata = _chat_metadata(final_payload, raw_text, max_tokens)
    finish_reason = metadata["finish_reason"]
    return {
        "purpose": "FactorProposal",
        "endpoint_path": "/chat/completions",
        "profile": {
            "reasoning_effort": "low",
            "response_format": "json_object",
            "temperature": 0,
            "max_tokens": max_tokens,
        },
        "request_hash": canonical_hash(body),
        "response_hash": canonical_hash(final_payload),
        "latency_ms": latency_ms,
        "http_status": final_response.status_code,
        "observed_model": final_payload.get("model"),
        "provider_error": final_payload.get("error") or final_payload.get("non_json_response"),
        "final_text": raw_text,
        "parsed_json": _parsed(schema, raw_text),
        "response_metadata": metadata,
        "error_code": _failure_code(
            status_code=final_response.status_code,
            final_text=raw_text,
            finish_reason=finish_reason if isinstance(finish_reason, str) else None,
        ),
        "validation": {"valid": valid, "error": error},
        "repair_required": repair_attempts > 0,
        "repair_attempts": repair_attempts,
    }
