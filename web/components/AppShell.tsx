import Link from "next/link";
import { summary } from "../lib/evidence";

const nav = [["Lab", "/lab"], ["Factors", "/factors"], ["Paper", "/paper"], ["Ledger", "/ledger"], ["System", "/system"]];

export default function AppShell({ active, children }: { active: string; children: React.ReactNode }) {
  const state = summary();
  return <div className="app-shell">
    <aside className="rail"><Link className="brand" href="/" aria-label="Back to landing page">R/</Link><nav aria-label="Primary">{nav.map(([label, href]) => <Link className={active === label ? "active" : ""} href={href} key={href}>{label}</Link>)}</nav><div className="rail-footer"><Link className="overview-link" href="/">Overview ↗</Link><Link className="proof-link" href="/proof">Research proof ↗</Link></div></aside>
    <main>
      <header className="truth-strip" aria-label="Global product status"><span><i className="pulse" /> REAL BITGET MARKET DATA</span><span>RESEARCH MODE</span><span>NO CAPITAL ALLOCATED</span><span>{state.protocol}</span><span>SEARCH N {state.global_search_n}</span><strong>CHAIN VERIFIED</strong><time>{new Date(state.latest_verified_source_timestamp).toISOString()}</time></header>
      {children}
    </main>
    <nav className="mobile-nav" aria-label="Mobile navigation">{nav.map(([label, href]) => <Link className={active === label ? "active" : ""} href={href} key={href}>{label}</Link>)}</nav>
  </div>;
}
