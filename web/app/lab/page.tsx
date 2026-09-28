import Link from "next/link";
import { expressionText, pct, readPhase2 } from "../../lib/phase2";
import { readPhase3 } from "../../lib/phase3";

export default function LabPage() {
  const data = readPhase2();
  const hardened = readPhase3();
  const factor = data.factors.at(-1)!;
  const report = factor.metrics_json!;
  const cycle = data.cycles.at(-1)!;
  const diagnostic = hardened.factors.find((item) => item.trial_number === factor.trial_number)!;
  const counts = data.factors.reduce<Record<string, number>>((out, item) => {
    out[item.lifecycle_state ?? "INCONCLUSIVE"] = (out[item.lifecycle_state ?? "INCONCLUSIVE"] ?? 0) + 1;
    return out;
  }, {});
  return (
    <div className="app-shell">
      <aside className="rail"><Link className="brand" href="/lab">R/</Link><nav><Link className="active" href="/lab">Lab</Link><Link href="/factors">Factors</Link><span>Paper</span><span>Ledger</span><span>System</span></nav></aside>
      <main>
        <header className="system-strip"><span><i className="pulse" /> BITGET REALITY</span><span>8/8 RESEARCH UNIVERSE</span><span>PHASE 2 · COMPLETE</span><strong>RESEARCH ONLY · REAL MARKET DATA</strong></header>
        <section className="hero"><div><p className="eyebrow">AUTONOMOUS RESEARCH CYCLE #{String(cycle.cycle_number).padStart(4, "0")}</p><h1>{factor.name}</h1><p className="thesis">{factor.thesis}</p></div><div className="source-time"><span>LATEST INCLUDED BAR</span><strong>{new Date(report.data_contract.latest_included_timestamp).toISOString()}</strong><small>Trial {factor.trial_number} · {cycle.status}</small></div></section>
        <div className="notice"><strong>{report.aggregate} · FIRST HARD FAIL: {diagnostic.first_hard_fail}.</strong> Phase 3 completed DSR and scope-aware stability diagnostics. No paper trading has started.</div>
        <section className="workspace">
          <article className="panel hypothesis"><div className="panel-head"><span>QWEN PROPOSAL</span><span>{factor.canonical_spec_json!.session_filter.join(" · ")}</span></div><code>{expressionText(factor.canonical_spec_json!.signal)}</code><dl className="contract"><div><dt>Universe</dt><dd>{factor.canonical_spec_json!.universe.join(" · ")}</dd></div><div><dt>Protocol</dt><dd>{data.protocol} · {data.protocol_hash.slice(0, 16)}</dd></div><div><dt>Data window</dt><dd>{report.data_contract.start.slice(0, 10)} → {report.data_contract.end.slice(0, 10)}</dd></div><div><dt>IS / OOS boundary</dt><dd>{report.split_timestamp}</dd></div><div><dt>Lifecycle</dt><dd>{factor.lifecycle_state}</dd></div></dl><p className="hash">FACTOR {factor.canonical_identity_hash}</p></article>
          <article className="panel gates"><div className="panel-head"><span>DETERMINISTIC GATES</span><span>{factor.gates.length} CHECKS</span></div>{factor.gates.map((gate) => <div className="gate" key={gate.name}><div><strong>{gate.name}</strong><p>{gate.reason}</p></div><span className={`verdict ${gate.outcome.toLowerCase()}`}>{gate.outcome}</span></div>)}</article>
        </section>
        <section className="panel metrics"><div className="panel-head"><span>HISTORICAL EVIDENCE</span><span>FIXED OOS · COSTED</span></div><div className="metric-grid"><div><span>Gross return</span><strong>{pct(report.metrics.gross.total_return)}</strong><small>before costs</small></div><div><span>Net return</span><strong>{pct(report.metrics.net.total_return)}</strong><small>after costs</small></div><div><span>IS net</span><strong>{pct(report.metrics.is_net.total_return)}</strong><small>fixed earlier window</small></div><div><span>OOS net</span><strong>{pct(report.metrics.oos_net.total_return)}</strong><small>{report.metrics.oos_net.fills} fills</small></div><div><span>Buy & hold</span><strong>{pct(report.metrics.buy_hold)}</strong><small>same window</small></div><div><span>Max drawdown</span><strong>{pct(report.metrics.net.max_drawdown)}</strong><small>net series</small></div></div></section>
        <section className="funnel"><div><strong>{data.factors.length}</strong><span>TRIALS</span></div><div><strong>{counts.REJECTED ?? 0}</strong><span>REJECTED</span></div><div><strong>{counts.INCONCLUSIVE ?? 0}</strong><span>INCONCLUSIVE</span></div><div><strong>{counts.CANDIDATE ?? 0}</strong><span>CANDIDATE</span></div><Link href="/factors">Open Factor Graveyard →</Link></section>
        <details className="search-budget"><summary>Research Search Budget <span>{hardened.gate_distribution.PASS + hardened.gate_distribution.FAIL + hardened.gate_distribution.INCONCLUSIVE}/50 hardened gates</span></summary><div className="budget-grid"><div><strong>{data.factors.length}</strong><span>Committed autonomous trials</span></div><div><strong>{data.factors.filter((item) => !item.duplicate_of).length}</strong><span>Unique evaluated trials</span></div><div><strong>{data.factors.filter((item) => item.duplicate_of).length}</strong><span>Duplicate proposals</span></div><div><strong>{hardened.search_n}</strong><span>Current DSR search N</span></div><div><strong>18,224</strong><span>Measured Qwen tokens</span></div></div><p>Every strategy we test raises the evidence bar for the next one.</p></details>
        <footer><span>Generated {new Date(data.generated_at).toISOString()}</span><a href="/evidence/phase2-summary.json">Open raw evidence JSON ↗</a></footer>
      </main>
      <nav className="mobile-nav"><Link className="active" href="/lab">Lab</Link><Link href="/factors">Factors</Link><span>Paper</span><span>Ledger</span><span>System</span></nav>
    </div>
  );
}
