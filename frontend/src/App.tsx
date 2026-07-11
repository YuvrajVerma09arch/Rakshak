import { useState } from "react";
import FirewallPanel from "./components/FirewallPanel";
import JaalPanel from "./components/JaalPanel";

type Tab = "firewall" | "jaal";

export default function App() {
  const [tab, setTab] = useState<Tab>("firewall");

  return (
    <>
      <header>
        <div className="masthead">
          <h1>
            RAKSHAK<span className="devanagari">रक्षक</span>
          </h1>
        </div>
        <p className="tagline">
          The Agent Panchayat — a council of guardian agents at the moment money moves.
          Scam bots attack alone; Rakshak defends as a council.
        </p>
        <nav className="tabs">
          <button className={tab === "firewall" ? "active" : ""} onClick={() => setTab("firewall")}>
            Trust Firewall
          </button>
          <button className={tab === "jaal" ? "active" : ""} onClick={() => setTab("jaal")}>
            Jaal — Honeypot
          </button>
        </nav>
      </header>

      {tab === "firewall" ? <FirewallPanel /> : <JaalPanel />}

      <footer>
        Drishti watches offline for ₹0 · the Panchayat convenes only on ambiguity (≈₹0.15/case) ·
        Vakeel&apos;s veto protects legitimate payments · report fraud at 1930 (Cyber Crime Helpline)
      </footer>
    </>
  );
}
