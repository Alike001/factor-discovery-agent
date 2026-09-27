from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bitget_base_url: str = "https://api.bitget.com"
    stock_mcp_url: str = "https://agent.bitget.com/mcp"
    qwen_base_url: str = "https://hackathon.bitgetops.com/v1"
    qwen_model: str = "qwen3.8-max"
    qwen_api_key: str | None = None
    bitget_api_key: str | None = None
    bitget_api_secret: str | None = None
    bitget_api_passphrase: str | None = None
    demo_api_key: str | None = None
    demo_api_secret: str | None = None
    demo_api_passphrase: str | None = None
    database_url: str | None = None
    execution_mode: str = "local_paper"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            qwen_base_url=os.getenv("BITGET_QWEN_BASE_URL", cls.qwen_base_url),
            qwen_model=os.getenv("QWEN_MODEL", cls.qwen_model),
            qwen_api_key=os.getenv("BITGET_QWEN_API_KEY"),
            bitget_api_key=os.getenv("BITGET_API_KEY"),
            bitget_api_secret=os.getenv("BITGET_API_SECRET"),
            bitget_api_passphrase=os.getenv("BITGET_API_PASSPHRASE"),
            demo_api_key=os.getenv("BITGET_DEMO_API_KEY"),
            demo_api_secret=os.getenv("BITGET_DEMO_API_SECRET"),
            demo_api_passphrase=os.getenv("BITGET_DEMO_API_PASSPHRASE"),
            database_url=os.getenv("DATABASE_URL"),
            execution_mode=os.getenv("EXECUTION_MODE", "local_paper"),
        )

