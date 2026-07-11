import type { AnalyzeResponse, ActionVerdict } from "../api";
import TraceTimeline from "./TraceTimeline";

// Status semantics: icon + label + color, never color alone.
const VERDICT: Record<ActionVerdict, { icon: string; label: string; sub: string; cls: string }> = {
  allow: {
    icon: "✅",
    label: "SAFE TO PROCEED",
    sub: "No scam signals — the payment goes through silently.",
    cls: "v-allow",
  },
  warn: {
    icon: "⚠️",
    label: "WAIT — THINK FIRST",
    sub: "Some scam signals found. Read the reasons before paying.",
    cls: "v-warn",
  },
  friction: {
    icon: "🛑",
    label: "VERY LIKELY A SCAM",
    sub: "Strong evidence. A hold + voice warning stands between the user and the money.",
    cls: "v-friction",
  },
  block: {
    icon: "⛔",
    label: "CONFIRMED SCAM — BLOCKED",
    sub: "Community-verified fraud. The payment is stopped.",
    cls: "v-block",
  },
  guardian: {
    icon: "🛡",
    label: "GUARDIAN APPROVAL NEEDED",
    sub: "High risk for a protected user — Sahara has sent the guardian a risk card.",
    cls: "v-guardian",
  },
};

function Meter({ name, value }: { name: string; value: number }) {
  return (
    <div className="meter">
      <div className="meter-head">
        <span className="meter-name">{name}</span>
        <span className="meter-value">{value.toFixed(2)}</span>
      </div>
      <div className="track" role="meter" aria-valuemin={0} aria-valuemax={1} aria-valuenow={value} aria-label={name}>
        <div className="fill" style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
    </div>
  );
}

export default function VerdictCard({ result }: { result: AnalyzeResponse }) {
  const { capsule, warning_text, panchayat_convened } = result;
  const v = VERDICT[capsule.verdict.action];
  const totalCost = capsule.panchayat_trace.reduce((s, t) => s + t.cost_inr, 0);
  const totalMs = capsule.panchayat_trace.reduce((s, t) => s + t.ms, 0);

  return (
    <>
      <div className={`verdict-banner ${v.cls}`}>
        <span className="icon" aria-hidden>
          {v.icon}
        </span>
        <div>
          <div className="label">{v.label}</div>
          <div className="sub">{v.sub}</div>
        </div>
      </div>

      <div className="tiles">
        <div className="tile">
          <div className="tile-value">{panchayat_convened ? "Convened" : "Not needed"}</div>
          <div className="tile-label">Agent Panchayat</div>
        </div>
        <div className="tile">
          <div className="tile-value">₹{totalCost.toFixed(2)}</div>
          <div className="tile-label">Decision cost</div>
        </div>
        <div className="tile">
          <div className="tile-value">{totalMs} ms</div>
          <div className="tile-label">Time to verdict</div>
        </div>
      </div>

      <section className="card">
        <h2>Risk scores</h2>
        <div className="meters">
          <Meter name="Evidence — how sure is the council it's a scam" value={capsule.verdict.evidence_score} />
          <Meter name="Harm — how bad if it is" value={capsule.verdict.harm_score} />
        </div>
      </section>

      {capsule.verdict.reasons.length > 0 && (
        <section className="card">
          <h2>Why — in the user's language</h2>
          <ul className="reasons">
            {capsule.verdict.reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
          {capsule.verdict.vakeel_veto && (
            <p className="veto-note">
              ⚖ Vakeel vetoed a hard block — downgraded to friction so a legitimate payment is never
              silently killed.
            </p>
          )}
        </section>
      )}

      {warning_text && (
        <section className="card">
          <h2>Bhasha's spoken warning (offline template)</h2>
          <div className="warning-text" lang={capsule.language}>
            {warning_text}
          </div>
        </section>
      )}

      <section className="card">
        <h2>Panchayat trace — every paisa and millisecond accounted for</h2>
        <TraceTimeline trace={capsule.panchayat_trace} />
      </section>
    </>
  );
}
