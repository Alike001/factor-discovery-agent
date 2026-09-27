# UX Research and Final Design Direction

Snapshot: 2026-09-27

This file is the UX source of truth for the Factor Discovery product. It is based on direct inspection of Masayume's public repository and current product documentation, plus comparison with QuantConnect's Research Pipeline and Composer's strategy/backtest UI.

The goal is not to copy Masayume's visual identity. The goal is to borrow the product-design principles that make a dense financial system legible, trustworthy, responsive, and demo-friendly.

## 1. UX thesis

This product should feel like a research operating system, not a crypto dashboard and not an AI chat wrapper.

The user should be able to answer these questions within seconds:

1. What is the agent researching right now?
2. What did it propose?
3. What evidence did the experiment produce?
4. Which gate killed or promoted the factor?
5. What is currently being paper-traded?
6. Which exact factor caused each position?
7. Are the data sources and worker healthy?
8. Can I reproduce the decision from the stored evidence?

The product should be visually calm even when it carries a lot of data.

## 2. What Masayume does well

Repository inspected:
https://github.com/Blockchain-Oracle/masayume

Relevant source paths:
- `web/src/app/layout.tsx`
- `web/src/styles/tokens.css`
- `web/src/styles/shell.css`
- `web/src/styles/navigation.css`
- `web/src/styles/markets-hero.css`
- `web/src/styles/status.css`
- `web/src/features/strategies/AgentsScreen.tsx`
- `web/src/features/strategies/StrategyCard.tsx`
- `web/src/features/strategies/desk.css`
- `web/src/styles/yosuku/part-01.css`
- `web/src/lib/theme.ts`

### 2.1 Product opens into the core loop

Masayume's `/` route redirects into the markets experience. It does not force a judge or user through a large marketing homepage before the product.

Adopt:
- `/` redirects to `/lab`.
- Public judges can explore immediately.
- Marketing content belongs in the README, submission, and optional `/about`, not in front of the product.

### 2.2 One visual accent, semantic colors for facts

Masayume uses a near-black ground, one vermilion brand accent, and reserves green/red for financial direction and PnL.

Adopt the rule, not the color:
- one product accent
- green only for genuinely positive/pass states
- rose/red only for negative/fail states
- amber for inconclusive/warning
- gray for missing/offline/not applicable
- never use the brand accent as "success"
- never encode a state by color alone

Brand accent is intentionally left TBD until the product name is selected. The implementation must use semantic CSS variables so the final brand can change in one file.

### 2.3 Dense information with strong hierarchy

Masayume often uses:
- a strong display headline
- small mono metadata
- tabular numbers
- hairline borders
- restrained surfaces
- very little shadow
- one bold number or action per card

Adopt:
- display type for titles and one key metric
- mono type for hashes, timestamps, formulas, model versions, state labels
- body type for explanations
- tabular numerals for all metrics
- avoid giant generic cards full of equally weighted numbers

### 2.4 Honest unavailable states

Masayume has explicit `CapabilityPending` and source-health states instead of rendering realistic-looking fake data.

This is critical for our product.

Every data-bearing component must support:
- LIVE
- CACHED with age
- STALE
- MISSING
- ERROR
- INCONCLUSIVE
- NOT APPLICABLE

Never replace failed live data with a fixture while keeping a "live" label.

### 2.5 Mobile is designed, not squeezed

Masayume uses a mobile drawer and a persistent bottom navigation instead of shrinking desktop navigation.

Adopt:
- mobile bottom tabs: Lab, Factors, Paper, Ledger, System
- no wide research table compressed to phone width
- switch tables to stacked evidence rows
- factor formula tree becomes vertically nested
- charts use one metric at a time
- mobile is an observer/control surface, not a full research authoring environment

### 2.6 Status is a first-class product page

Masayume has an explicit system status screen with source health, warning states, and freshness.

Adopt:
- `/system` is mandatory
- source freshness and worker state are user-facing product features
- Qwen failure, Bitget data failure, stale candles, missing reference bars, and execution mode are visible

### 2.7 Evidence has a visual object

Masayume uses receipts and settlement evidence as visual objects.

Our equivalent is a `Research Proof` object.

Every experiment gets a compact proof panel containing:
- factor version
- lifecycle state
- proposal time
- model + prompt hash
- data snapshot hash
- tested period
- cost model version
- trial number
- gate verdicts
- final lifecycle action
- link to raw JSON

This proof panel should be visually distinct from normal dashboard cards, but should not imitate Masayume's cream receipt styling.

## 3. What QuantConnect adds

Current QuantConnect Research Pipeline:
https://www.quantconnect.com/docs/v2/cloud-platform/research-pipeline

QuantConnect organizes ideas through explicit research stages and retains archived projects that failed research or live deployment.

The useful UX pattern is the lifecycle, not drag-and-drop.

Adopt a read-only automated pipeline:

PROPOSED -> TESTING -> CANDIDATE -> CERTIFIED -> PAPER PROBATION -> ACTIVE

with side exits:

REJECTED
INCONCLUSIVE
DECAYED
RETIRED

The system, not the user, moves cards between lanes.

A judge should be able to see the full research funnel at a glance.

## 4. What Composer adds

Current Composer:
https://www.composer.trade/
https://www.composer.trade/learn/creating-and-editing-algorithmic-trading-strategies-with-composer
https://help.composer.trade/article/67-backtest-basics

Composer makes strategy logic visually readable and puts backtest metrics beside the logic.

Adopt:
- render our safe factor DSL as a human-readable expression tree
- show factor logic and evidence side by side on desktop
- make fees and slippage visible beside performance
- clearly separate hypothetical historical backtest from forward paper behavior

Do not build Composer's manual no-code editor in V1. The agent authors the factor. The user inspects it.

## 5. Information architecture

Primary desktop navigation:

1. Lab
2. Factors
3. Paper
4. Ledger
5. System

Non-primary public route:
- `/proof` - judge evidence pack
- `/demo` - optional guided replay of the latest complete research cycle

No dashboard item called "Home".

### 5.1 Global shell

Desktop:
- left navigation rail, compact
- top system strip
- content canvas
- optional right context rail only where useful

Top system strip:
- `BITGET REALITY`
- current US market phase
- research universe health, e.g. `8/8`
- worker pulse
- last completed research cycle
- next scheduled cycle
- global execution badge: `PAPER · REAL MARKET DATA`

Do not display account wallet controls in V1.

### 5.2 `/lab`

This is the first screen.

Top:
- `Research Cycle #0042`
- state pill: RUNNING / COMPLETE / DEGRADED
- started time and duration
- `Replay latest cycle` for judges

Main desktop grid:
- left 7 columns: Current hypothesis
- right 5 columns: Lifecycle + gate stack

Current hypothesis card:
- plain-English thesis
- target universe
- session
- horizon
- Qwen rationale
- compact factor expression tree
- trial number
- current stage

Gate stack:
- Syntax
- Coverage
- Point-in-time
- Costs
- OOS
- Stability
- Placebo
- Multiple testing
- Promotion

Each gate row shows PASS / FAIL / INCONCLUSIVE plus one concise reason.

Below:
- experiment chart
- IS/OOS split clearly shaded
- net vs gross toggle
- benchmark toggle
- cost assumption line
- latest rejected hypotheses
- latest promoted factor
- research funnel totals

### 5.3 `/factors`

Top:
- funnel counts
- filters
- search

Lifecycle tabs:
- Certified
- Probation
- Active
- Testing
- Graveyard

Each factor card:
- name
- state
- factor hash short form
- one-line expression
- session
- universe
- net OOS Sharpe or `insufficient`
- OOS decay
- cost status
- forward observations
- age
- "Open evidence"

Graveyard is not hidden behind a tiny advanced menu. Rejections are part of the product.

### 5.4 `/factors/[factorId]`

Sections:

1. Thesis
2. Factor expression
3. Data contract
4. Historical evidence
5. Robustness
6. Forward paper evidence
7. Lifecycle history
8. Research proof

Desktop hero:
- factor name + state
- short thesis
- one main status figure, not ten
- the safe DSL tree next to the current gate verdict

Expression tree visual grammar:
- source nodes: rectangular, quiet surface
- transforms: compact outlined chips
- conditions: nested indentation
- session filter: visible tag
- horizon: visible tag
- no draggable editing

Historical evidence:
- equity/return chart
- vertical OOS boundary marker
- metrics table with gross and net columns
- symbol/session breakdown
- rejected baseline comparison

Robustness:
- permutation/placebo
- split-half or block stability
- leave-one-symbol-out
- cost stress
- DSR/trial penalty

Forward:
- paper observations
- realized vs historical expectation
- current status: PROBATION / ACTIVE / DECAYED

### 5.5 `/paper`

Top:
- PAPER mode badge
- real Bitget market data timestamp
- equity
- cash
- gross exposure
- max drawdown
- realized/unrealized PnL

Main:
- equity curve
- current positions

Each position must name:
- symbol
- side, V1 should be LONG or FLAT only
- size
- entry
- mark
- PnL
- factor version
- Qwen decision ID
- next review time

Below:
- latest allocation decisions
- risk vetoes
- factor attribution
- shadow/counterfactual view if implemented

Never use "live trading" for this V1.

### 5.6 `/ledger`

Append-only event stream.

Filters:
- Research
- Model
- Gate
- Data
- Portfolio
- Recovery

Rows:
- timestamp
- event
- factor/cycle
- result
- integrity short hash

Open event drawer:
- full input metadata
- prompt/model hashes
- snapshot hash
- idempotency key
- source timestamps
- machine-readable JSON
- upstream errors if any

The ledger is one of the judge-demo screens, so it must be readable without opening developer tools.

### 5.7 `/system`

Top:
- overall health
- last full preflight
- worker heartbeat

Tables:
- Bitget Reality market
- rToken candles
- underlying US data
- market calendar/session source
- Qwen
- database
- scheduler
- paper engine

Universe coverage matrix:
rows = symbols
columns = price, volume, underlying, session, latest timestamp

Execution mode card:
`LOCAL PAPER ENGINE`
`REAL BITGET MARKET DATA`
`NO REAL CAPITAL`

If rToken Demo is later verified, show it as a separate capability and never silently switch modes.

### 5.8 `/proof`

One judge-oriented page.

Order:
1. 30-second product explanation
2. latest complete autonomous cycle
3. funnel: proposed / rejected / inconclusive / promoted
4. one rejected factor
5. one survivor
6. paper portfolio
7. integrity/restart evidence
8. source health
9. exact links to GitHub, logs, JSON, demo video

This page should be usable as the main submission demo URL if the rest of the product is too deep.

## 6. Interaction design

### 6.1 State changes

Research cycles should stream progress:

SNAPSHOT
-> PROPOSE
-> COMMIT
-> FORMALIZE
-> BACKTEST
-> COST
-> OOS
-> ROBUSTNESS
-> LIFECYCLE
-> PAPER

Use a subtle step pulse and text update. Do not use fake percentage loaders.

### 6.2 Motion

Use motion only for:
- new event arriving
- lifecycle transition
- chart update
- drawer open/close

Respect `prefers-reduced-motion`.

No looping decorative particle systems.

### 6.3 Confirmation

The public product is read-only by default.

Admin-only actions:
- pause research
- resume research
- run one cycle
- reset paper account, development only

Dangerous controls require confirmation and should not be visible to judges unless authenticated.

## 7. Visual system

Do not copy Masayume's vermilion identity.

Implement semantic tokens first:

```css
--bg
--surface-1
--surface-2
--surface-3
--hairline
--ink
--ink-secondary
--ink-muted
--accent
--accent-wash
--positive
--negative
--warning
--offline
```

Dark theme first.

Light theme can ship after the core product if time allows, but the token system must support it.

Typography:
- display: Geist Sans or equivalent clean geometric sans
- body: Geist Sans / Inter
- data: Geist Mono / IBM Plex Mono
- all numbers use tabular numerals

Geometry:
- 10 to 14 px radius for panels
- 1 px hairline borders
- little or no drop shadow
- stronger contrast from spacing and typography rather than glow

Charts:
- no rainbow palettes
- one factor line
- one benchmark line
- OOS region
- drawdown region only when requested
- tooltips include data timestamp
- line style can distinguish series in addition to color

## 8. Copy system

Avoid AI hype.

Good:
- "Qwen proposed this hypothesis."
- "Historical evidence was insufficient."
- "Rejected after costs."
- "Promoted to paper probation."
- "Source is stale. New positions are blocked."

Bad:
- "AI found guaranteed alpha."
- "High-confidence winning strategy."
- "Live trade" when using local paper fills.
- "Verified" when a test is only simulated.

State labels are exact:
- PASS
- FAIL
- INCONCLUSIVE
- STALE
- MISSING
- PAPER
- REAL MARKET DATA

## 9. Responsive rules

Desktop, >= 1024:
- persistent left rail
- max content width 1440
- 12-column grid
- side-by-side factor logic/evidence

Tablet:
- rail collapses
- top nav + drawer
- charts full width

Phone:
- bottom nav
- one column
- key metric first
- cards become evidence rows
- factor tree stacks vertically
- no horizontal metrics table
- no hover-only information

## 10. Accessibility

Required:
- keyboard navigation
- visible focus ring
- ARIA labels for status icons
- status never depends only on color
- contrast target WCAG AA
- reduced motion
- chart data also available as a table
- button targets >= 44px on touch
- no tiny 8px body copy even if metadata is compact

## 11. UX acceptance tests

Before demo:
- a first-time tester can explain the product after 30 seconds
- tester can identify why a rejected factor failed without opening raw JSON
- tester can identify which factor caused a paper position
- tester can distinguish historical backtest from forward paper results
- tester can find source freshness in <= 2 clicks
- tester can find raw evidence for a decision in <= 2 clicks
- phone layout has no horizontal page scroll
- stale data visibly blocks new positions
- all unknown/loading/error states are distinct
- public demo requires no login

## 12. Research sources

Masayume:
https://github.com/Blockchain-Oracle/masayume

Masayume docs:
https://docs.masayume.app

QuantConnect Research Pipeline:
https://www.quantconnect.com/docs/v2/cloud-platform/research-pipeline

QuantConnect:
https://www.quantconnect.com/

Composer:
https://www.composer.trade/

Composer backtest basics:
https://help.composer.trade/article/67-backtest-basics

Composer strategy editing:
https://www.composer.trade/learn/creating-and-editing-algorithmic-trading-strategies-with-composer
