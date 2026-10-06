import type { Metadata } from "next";
import Link from "next/link";
import { chainSummary, summary, trials } from "../lib/evidence";

export const metadata: Metadata = {
  title: { absolute: "Factor Discovery Agent — Evidence-Gated rToken Research" },
};

const process = [
  ["01", "Qwen hypothesis", "A bounded economic thesis for an allowed research family."],
  ["02", "FactorRecipe", "Structured fields become the authoritative experiment contract."],
  ["03", "Deterministic compiler", "Local code compiles the recipe; Qwen emits no executable raw AST."],
  ["04", "Frozen evidence gates", "Costs, OOS, stability, placebo and search penalties try to falsify it."],
  ["05", "Capital gate", "Only eligible evidence can unlock paper probation."],
] as const;

export default function Home() {
  const research = summary();
  const chain = chainSummary();
  const [trial8, trial9] = trials();
  const dsr = Number(trial8.dsr?.probability ?? 0).toFixed(4);
  const dsrThreshold = Number(trial8.dsr?.threshold ?? 0).toFixed(2);
  const permutation = String(trial8.permutation?.reason ?? "").match(/p=([0-9.]+)/)?.[1] ?? "unavailable";
  const oosFills = Number(trial8.metrics?.oos_net?.fills ?? 0);
  const trial9BudgetReason = String((trial9.qwen_metadata?.calls as Array<Record<string, unknown>> | undefined)?.find(call => call.attempt === 2)?.reason ?? trial9.gates[0]?.reason);

  return <div className="landing-page">
    <a className="skip-link" href="#landing-content">Skip to content</a>
    <header className="landing-header">
      <Link className="landing-brand" href="/" aria-label="Factor Discovery Agent home">
        <span className="brand-mark" aria-hidden="true">F/</span>
        <span>Factor Discovery Agent</span>
      </Link>
      <nav className="landing-nav" aria-label="Landing page navigation">
        <a href="#product">Product</a>
        <Link href="/proof">Proof</Link>
        <Link href="/factors">Factors</Link>
        <Link href="/ledger">Ledger</Link>
      </nav>
      <Link className="nav-cta" href="/lab">Open Lab <span aria-hidden="true">↗</span></Link>
    </header>

    <main id="landing-content" className="landing-main">
      <section className="landing-hero" aria-labelledby="landing-title">
        <div className="landing-hero-copy">
          <p className="landing-eyebrow"><span /> BITGET rTOKEN · AGENTIC FACTOR RESEARCH</p>
          <h1 id="landing-title">AI proposes the trade. <em>Evidence decides</em> if capital is allowed.</h1>
          <p className="landing-intro">Qwen proposes bounded hypotheses for 24/7 tokenized U.S. stocks. A deterministic compiler, backtester and evidence gate try to falsify each idea before it can reach capital.</p>
          <div className="landing-actions">
            <Link className="button-primary" href="/lab">Enter Research Lab <span aria-hidden="true">↗</span></Link>
            <Link className="button-secondary" href="/proof">View Research Proof</Link>
          </div>
          <Link className="tertiary-link" href="/replay?trial=8">Replay Trial 8 <span aria-hidden="true">→</span></Link>
        </div>

        <aside className="capital-gate" aria-label="Current capital gate status">
          <div className="gate-topline"><span>CAPITAL GATE · FINAL STATE</span><strong>CLOSED</strong></div>
          <div className="gate-orbit" aria-hidden="true"><span className="orbit-core">0</span><i /><i /><i /></div>
          <div className="gate-equation"><span>{research.paper_eligible} eligible factors</span><b>→</b><span>{research.paper.capital_usdt} capital allocated</span></div>
          <p>No hypothesis passed every frozen gate. Capital stayed out of the market.</p>
          <div className="gate-footer"><span>PROTOCOL {research.protocol}</span><span>RESEARCH CLOSED</span></div>
        </aside>
      </section>

      <section className="truth-band" aria-label="Committed research facts">
        <div><strong>{research.trials}</strong><span>COMMITTED TRIALS</span></div>
        <div><strong>{research.candidates}</strong><span>CANDIDATES</span></div>
        <div><strong>{research.paper.fills}</strong><span>PAPER TRADES</span></div>
        <div><strong>{chain.event_count}</strong><span>LEDGER EVENTS</span></div>
        <div className="chain-metric"><strong><i /> CHAIN VERIFIED</strong><span>{chain.head_hash.slice(0, 12)}…</span></div>
      </section>
      <div className="trust-line" aria-label="Research stack"><span>QWEN 3.8 MAX</span><span>REAL BITGET MARKET DATA</span><span>{research.protocol}</span><time>{new Date(research.latest_verified_source_timestamp).toISOString()}</time></div>

      <section className="landing-section process-section" id="product" aria-labelledby="process-title">
        <div className="section-kicker"><span>01</span><p>HOW THE SYSTEM WORKS</p></div>
        <div className="section-heading"><h2 id="process-title">An AI researcher<br />with no authority to trade.</h2><p>Qwen forms the hypothesis. Deterministic code owns execution semantics, measurement, rejection and the final capital decision.</p></div>
        <ol className="process-rail">
          {process.map(([number, title, description]) => <li key={number}><span>{number}</span><div><h3>{title}</h3><p>{description}</p></div></li>)}
        </ol>
      </section>

      <section className="landing-section zero-section" aria-labelledby="zero-title">
        <div className="zero-statement"><p className="landing-eyebrow">CAPITAL DISCIPLINE</p><h2 id="zero-title">Zero trades is an outcome,<br /><em>not a missing feature.</em></h2><p>No factor passed the frozen evidence standard, so the capital gate remained closed. The app does not manufacture a paper portfolio to make the dashboard look active.</p><Link className="button-secondary" href="/paper">Inspect the locked Paper engine <span aria-hidden="true">→</span></Link></div>
        <div className="zero-proof" aria-label="Capital allocation result"><div><span>ELIGIBLE FACTORS</span><strong>{research.paper_eligible}</strong></div><b aria-hidden="true">→</b><div><span>CAPITAL ALLOCATED</span><strong>{research.paper.capital_usdt} <small>USDT</small></strong></div><p>Positions {research.paper.positions} · Orders {research.paper.orders} · Fills {research.paper.fills}</p></div>
      </section>

      <section className="landing-section proof-moments" aria-labelledby="proof-title">
        <div className="section-kicker"><span>02</span><p>TWO PROOF MOMENTS</p></div>
        <div className="section-heading compact-heading"><h2 id="proof-title">Rejection is visible.<br />Constraints are enforceable.</h2><p>Two stored trials show both sides of the control system: an executable idea that failed its evidence gates, and an invalid proposal that could not spend beyond its budget.</p></div>
        <div className="proof-moment-grid">
          <article className="trial-proof trial-proof-primary">
            <header><div><span>TRIAL 08 · {trial8.family}</span><p>RAMD / RQQQ</p></div><strong>{trial8.outcome}</strong></header>
            <h3>Evidence rejected an executable hypothesis.</h3>
            <dl><div><dt>FIRST HARD FAIL</dt><dd>{trial8.first_hard_fail}</dd></div><div><dt>DSR</dt><dd>{dsr} <small>vs {dsrThreshold} required</small></dd></div><div><dt>PERMUTATION</dt><dd>p = {permutation}</dd></div><div><dt>OOS</dt><dd>{oosFills} fills</dd></div></dl>
            <Link href="/factors/trial-8">Inspect Trial 8 <span aria-hidden="true">→</span></Link>
          </article>
          <article className="trial-proof">
            <header><div><span>TRIAL 09 · {trial9.family}</span><p>STRUCTURAL PROPOSAL FAILURE</p></div><strong>{trial9.outcome}</strong></header>
            <h3>The budget stopped repair before another HTTP call.</h3>
            <p>No valid recipe compiled. The projected hard-budget breach blocked the only permitted repair, so no executable hypothesis or performance evidence was fabricated.</p>
            <code>{trial9BudgetReason}</code>
            <Link href="/factors/trial-9">Inspect budget evidence <span aria-hidden="true">→</span></Link>
          </article>
        </div>
      </section>

      <section className="landing-section fit-integrity" aria-label="Bitget fit and evidence integrity">
        <article className="fit-copy"><div className="section-kicker"><span>03</span><p>BITGET FIT</p></div><h2>Built for 24/7<br />rToken research.</h2><p>The research problem is specific to short-history, continuously tradable tokenized equities where session effects and repeated backtesting can create false confidence.</p><ul><li>Bitget Reality / rToken market data</li><li>Tokenized U.S. stock session structure</li><li>Qwen 3.8 Max hypothesis and lifecycle reasoning</li><li>Deterministic local research and evidence pipeline</li></ul></article>
        <article className="integrity-panel"><p className="landing-eyebrow">EVIDENCE INTEGRITY</p><h3>Every idea leaves a trace.</h3><ul><li><span>01</span><div><strong>Committed before evaluation</strong><p>The proposal exists before outcome data can influence its identity.</p></div></li><li><span>02</span><div><strong>Multiple-testing search N preserved</strong><p>Every committed hypothesis raises the statistical hurdle. Current N: {research.global_search_n}.</p></div></li><li><span>03</span><div><strong>Append-only evidence chain</strong><p>{chain.event_count} events resolve to one verified head hash.</p></div></li><li><span>04</span><div><strong>Hard pre-call Qwen budget</strong><p>Projected exhaustion stops the request before HTTP.</p></div></li><li><span>05</span><div><strong>No raw model reasoning persisted</strong><p>Judge-safe evidence exposes decisions, hashes and outcomes.</p></div></li></ul><Link href="/ledger">Open Ledger <span aria-hidden="true">→</span></Link></article>
      </section>

      <section className="landing-close" aria-labelledby="close-title"><p>THE CAPITAL GATE IS THE PRODUCT</p><h2 id="close-title">The AI is allowed to have bad ideas.<br /><em>It is not allowed to turn bad evidence into a trade.</em></h2><div><Link className="button-primary" href="/lab">Open Research Lab <span aria-hidden="true">↗</span></Link><Link className="button-secondary" href="/proof">See the complete proof</Link></div></section>
    </main>

    <footer className="landing-footer"><div><span className="brand-mark">F/</span><div><strong>Factor Discovery Agent</strong><p>Built for Bitget AI Genesis S2</p></div></div><p>Research-only · No capital allocated</p><nav aria-label="Footer"><Link href="/proof">Proof</Link><Link href="/run-records">Run records</Link><Link href="/system">System</Link></nav></footer>
  </div>;
}
