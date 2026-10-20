"use client";

import { useState } from "react";
import ArchitectureExplorer from "../components/ArchitectureExplorer";
import BrainConsole from "../components/BrainConsole";
import DomainExplorer from "../components/DomainExplorer";

const TABS = [
  { id: "console", label: "Brain Console" },
  { id: "architecture", label: "Architecture and Patterns" },
  { id: "domain", label: "Domain: 4S PLUS" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function Home() {
  const [tab, setTab] = useState<TabId>("console");
  return (
    <main>
      <header>
        <div>
          <h1>AI Marketing Agent</h1>
          <p className="sub">
            Built for one domain first: 4S PLUS automotive ERP by Vo Technology. A brain that plans in the open,
            computes with code, and never touches the outside world without a human.
          </p>
        </div>
        <a className="repo" href="https://github.com/AhmdArFa/AI-Marketing-Agent">
          GitHub repo
        </a>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button key={t.id} className={tab === t.id ? "tab active" : "tab"} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "console" && <BrainConsole />}
      {tab === "architecture" && <ArchitectureExplorer />}
      {tab === "domain" && <DomainExplorer />}

      <footer>
        Python computes. TypeScript orchestrates. The brain plans. Humans approve. Numbers come from code, never
        from a model.
      </footer>
    </main>
  );
}
