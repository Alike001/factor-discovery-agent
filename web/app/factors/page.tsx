import Link from "next/link";
import AppShell from "../../components/AppShell";
import { summary, trials } from "../../lib/evidence";
import { readPhase2 } from "../../lib/phase2";
import { readTargetedBatch } from "../../lib/targeted";

const tabs = ["all", "rejected", "inconclusive", "candidate", "certified"];

export default async function FactorsPage({ searchParams }: { searchParams: Promise<{ tab?: string }> }) {
  const state = summary();
  const tab = (await searchParams).tab?.toLowerCase() ?? "all";
  const recent = trials();
  const targeted = readTargetedBatch().trials.filter(item => item.trial_number);
  const phase1 = readPhase2().factors;
  const rows = [
    ...recent.map(t => ({ trial: t.trial_number, protocol: "fdp-v3", family: t.family, name: String(t.recipe?.name ?? "Session-transition structural failure"), thesis: t.qwen_rationale, symbols: t.family === "beta_residual" ? "RAMDUSDT · RQQQUSDT" : "Unavailable", session: t.family === "beta_residual" ? "regular" : "not evaluated", lifecycle: String(t.lifecycle?.action ?? "REJECTED"), hardFail: t.first_hard_fail, searchN: 9, href: `/factors/trial-${t.trial_number}`, evidence: `/evidence/latest/TRIAL_${t.trial_number}.json`, outcome: "REJECTED" })),
    ...targeted.map(t => ({ trial: t.trial_number!, protocol: "fdp-v2", family: t.family, name: t.proposal?.name ?? `${t.family} structural failure`, thesis: t.proposal?.thesis ?? "Proposal preserved as structural failure evidence.", symbols: "See evidence", session: t.proposal?.session_filter?.join(" · ") ?? "not evaluated", lifecycle: "REJECTED", hardFail: t.report?.first_hard_fail ?? "Syntax", searchN: t.trial_number!, href: "/evidence/targeted-batch-v2.json", evidence: "/evidence/targeted-batch-v2.json", outcome: "REJECTED" })),
    ...phase1.map(f => ({ trial: f.trial_number, protocol: "fdp-v1", family: "safe_ast", name: f.name, thesis: f.thesis, symbols: f.canonical_spec_json?.universe.join(" · ") ?? "Unavailable", session: f.canonical_spec_json?.session_filter.join(" · ") ?? "Unavailable", lifecycle: f.lifecycle_state ?? "INCONCLUSIVE", hardFail: f.gates.find(g => g.outcome === "FAIL")?.name ?? "Coverage", searchN: f.trial_number, href: `/factors/${f.factor_version_id}`, evidence: "/evidence/phase3-rejection-matrix.json", outcome: f.lifecycle_state ?? "INCONCLUSIVE" })),
  ].sort((a, b) => b.trial - a.trial);
  const filtered = tab === "all" ? rows : rows.filter(row => row.outcome.toLowerCase() === tab);
  return <AppShell active="Factors"><section className="hero compact"><div><p className="eyebrow">FACTOR LIBRARY / PERMANENT RECORD</p><h1>Nothing hidden.</h1><p className="thesis">All {state.trials} committed hypotheses remain inspectable. The library is ordered by trial, never by return.</p></div></section><nav className="tabs" aria-label="Factor status filters">{tabs.map(item => <Link className={tab === item ? "active" : ""} href={item === "all" ? "/factors" : `/factors?tab=${item}`} key={item}>{item[0].toUpperCase() + item.slice(1)}</Link>)}</nav>{filtered.length === 0 ? <section className="empty-state"><span>0 RESULTS</span><h2>No {tab} factors.</h2><p>Empty is the truthful state. No records are created to populate this view.</p></section> : <section className="factor-list">{filtered.map(row => <article className="factor-row" key={row.trial}><div><span className="eyebrow">TRIAL {row.trial} · {row.protocol} · {row.family}</span><h2><Link href={row.href}>{row.name}</Link></h2><p>{row.thesis}</p><div className="tag-row"><span>{row.symbols}</span><span>{row.session}</span><span>{row.lifecycle}</span></div></div><div className="factor-outcome"><span className="verdict fail">{row.outcome}</span><strong>FIRST HARD FAIL · {row.hardFail}</strong><small>SEARCH N AT EVALUATION · {row.searchN}</small><Link className="text-link" href={row.evidence}>Raw evidence ↗</Link></div></article>)}</section>}<footer><span>DEFAULT ORDER · NEWEST TRIAL FIRST</span><Link href="/proof">Research proof →</Link></footer></AppShell>;
}
