import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Autonomous rToken Research Lab",
  description: "Qwen proposes session factors; deterministic evidence gates reject weak ideas.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
