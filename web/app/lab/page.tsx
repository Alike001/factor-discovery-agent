import Link from "next/link";
import { expressionText, pct, readPhase2 } from "../../lib/phase2";
import { readTargetedBatch } from "../../lib/targeted";
import { readSessionTransitionClosure } from "../../lib/session-transition";

export default function LabPage() {
  const data = readPhase2();
  const targeted = readTargetedBatch();
  const transitionClosure = readSessionTransitionClosure();
  const factor = data.factors.at(-1)!;
  const report = factor.metrics_json!;
  const cycle = data.cycles.at(-1)!;
  const counts = data.factors.reduce<Record<string, number>>((out, item) => {
    out[item.lifecycle_state ?? "INCONCLUSIVE"] = (out[item.lifecycle_state ?? "INCONCLUSIVE"] ?? 0) + 1;
    return out;
  }, {});
  return (
    <div className="app-shell">
      <aside className="rail"><Link className="brand" href="/lab">R/</Link><nav><Link className="active" href="/lab">Lab</Link><Link href="/factors">Factors</Link><span>Paper</span><span>Ledger</span><span>System</span></nav></aside>
      <main>
        <header className="system-strip"><span><i className="pulse" /> BITGET REALITY</span><span>8/8 RESEARCH UNIVERSE</span><span>PROTOCOL REVIEW</span><strong>RESEARCH ONLY · NO PAPER POSITIONS</strong></header>
        <section className="hero"><div><p className="eyebrow">AUTONOMOUS RESEARCH CYCLE #{String(cycle.cycle_number).padStart(4, "0")}</p><h1>{factor.name}</h1><p className="thesis">{factor.thesis}</p></div><div className="source-time"><span>LATEST INCLUDED BAR</span><strong>{new Date(report.data_contract.latest_included_timestamp).toISOString()}</strong><small>Trial {factor.trial_number} · {cycle.status}</small></div></section>
        <div className="notice"><strong>{targeted.decision.recommendation} · SEARCH N {targeted.budget.search_n_before}→{targeted.budget.search_n_after}.</strong> The hard token budget stopped Slot C; no paper trading has started.</div>
        <section className="panel compiler-card"><div className="panel-head"><span>RESEARCH COMPILER</span><span>{transitionClosure.closure.recommendation}</span></div><div><p><strong>Recipes compile to deterministic safe ASTs.</strong> Exact 15-minute session-transition anchors now fail closed on missing data and remain research-only.</p><dl><div><dt>Recipe schema</dt><dd>{transitionClosure.closure.recipe_schema_version}</dd></div><div><dt>Compiler</dt><dd>{transitionClosure.closure.compiler_version}</dd></div><div><dt>READY families</dt><dd>{transitionClosure.closure.ready_families.join(" · ")}</dd></div><div><dt>Transition contract</dt><dd>{transitionClosure.closure.contract_version}</dd></div><div><dt>Golden fixtures</dt><dd>{transitionClosure.closure.golden_valid_passed + transitionClosure.closure.golden_invalid_passed}/17 PASS</dd></div><div><dt>Search N</dt><dd>{transitionClosure.closure.search_n_after}</dd></div><div><dt>Qwen calls this phase</dt><dd>{transitionClosure.closure.qwen_http_attempts_phase}</dd></div><div><dt>Still NOT_READY</dt><dd>{transitionClosure.closure.not_ready_families.join(" · ")}</dd></div></dl></div></section>
        <section className="panel targeted-status"><div className="panel-head"><span>TARGETED FDP-V2 BATCH</span><span>{targeted.decision.status}</span></div><div className="slot-grid">{targeted.trials.map((trial) => <div key={trial.slot}><span>SLOT {trial.slot} · {targeted.plan.slots[trial.slot].title}</span><strong>{trial.report?.aggregate ?? trial.state}</strong><p>{trial.proposal?.economic_mechanism ?? "Ex-ante mechanism unavailable: proposal failed structural validation or was not called."}</p><small>COST GATE · {trial.report?.gates.find((gate) => gate.name === "Costs")?.outcome ?? "NOT EVALUATED"}</small></div>)}</div></section>
        <section className="workspace">
          <article className="panel hypothesis"><div className="panel-head"><span>QWEN PROPOSAL</span><span>{factor.canonical_spec_json!.session_filter.join(" · ")}</span></div><code>{expressionText(factor.canonical_spec_json!.signal)}</code><dl className="contract"><div><dt>Universe</dt><dd>{factor.canonical_spec_json!.universe.join(" · ")}</dd></div><div><dt>Protocol</dt><dd>{data.protocol} · {data.protocol_hash.slice(0, 16)}</dd></div><div><dt>Data window</dt><dd>{report.data_contract.start.slice(0, 10)} → {report.data_contract.end.slice(0, 10)}</dd></div><div><dt>IS / OOS boundary</dt><dd>{report.split_timestamp}</dd></div><div><dt>Lifecycle</dt><dd>{factor.lifecycle_state}</dd></div></dl><p className="hash">FACTOR {factor.canonical_identity_hash}</p></article>
          <article className="panel gates"><div className="panel-head"><span>DETERMINISTIC GATES</span><span>{factor.gates.length} CHECKS</span></div>{factor.gates.map((gate) => <div className="gate" key={gate.name}><div><strong>{gate.name}</strong><p>{gate.reason}</p></div><span className={`verdict ${gate.outcome.toLowerCase()}`}>{gate.outcome}</span></div>)}</article>
        </section>
        <section className="panel metrics"><div className="panel-head"><span>HISTORICAL EVIDENCE</span><span>FIXED OOS · COSTED</span></div><div className="metric-grid"><div><span>Gross return</span><strong>{pct(report.metrics.gross.total_return)}</strong><small>before costs</small></div><div><span>Net return</span><strong>{pct(report.metrics.net.total_return)}</strong><small>after costs</small></div><div><span>IS net</span><strong>{pct(report.metrics.is_net.total_return)}</strong><small>fixed earlier window</small></div><div><span>OOS net</span><strong>{pct(report.metrics.oos_net.total_return)}</strong><small>{report.metrics.oos_net.fills} fills</small></div><div><span>Buy & hold</span><strong>{pct(report.metrics.buy_hold)}</strong><small>same window</small></div><div><span>Max drawdown</span><strong>{pct(report.metrics.net.max_drawdown)}</strong><small>net series</small></div></div></section>
        <section className="funnel"><div><strong>{data.factors.length}</strong><span>TRIALS</span></div><div><strong>{counts.REJECTED ?? 0}</strong><span>REJECTED</span></div><div><strong>{counts.INCONCLUSIVE ?? 0}</strong><span>INCONCLUSIVE</span></div><div><strong>{counts.CANDIDATE ?? 0}</strong><span>CANDIDATE</span></div><Link href="/factors">Open Factor Graveyard →</Link></section>
        <details className="search-budget"><summary>Research Search Budget <span>{targeted.decision.committed_trials}/{targeted.plan.planned_unique_trials} targeted trials committed</span></summary><div className="budget-grid"><div><strong>{targeted.budget.search_n_after}</strong><span>Global committed unique trials</span></div><div><strong>{targeted.decision.committed_trials}</strong><span>New committed trials</span></div><div><strong>{targeted.plan.planned_unique_trials}</strong><span>New planned trials</span></div><div><strong>{targeted.budget.search_n_after}</strong><span>Current DSR search N</span></div><div><strong>{targeted.budget.measured_tokens.toLocaleString()}</strong><span>Additional measured Qwen tokens</span></div></div><p>Every committed hypothesis raises the statistical hurdle for the next one.</p></details>
        <footer><span>Generated {new Date(data.generated_at).toISOString()}</span><a href="/evidence/phase2-summary.json">Open raw evidence JSON ↗</a></footer>
      </main>
      <nav className="mobile-nav"><Link className="active" href="/lab">Lab</Link><Link href="/factors">Factors</Link><span>Paper</span><span>Ledger</span><span>System</span></nav>
    </div>
  );
}
