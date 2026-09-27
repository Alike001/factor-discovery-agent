# Hostile Feasibility Pass — Factor Discovery

Snapshot: 2026-09-27.

Goal: try to reject the Factor Discovery direction before writing a final product spec.

## Verdict

The broad idea "AI proposes factors, backtests them, then trades the winners" DOES NOT survive unchanged.

The Factor Discovery sub-theme itself still survives, but only as a narrower Bitget-native product:
an autonomous session-aware rToken researcher that discovers, falsifies, promotes, forward-paper-trades, and retires factors specifically around the 24/7 tokenized-equity market structure.

The final product must differentiate from:
- Bitget GetAgent Playbook, which already authors/backtests/deploys user-specified strategies
- Bitget native trend-following and Smart Portfolio bots
- Alpha Factory rToken factor strategies
- ARGUS's sophisticated, though not Track-2-submitted, factor laboratory
- generic RD-Agent / Qlib / FactorMiner-style factor factories

## Kill Test 1 — Is there enough Bitget-native market surface?

PASS, with scope constraints.

Official Bitget facts:
- rTokens are Reality spot pairs with the `r` prefix.
- Bitget says rTokens cover 500+ US stocks/ETFs.
- Bitget announced 93 stock tokens with 24/7 trading as of 2026-08-14.
- UTA announced 125 stock tokens eligible in the cross-asset margin pool.
- Reality exposes instruments, tickers, candles, stock reference data, and order placement.

Conclusion:
There is enough universe for a real product, but the MVP should intentionally restrict itself to a quality-controlled core universe, not claim equal research quality across 500+ assets.

Provisional quality universe:
rNVDA, rAAPL, rTSLA, rMSFT, rAMZN, rMETA, rAMD, rCOIN, rHOOD, rQQQ, rSPY, optionally rMSTR.

The universe should be generated from actual current `isReality=yes` instruments at runtime and intersected with our quality/data rules.

## Kill Test 2 — Is the historical data deep and clean enough?

PARTIAL PASS. This is the first serious weakness.

Official constraints:
- rTokens launched in June 2026, so rToken-specific history is intrinsically short.
- rToken candles support 1m, 5m, 15m, 1H, 4H, 1D.
- candle history can be paged farther than 90 days ago, but each request range is capped.
- before 2026-07-09, volume/turnover may be empty.
- some Reality depth/fills surfaces require whitelist access.

Observed competitor lessons:
- SEAL collected real 15m rToken data from June onward and found some bars thin.
- Gloaming found that mismatched time windows created fake multi-percent spreads. Once corrected, real overnight dislocations were often only tenths of a percent.
- Gloaming also caught a stale/missing Friday stock bar causing nine false weekend paper fills.
- ARGUS measured 13 rTokens over 90 days and found naive market/index basis much less monetizable after costs than early assumptions implied.

Implication:
Do NOT build a huge unconstrained factor factory or claim robust decades-style quantitative evidence.

The product must focus on:
- session structure
- cross-sectional relationships across multiple rTokens
- price-based factors available from launch
- volume factors only from honest post-July-9 data
- point-in-time-safe underlying-stock/crypto references
- forward paper evidence
- explicit uncertainty caused by short history

The short history becomes part of the product thesis: the system is designed to reject weak evidence, not mine until something looks profitable.

## Kill Test 3 — Can we honestly use Bitget Demo for rToken spot execution?

FAIL for direct rToken Demo, based on public builder measurements.

Official Demo docs explain Demo API keys and `paptrading: 1`, but do not specifically guarantee Reality spot coverage.

Multiple public S2 builders measured:
- Gloaming: RAAPLUSDT was not listed in Agent Hub paper/demo environment, while BTCUSDT worked far enough to hit normal order validation.
- WardenClaw: their tested Demo environment was futures-only; spot calls returned environment mismatch, so xStock/rToken fills remained local paper fills.
- Tare: even for supported futures, measured demo execution sometimes diverged materially from the public market and did not list all target symbols.

Conclusion:
The hackathon product must not claim rToken exchange-demo fills unless we personally verify them on our account.

Default architecture:
real Bitget rToken market data
-> autonomous AI decision
-> deterministic paper execution model
-> persistent local/cloud paper ledger
-> mark to real Bitget prices
-> explicit label `PAPER / REAL MARKET DATA`

Secondary integration:
- Agent Hub used for market/account/discovery surfaces and dry-run paths where supported.
- We may add a mapped Bitget stock-perp Demo proof as a secondary adapter, but should not pretend that is an rToken fill.

Future production path:
real rToken Agentic Account execution after controlled live validation.

## Kill Test 4 — Does Playbook already make our product redundant?

The generic version is redundant.

GetAgent Playbook already lets an AI coding agent:
- author Python strategies
- validate packages
- upload to GetAgent Cloud
- run managed backtests
- publish accepted versions
- open subscriptions

Bitget has expanded Playbook to tokenized US equities and automated order placement. Bitget also has stock-selection Playbooks using LLM research.

Competitor evidence:
- SEAL found Playbook's displayed metrics insufficient by themselves for hackathon-grade IS/OOS/Sortino/turnover evidence.
- rToken Breakout Lab used GetAgent Studio, but its Studio historical data did not supply the R-prefixed spot history it needed, so it used corresponding stock-perpetual legs for the cloud backtest and a separate local rToken engine.

Therefore:
"Tell AI a strategy, backtest it, deploy it" is not a product opportunity. Bitget already does that.

Our surviving differentiation:
The agent originates the research agenda itself, keeps a factor research memory, falsifies hypotheses, counts every trial, refuses promotion when evidence is weak, builds a portfolio only from survivors, and retires factors on forward decay.

Playbook can become an export/deployment target later, not the research brain.

## Kill Test 5 — Is Factor Discovery actually uncrowded?

PARTIAL PASS, with an important competitor.

Exact public S2 searches did not surface a clearly dedicated submitted Factor Discovery Agent product comparable to the full proposed loop.

But ARGUS raises the technical bar sharply.

ARGUS contains a serious factor lab:
- immutable lifecycle
- deterministic evaluation
- trial counter
- Deflated Sharpe
- anti-overfit gates
- split-half reproducibility
- factor cemetery
- factor memory deliberately blinded from outcome scores
- decay/retire states

Critical distinction:
ARGUS's own source currently calls its factor inputs "stand-ins for model proposals: every vetted primitive, submitted blind." Its public docs say the factor/Alpha machinery is not its Track 2 submission; its separate Track 2 entry is t2-sentiment-agent.

So ARGUS is prior art and a benchmark, but not proof that the named Factor Discovery prize is already occupied by that exact product.

Our product cannot merely recreate ARGUS's factor lab.

We need to surpass it on the actual Track 2 loop:
Qwen-originated research
-> formal factor DSL
-> deterministic falsification
-> promotion
-> forward paper portfolio
-> factor decay/retirement
-> autonomous next research cycle.

## Kill Test 6 — Are easy rToken alphas real enough?

FAIL for naive assumptions.

Do not base the product on:
- "weekend rTokens drift far from fair value"
- "the underlying stock freezes, so rToken reference price is stale"
- "simple momentum/RSI should work because trading is 24/7"
- "more factor search will inevitably find profitable alpha"

Public projects have already falsified versions of these assumptions.

The product must be hypothesis-agnostic:
its success is not finding a guaranteed factor.
Its success is running a credible scientific process that can say "nothing passed."

A factor cemetery full of rejected ideas is a feature if the method is real.

## Kill Test 7 — Does Bitget itself already solve simple automation?

YES.

Bitget already offers:
- Smart Portfolio for rTokens and crypto
- 24/7 automatic portfolio trading/rebalancing
- spot trend-following bots for rTokens using MA/Bollinger/RSI
- GetAgent Playbooks
- Agent Hub

Therefore our product cannot center on:
- rebalancing
- moving-average/RSI strategy generation
- "AI trades while you sleep"
- one-click automation
- generic strategy deployment

## Surviving product territory

Working research shape:

"An AI quant researcher for Bitget rTokens. It looks for trading rules whose behavior changes across the 24/7 tokenized-stock session, tests every hypothesis on unseen data and after costs, rejects weak ideas, paper-trades only certified factors, then retires them when forward evidence decays."

This is narrower than a generic factor factory.

Core distinction:
- Bitget-native market structure is the research subject.
- AI owns hypothesis generation and lifecycle decisions.
- deterministic code owns measurement and vetoes.
- forward paper evidence matters as much as historical fit.
- rejection and inactivity are first-class outputs.

## Strong product loop

1. Observe
   - scan the approved rToken universe
   - identify session/regime anomalies without looking at future outcomes

2. Hypothesize
   - Qwen proposes one bounded factor expression + economic rationale
   - exact research input and prompt are hashed
   - proposal is committed before evaluation

3. Formalize
   - parse into a safe DSL
   - no arbitrary model-authored Python
   - point-in-time fields only

4. Falsify
   - fees/costs
   - IS/OOS
   - walk-forward where possible
   - multiple-testing/trial penalty
   - split/session stability
   - simple baselines
   - missing-data and leakage checks

5. Decide
   - Qwen sees the experiment report and chooses revise/reject/promote
   - deterministic promotion minimum still cannot be bypassed

6. Paper Deploy
   - certified factor enters a bounded paper portfolio
   - fills marked to real Bitget prices
   - all decisions logged
   - no fake rToken Demo claim

7. Monitor
   - forward IC/return/drawdown/turnover
   - compare research expectation vs forward behavior

8. Retire/Evolve
   - factor loses certification after explicit decay rules
   - Qwen proposes a replacement or revision
   - old factor remains in cemetery, never deleted from evidence

## What must be measured to make this competitive

Research-process metrics:
- hypotheses proposed
- duplicates suppressed
- factors rejected at each gate
- certification rate
- trials counted for multiple-testing penalty
- time from hypothesis to verdict

Historical factor metrics:
- gross/net return
- Sharpe/Sortino
- max drawdown
- turnover
- OOS decay
- cross-symbol/session stability
- cost stress
- simple baseline comparison

Forward paper metrics:
- timestamped decisions
- active factor/version
- symbol/side/target
- entry/mark/exit
- account equity
- drawdown
- factor attribution
- accepted vs rejected trade counterfactuals

Reliability metrics:
- stale-source holds
- execution duplicates prevented
- restart recoveries
- unresolved execution attempts
- model failures/refusals
- data coverage

## Post-hackathon product path

V1 — autonomous rToken research + paper portfolio
V2 — user-defined research mandates
V3 — export validated factors into GetAgent Playbook / controlled Agentic Account deployment
V4 — private factor libraries for teams
V5 — publish/follow validated strategies with bounded capital
V6 — multi-venue tokenized-equity research

The business/product is the continuously running research system and its evidence library, not a single discovered strategy.

## Final decision gate

Proceed to final product specification only if we accept these constraints:
- no claim of rToken Demo execution until personally verified
- own paper engine with real Bitget marks is acceptable and clearly labeled
- research universe is small/quality-controlled
- no use of current-only fundamental snapshots in historical backtests
- Qwen is truly load-bearing in hypothesis and lifecycle decisions
- safe DSL, no arbitrary AI-authored execution code
- failures/rejected factors remain visible
- forward paper logger starts as soon as the first certified candidate can trade
- product pitch remains understandable in 30 seconds

If any of those are unacceptable, reject Factor Discovery and return to Cross-Asset research.
