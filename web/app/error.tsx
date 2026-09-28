"use client";
export default function Error({ reset }: { reset: () => void }) { return <div className="route-state"><span>EVIDENCE VIEW UNAVAILABLE</span><h1>The stored snapshot could not be read.</h1><p>No fallback data was fabricated.</p><button onClick={reset}>Try again</button></div>; }
