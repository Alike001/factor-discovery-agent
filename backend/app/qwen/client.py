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
    started = time.perf_counter()
    response = await client.post(
        "/responses",
        headers={"Authorization": f"Bearer {api_key}"},
        json=body,
    )
    latency_ms = round((time.perf_counter() - started) * 1000)
    raw_payload = response.json() if response.content else {}
    raw_text = raw_payload.get("output_text", "")
    if not raw_text:
        chunks = []
        for item in raw_payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    chunks.append(content.get("text", ""))
        raw_text = "".join(chunks)
    valid = False
    error = None
    try:
        schema.model_validate_json(raw_text)
        valid = True
    except (ValidationError, ValueError) as exc:
        error = str(exc)
    return {
        "purpose": purpose,
        "request_hash": canonical_hash(body),
        "response_hash": canonical_hash(raw_payload),
        "latency_ms": latency_ms,
        "http_status": response.status_code,
        "raw_text": raw_text,
        "validation": {"valid": valid, "error": error},
        "repair_required": False,
    }

