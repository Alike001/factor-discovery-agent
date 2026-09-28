from __future__ import annotations

from typing import Any


def capability_matrix() -> list[dict[str, Any]]:
    def row(name: str, status: str, reason: str, *, prompted: bool = False, schema: bool = True,
            compileable: bool = True, evaluatable: bool = True, data: bool = True, ui: bool = True) -> dict[str, Any]:
        return {"capability": name, "status": status, "PROMPTED": prompted, "SCHEMA_VALID": schema,
                "COMPILABLE": compileable, "EVALUATABLE": evaluatable, "DATA_AVAILABLE": data,
                "UI_RENDERABLE": ui, "reason": reason}

    return [
        row("source", "READY_INTERNAL", "Compiler emits validated closed-OHLC source nodes; Qwen never emits nodes."),
        row("ret", "READY_INTERNAL", "Compiler emits close-return nodes and evaluator supports them."),
        row("sma", "READY_INTERNAL", "Safe AST and evaluator support it; no READY recipe currently requires it."),
        row("zscore", "READY_INTERNAL", "beta_residual compiler emits it deterministically."),
        row("rank", "NOT_READY", "No cross-sectional selection/portfolio evaluator.", schema=True, compileable=False, evaluatable=False),
        row("group_mean", "NOT_READY", "Scalar helper exists but basket semantics and attribution do not.", compileable=False, evaluatable=False),
        row("rolling_beta", "READY_INTERNAL", "Rolling beta is deterministically embedded by residual evaluation."),
        row("residual", "READY", "Full recipe/compiler/evaluator/data/UI path passes golden fixtures.", prompted=True),
        row("spread_bps", "NOT_READY", "No point-in-time reference-price adapter or evaluator node.", schema=False, compileable=False, evaluatable=False, data=False, ui=False),
        row("abs", "READY_INTERNAL", "Safe AST and evaluator support it; hidden from recipe menu."),
        row("sign", "READY_INTERNAL", "Safe AST and evaluator support it; hidden from recipe menu."),
        row("clip", "READY_INTERNAL", "Safe AST and evaluator support it; hidden from recipe menu."),
        row("add/sub/mul/div", "READY_INTERNAL", "Safe arithmetic exists but Qwen cannot compose raw nodes."),
        row("session_filter", "READY", "Single America/New_York session contract compiles and evaluates.", prompted=True),
        row("session_transition", "READY", "Frozen 15m exact-anchor contract, deterministic compiler, fail-closed evaluator, data path, and UI evidence pass.", prompted=True),
        row("multi_symbol_references", "READY_LIMITED", "Target plus one reference is supported for beta residual; generic graphs are hidden.", prompted=True),
        row("universe_basket", "NOT_READY", "No cross-sectional holdings, attribution, or leave-one-out implementation.", compileable=False, evaluatable=False),
        row("dispersion", "NOT_READY", "Scalar dispersion does not provide executable basket semantics.", compileable=False, evaluatable=False),
    ]
