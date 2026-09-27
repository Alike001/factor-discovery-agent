import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "rToken Research Lab",
  description: "Evidence-first Bitget Reality factor research tracer",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

