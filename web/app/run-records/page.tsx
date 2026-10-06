import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
import AppShell from "../../components/AppShell";
import { chainSummary, summary, trials } from "../../lib/evidence";
import type { RunRecord } from "../../server/run-records";

type RunArtifact = {
  label: string; started_at: string; completed_at: string;
  sdk: { package: string; version: string; mode: string; tool: string; action: string; credentials_used: boolean };
  frozen_research: { search_n: number; candidates: number; certified: number; paper_positions: number; paper_orders: number; paper_fills: number; capital_gate: string; ledger_events: number; evidence_chain: string; research_status: string };
  checkpoints: RunRecord[];
  supplementary_validation: { trial: number; status: string; certified_history_days: number; historical_backtest_fills: number; oos_window_days: number; oos_fills: number };
  account_balance_change_semantics: string;
  source_code: string[];
};

const headings = ["Timestamp · UTC", "Instrument", "Observed price · USDT", "Direction", "Quantity", "Balance Δ · USDT", "Candidates", "Capital gate", "Execution state", "SDK mode", "Decision reason"];

export default function RunRecordsPage() {
  const artifact = JSON.parse(fs.readFileSync(path.join(process.cwd(), "public/evidence/AGENTIC_TRADING_RUN_RECORD.json"), "utf8")) as RunArtifact;
  const current = summary();
  const chain = chainSummary();
  const [trial8] = trials();
  if (artifact.frozen_research.search_n !== current.global_search_n || artifact.frozen_research.candidates !== current.candidates || artifact.frozen_research.ledger_events !== chain.event_count ||
      artifact.frozen_research.evidence_chain !== chain.status || artifact.supplementary_validation.status !== trial8.outcome || artifact.supplementary_validation.oos_fills !== trial8.metrics?.oos_net?.fills) {
    throw new Error("Run-record snapshot does not match frozen public evidence");
  }
  return <AppShell active="">
    <section className="hero compact run-hero"><div><p className="eyebrow">AGENTIC TRADING / PUBLIC RUN RECORD</p><h1>Real market checks. No order.</h1><p className="thesis">An actual, timestamped read-only SDK observation session on RAMDUSDT. At each checkpoint the research gate blocked the paper decision before an OrderIntent existed. This is not executed trading.</p></div><div className="run-verdict"><span>CAPITAL GATE</span><strong>CLOSED</strong><small>BLOCKED_NO_CANDIDATE</small></div></section>
    <div className="notice danger"><strong>ACTUAL PAPER-DECISION / NO-ORDER RUN</strong> · {artifact.checkpoints.length} public market observations · 0 positions · 0 orders · 0 fills · no account read</div>
    <section className="run-meta" aria-label="Observation session metadata"><div><span>SDK</span><strong>{artifact.sdk.package} v{artifact.sdk.version}</strong></div><div><span>MODE</span><strong>{artifact.sdk.mode}</strong></div><div><span>OBSERVATION WINDOW</span><strong>{artifact.started_at} → {artifact.completed_at}</strong></div><div><span>SEARCH / CANDIDATES</span><strong>{artifact.frozen_research.search_n} / {artifact.frozen_research.candidates}</strong></div></section>
    <section className="panel top-gap"><div className="panel-head"><span>CHECKPOINT LOG</span><span>BITGET AGENT SDK · SPOT TICKERS · LAST PRICE</span></div><p className="run-scroll-hint">Scroll horizontally to inspect every field →</p><div className="run-table-scroll"><table className="run-table"><thead><tr>{headings.map(heading => <th key={heading} scope="col">{heading}</th>)}</tr></thead><tbody>{artifact.checkpoints.map((row, index) => <tr key={`${row.timestamp}-${index}`}><td><time dateTime={row.timestamp}>{row.timestamp}</time></td><td>{row.instrument}</td><td className="run-price">{row.observed_market_price}</td><td>{row.direction}</td><td>{row.quantity}</td><td>{row.account_balance_change}</td><td>{row.candidate_count}</td><td>{row.capital_gate_state}</td><td className="run-blocked">{row.execution_state}</td><td>{row.sdk_mode}</td><td>{row.decision_reason}</td></tr>)}</tbody></table></div><div className="run-downloads"><a href="/evidence/AGENTIC_TRADING_RUN_RECORD.csv" download>Download CSV ↗</a><a href="/evidence/AGENTIC_TRADING_RUN_RECORD.json" download>Download JSON ↗</a></div></section>
    <p className="run-method">The displayed price is Bitget&apos;s public <code>lastPrice</code>, not a fill price. The JSON also includes the ticker and SDK request timestamps. Balance change of 0 describes this system&apos;s no-order path; no private balance was queried, so unrelated account activity is not measured.</p>
    <section className="panel top-gap"><div className="panel-head"><span>SUPPLEMENTARY VALIDATION · TRIAL 8</span><span>HISTORICAL BACKTEST ONLY</span></div><div className="run-trial-stats"><div><strong>{artifact.supplementary_validation.certified_history_days}</strong><span>CERTIFIED DAYS</span></div><div><strong>{artifact.supplementary_validation.historical_backtest_fills}</strong><span>HISTORICAL FILLS</span></div><div><strong>{artifact.supplementary_validation.oos_fills}</strong><span>LATEST {artifact.supplementary_validation.oos_window_days}-DAY OOS FILLS</span></div><div><strong className="run-blocked">{artifact.supplementary_validation.status}</strong><span>FACTOR OUTCOME</span></div></div><p className="sdk-note">These ten fills are deterministic backtest events, not paper or live orders. The rejected factor supplied no Candidate to this observation session. <Link href="/factors/trial-8">Inspect Trial 8 →</Link></p></section>
    <section className="run-sources"><h2>Source and provenance</h2><p>Read-only observations were generated locally from the official SDK, the committed research summary, and the existing candidate-to-order gate. This export is separate from the historical evidence manifest and the 190-event ledger.</p><div>{artifact.source_code.map(source => <a key={source} href={`https://github.com/Alike001/factor-discovery-agent/blob/main/${source}`} target="_blank" rel="noopener noreferrer">{source} ↗</a>)}<a href="/evidence/latest/TRIAL_8.json">Frozen Trial 8 JSON ↗</a></div></section>
  </AppShell>;
}
