from __future__ import annotations

import json
import time
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.evidence import canonical_hash

T = TypeVar("T", bound=BaseModel)


async def probe_schema(
    client: httpx.AsyncClient,
    *,
    model: str,
    api_key: str,
    schema: type[T],
    purpose: str,
) -> dict[str, Any]:
    prompt = (
        f"Return JSON only for {purpose}. It must validate against this JSON schema: "
        f"{json.dumps(schema.model_json_schema(), separators=(',', ':'))}"
    )
    body = {"model": model, "input": prompt, "max_output_tokens": 900}
    async def request(request_body: dict[str, Any]) -> tuple[httpx.Response, dict[str, Any], int]:
        started = time.perf_counter()
        response = await client.post(
            "/responses",
            headers={"Authorization": f"Bearer {api_key}"},
            json=request_body,
        )
        latency = round((time.perf_counter() - started) * 1000)
        try:
            payload = response.json() if response.content else {}
        except ValueError:
            payload = {"non_json_response": response.text}
        return response, payload, latency

    def extract_text(payload: dict[str, Any]) -> str:
        if payload.get("output_text"):
            return payload["output_text"]
        chunks = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    chunks.append(content.get("text", ""))
        return "".join(chunks)

    response, raw_payload, latency_ms = await request(body)
    raw_text = extract_text(raw_payload)
    valid = False
    error = None
    repair_required = False
    repair_payload: dict[str, Any] | None = None
    try:
        schema.model_validate_json(raw_text)
        valid = True
    except (ValidationError, ValueError) as exc:
        error = str(exc)
        repair_required = True
        repair_body = {
            "model": model,
            "input": (
                f"Repair this invalid {purpose} response and return JSON only. Schema: "
                f"{json.dumps(schema.model_json_schema(), separators=(',', ':'))}. "
                f"Validation error: {error}. Invalid response: {raw_text}"
            ),
            "max_output_tokens": 900,
        }
        repair_response, repair_payload, repair_latency = await request(repair_body)
        latency_ms += repair_latency
        repaired_text = extract_text(repair_payload)
        try:
            schema.model_validate_json(repaired_text)
            valid = True
            error = None
            raw_text = repaired_text
            response = repair_response
        except (ValidationError, ValueError) as repair_exc:
            error = str(repair_exc)
    return {
        "purpose": purpose,
        "request_hash": canonical_hash(body),
        "response_hash": canonical_hash(repair_payload or raw_payload),
        "latency_ms": latency_ms,
        "http_status": response.status_code,
        "observed_model": (repair_payload or raw_payload).get("model"),
        "raw_text": raw_text,
        "validation": {"valid": valid, "error": error},
        "repair_required": repair_required,
        "repair_attempts": 1 if repair_required else 0,
    }
