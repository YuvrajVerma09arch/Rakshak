import type { TraceEntry } from "../api";

// Fixed agent → categorical slot assignment (never cycled, per the palette method).
const AGENT_COLOR: Record<string, string> = {
  drishti: "var(--agent-drishti)",
  jasoos: "var(--agent-jasoos)",
  vakeel: "var(--agent-vakeel)",
  bhasha: "var(--agent-bhasha)",
  sarpanch: "var(--agent-sarpanch)",
};

const AGENT_LABEL: Record<string, string> = {
  drishti: "Drishti · दृष्टि",
  jasoos: "Jasoos · जासूस",
  vakeel: "Vakeel · वकील",
  bhasha: "Bhasha · भाषा",
  sarpanch: "Sarpanch · सरपंच",
};

export default function TraceTimeline({ trace }: { trace: TraceEntry[] }) {
  return (
    <div className="trace">
      {trace.map((t, i) => (
        <div className="trace-row" key={i}>
          <span className="agent-chip">
            <span className="dot" style={{ background: AGENT_COLOR[t.agent] ?? "var(--muted)" }} />
            {AGENT_LABEL[t.agent] ?? t.agent}
          </span>
          <span className="trace-meta">
            {t.ms} ms · ₹{t.cost_inr.toFixed(2)}
          </span>
          <span className="trace-notes">{t.notes}</span>
        </div>
      ))}
    </div>
  );
}
