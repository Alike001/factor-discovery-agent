from __future__ import annotations

import math
from dataclasses import dataclass
from uuid import UUID

import psycopg


class ProjectedBudgetExhausted(RuntimeError):
    code = "NO_RUN_PROJECTED_BUDGET_EXHAUSTED"


def estimated_input_tokens(prompt: str, safety_factor: float = 1.25) -> int:
    return math.ceil(len(prompt) / 4 * safety_factor)


def conservative_reservation(prompt: str, max_completion_tokens: int) -> tuple[int, int]:
    estimate = estimated_input_tokens(prompt)
    conservative_input = max(estimate, len(prompt.encode("utf-8")))
    return estimate, conservative_input + max_completion_tokens


@dataclass(frozen=True)
class Reservation:
    id: UUID
    call_key: str
    estimated_input_tokens: int
    reserved_tokens: int


class PostgresTokenBudget:
    def __init__(self, database_url: str, scope: str, hard_limit: int):
        self.database_url = database_url
        self.scope = scope
        self.hard_limit = hard_limit

    def reserve(self, call_key: str, prompt: str, max_completion_tokens: int) -> Reservation:
        estimate, reserved = conservative_reservation(prompt, max_completion_tokens)
        with psycopg.connect(self.database_url) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (0x42554447,))
            connection.execute(
                """INSERT INTO qwen_budget_accounts(scope,hard_limit_tokens)
                   VALUES (%s,%s) ON CONFLICT(scope) DO NOTHING""", (self.scope, self.hard_limit)
            )
            account = connection.execute(
                "SELECT hard_limit_tokens,charged_tokens FROM qwen_budget_accounts WHERE scope=%s FOR UPDATE",
                (self.scope,),
            ).fetchone()
            if account[0] != self.hard_limit:
                raise ValueError("immutable hard limit mismatch")
            active = connection.execute(
                "SELECT COALESCE(sum(reserved_tokens),0) FROM qwen_token_reservations WHERE scope=%s AND status='RESERVED'",
                (self.scope,),
            ).fetchone()[0]
            if account[1] + active + reserved > self.hard_limit:
                raise ProjectedBudgetExhausted(ProjectedBudgetExhausted.code)
            row = connection.execute(
                """INSERT INTO qwen_token_reservations
                   (scope,call_key,estimated_input_tokens,max_completion_tokens,reserved_tokens,status)
                   VALUES (%s,%s,%s,%s,%s,'RESERVED') RETURNING id""",
                (self.scope, call_key, estimate, max_completion_tokens, reserved),
            ).fetchone()
        return Reservation(row[0], call_key, estimate, reserved)

    def settle(self, reservation: Reservation, actual_tokens: int | None) -> int:
        with psycopg.connect(self.database_url) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (0x42554447,))
            row = connection.execute(
                "SELECT reserved_tokens,status FROM qwen_token_reservations WHERE id=%s FOR UPDATE",
                (reservation.id,),
            ).fetchone()
            if not row or row[1] != "RESERVED":
                raise ValueError("reservation is not active")
            charge = row[0] if actual_tokens is None else actual_tokens
            if charge > row[0]:
                raise ValueError("actual usage exceeded conservative reservation")
            account = connection.execute(
                "SELECT charged_tokens,hard_limit_tokens FROM qwen_budget_accounts WHERE scope=%s FOR UPDATE",
                (self.scope,),
            ).fetchone()
            if account[0] + charge > account[1]:
                raise ValueError("settlement would exceed hard limit")
            connection.execute(
                "UPDATE qwen_budget_accounts SET charged_tokens=charged_tokens+%s WHERE scope=%s",
                (charge, self.scope),
            )
            connection.execute(
                """UPDATE qwen_token_reservations SET actual_tokens=%s,charged_tokens=%s,
                   status='SETTLED',settled_at=now() WHERE id=%s""",
                (actual_tokens, charge, reservation.id),
            )
        return charge

    def usage(self) -> dict[str, int]:
        with psycopg.connect(self.database_url) as connection:
            account = connection.execute(
                "SELECT charged_tokens,hard_limit_tokens FROM qwen_budget_accounts WHERE scope=%s", (self.scope,)
            ).fetchone()
            active = connection.execute(
                "SELECT COALESCE(sum(reserved_tokens),0) FROM qwen_token_reservations WHERE scope=%s AND status='RESERVED'",
                (self.scope,),
            ).fetchone()[0]
        return {"charged_tokens": int(account[0]), "outstanding_reservations": int(active), "hard_limit": int(account[1])}
