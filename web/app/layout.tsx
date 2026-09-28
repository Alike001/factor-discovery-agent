import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: {
    default: "Factor Discovery Agent — Evidence-Gated rToken Research",
    template: "%s · Factor Discovery Agent",
  },
  description: "An autonomous Bitget rToken factor-research system where Qwen proposes hypotheses and deterministic evidence gates decide whether capital is allowed.",
  openGraph: {
    type: "website",
    title: "Factor Discovery Agent — Evidence-Gated rToken Research",
    description: "Qwen proposes bounded rToken hypotheses. Deterministic evidence gates decide whether capital is allowed.",
    siteName: "Factor Discovery Agent",
  },
  twitter: {
    card: "summary",
    title: "Factor Discovery Agent — Evidence-Gated rToken Research",
    description: "Autonomous Bitget rToken research with a deterministic capital gate.",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
