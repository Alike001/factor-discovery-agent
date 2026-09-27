import fs from "node:fs";
import path from "node:path";

type Metric = {
  observations: number;
  total_return: number;
  sharpe: number | null;
  max_drawdown: number;
  turnover: number;
};

type Evidence = {
  generated_at: string;
  label: string;
  claim: string;
  expression_human: string;
  factor_hash: string;
  factor: { name: string; thesis: string; session_filter: string[]; universe: string[] };
  source: { last_timestamp: string; first_timestamp: string; aligned_rows: number; missing_bar_policy: string };
  protocol: {
    split_timestamp: string;
    split_rule: string;
    fill_rule: string;
    fee_per_fill: number;
    slippage_per_fill: number;
    fee_basis: string;
  };
  metrics: { gross: Metric; net: Metric; is_net: Metric; oos_net: Metric; fill_count: number; oos_fill_count: number };
  gates: { name: string; verdict: "PASS" | "FAIL" | "INCONCLUSIVE"; reason: string }[];
};

function readEvidence(): Evidence {
  const evidencePath = path.join(process.cwd(), "public", "evidence", "tracer-experiment.json");
  return JSON.parse(fs.readFileSync(evidencePath, "utf8")) as Evidence;
}

const percent = (value: number) => `${(value * 100).toFixed(2)}%`;
const number = (value: number | null) => (value === null ? "insufficient" : value.toFixed(2));

export default function LabPage() {
  const evidence = readEvidence();

  return (
    <div className="app-shell">
      <aside className="rail" aria-label="Primary navigation">
        <a className="brand" href="/lab" aria-label="rToken Research Lab">R/</a>
        <nav>
          <a className="active" href="/lab">Lab</a>
          <span aria-disabled="true">Factors</span>
          <span aria-disabled="true">Paper</span>
          <span aria-disabled="true">Ledger</span>
          <span aria-disabled="true">System</span>
        </nav>
      </aside>

      <main>
        <header className="system-strip">
          <span><i className="pulse" /> BITGET REALITY</span>
          <span>{evidence.factor.universe.length}/2 TRACER UNIVERSE</span>
          <span>PHASE 1 · COMPLETE</span>
          <strong>{evidence.label}</strong>
        </header>

        <section className="hero">
          <div>
            <p className="eyebrow">RESEARCH LAB / TRACER 001</p>
            <h1>{evidence.factor.name}</h1>
            <p className="thesis">{evidence.factor.thesis}</p>
          </div>
          <div className="source-time">
            <span>SOURCE TIMESTAMP</span>
            <strong>{new Date(evidence.source.last_timestamp).toLocaleString("en-GB", { timeZone: "UTC" })} UTC</strong>
            <small>{evidence.source.aligned_rows.toLocaleString()} aligned closed bars</small>
          </div>
        </section>

        <div className="notice"><strong>Architecture proof.</strong> {evidence.claim}</div>

        <section className="workspace">
          <article className="panel hypothesis">
            <div className="panel-head"><span>FACTOR EXPRESSION</span><span>OVERNIGHT · LONG / FLAT</span></div>
            <code>{evidence.expression_human}</code>
            <dl className="contract">
              <div><dt>Universe</dt><dd>{evidence.factor.universe.join(" · ")}</dd></div>
              <div><dt>Data window</dt><dd>{evidence.source.first_timestamp.slice(0, 10)} → {evidence.source.last_timestamp.slice(0, 10)}</dd></div>
              <div><dt>IS / OOS boundary</dt><dd>{evidence.protocol.split_timestamp.replace("T", " ").slice(0, 16)} UTC</dd></div>
              <div><dt>Fill rule</dt><dd>{evidence.protocol.fill_rule}</dd></div>
              <div><dt>Missing bars</dt><dd>{evidence.source.missing_bar_policy}</dd></div>
            </dl>
            <p className="hash">FACTOR {evidence.factor_hash}</p>
          </article>

          <article className="panel gates">
            <div className="panel-head"><span>DETERMINISTIC GATES</span><span>{evidence.gates.length} CHECKS</span></div>
            {evidence.gates.map((gate) => (
              <div className="gate" key={gate.name}>
                <div><strong>{gate.name}</strong><p>{gate.reason}</p></div>
                <span className={`verdict ${gate.verdict.toLowerCase()}`}>{gate.verdict}</span>
              </div>
            ))}
          </article>
        </section>

        <section className="panel metrics">
          <div className="panel-head"><span>HISTORICAL EXPERIMENT</span><span>GROSS vs NET</span></div>
          <div className="metric-grid">
            <div><span>Gross return</span><strong>{percent(evidence.metrics.gross.total_return)}</strong><small>before costs</small></div>
            <div><span>Net return</span><strong>{percent(evidence.metrics.net.total_return)}</strong><small>after costs</small></div>
            <div><span>IS net</span><strong>{percent(evidence.metrics.is_net.total_return)}</strong><small>fixed earlier window</small></div>
            <div><span>OOS net</span><strong>{percent(evidence.metrics.oos_net.total_return)}</strong><small>{evidence.metrics.oos_fill_count} fills</small></div>
            <div><span>Net Sharpe</span><strong>{number(evidence.metrics.net.sharpe)}</strong><small>hourly annualized</small></div>
            <div><span>Max drawdown</span><strong>{percent(evidence.metrics.net.max_drawdown)}</strong><small>net series</small></div>
          </div>
          <div className="cost-line">
            <span>Cost assumption</span>
            <strong>{(evidence.protocol.fee_per_fill * 100).toFixed(3)}% fee + {(evidence.protocol.slippage_per_fill * 100).toFixed(3)}% slippage per fill</strong>
            <em>{evidence.protocol.fee_basis}</em>
          </div>
        </section>

        <footer>
          <span>Generated {new Date(evidence.generated_at).toISOString()}</span>
          <a href="/evidence/tracer-experiment.json">Open raw evidence JSON ↗</a>
        </footer>
      </main>

      <nav className="mobile-nav" aria-label="Mobile navigation">
        <a className="active" href="/lab">Lab</a><span>Factors</span><span>Paper</span><span>Ledger</span><span>System</span>
      </nav>
    </div>
  );
}

