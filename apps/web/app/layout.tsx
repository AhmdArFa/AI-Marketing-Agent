import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "AI Marketing Agent: 4S PLUS",
  description:
    "A marketing agent with a real brain for the automotive ERP domain: plans, tools, skills, guardrails, and human approvals.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
