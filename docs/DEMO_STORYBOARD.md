# Demo storyboard — 2:50

## 0:00–0:20 — Proof

Open `/proof`. Say: rTokens trade across extended sessions, while their trusted public history is short. That makes plausible-looking backtests easy to overfit. The product lets Qwen propose ideas but makes deterministic evidence—not model confidence—the capital gate.

## 0:20–0:45 — Trial 8 recipe

Open Trial 8. Show the bounded FactorRecipe, its hash, and the executable hypothesis. Point out the visible rationale/recipe mismatch: model prose says mean reversion, while the structured recipe says positive continuation. The recipe wins; the inconsistency remains evidence.

## 0:45–1:10 — Compiler boundary

Show recipe → `factor-recipe-compiler-v2` → safe expression. Qwen supplies no raw code and no raw AST. The same recipe produces the same canonical JSON and AST hash.

## 1:10–1:40 — Falsification

Show Trial 8 gates: Stability FAIL, DSR probability 0.6296 versus 0.90 required, permutation p=0.2029 FAIL, baseline FAIL, and zero OOS fills. Never describe Trial 8 as successful alpha.

## 1:40–2:00 — Capital gate

Open `/paper`. Show zero eligible factors, zero USDT, zero positions, zero orders, and zero fills. Explain that an empty portfolio is the correct output when nothing survives.

## 2:00–2:20 — Trial 9 budget refusal

Return to Proof or Trial 9. The initial proposal was invalid. A conservative reservation projected that repair would exceed the fixed phase budget, so the system refused before HTTP. No replacement or third slot was created.

## 2:20–2:40 — Ledger

Open `/ledger`. Show 190 verified events, the chain head, filters, and one expandable payload. Explain commit-before-evaluation and append-only history.

## 2:40–2:50 — Close

Return to Proof and close with:

> Qwen can have a bad idea. The system cannot turn bad evidence into a trade.
