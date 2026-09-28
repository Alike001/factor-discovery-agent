import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: { default: "R/ Autonomous rToken Research", template: "%s · R/" },
  description: "Autonomous Qwen factor research with deterministic falsification before capital.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
