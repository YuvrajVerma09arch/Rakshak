import { useEffect, useRef, useState } from "react";
import { api, type JaalEvent } from "../api";

export default function JaalPanel() {
  const [events, setEvents] = useState<JaalEvent[]>([]);
  const [shown, setShown] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    api.jaalReplay().then(setEvents).catch(() => setError("Backend not reachable."));
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, []);

  // Reveal messages one by one, like a live conversation.
  useEffect(() => {
    if (shown < events.length) {
      timer.current = window.setTimeout(() => setShown((n) => n + 1), shown === 0 ? 300 : 1100);
    }
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [shown, events]);

  const meta = events.find((e): e is Extract<JaalEvent, { meta: unknown }> => "meta" in e);
  const visible = events.slice(0, shown);

  return (
    <section className="card">
      <h2>Rakshak Jaal (जाल) — wasting the scammer's time, extracting their network</h2>
      {error && <p className="error-note">{error}</p>}
      {meta && <span className="sim-badge">⚠ {meta.meta.label}</span>}
      {meta && <p className="hint">Persona: {meta.meta.persona}</p>}

      <div className="chat">
        {visible.map((e, i) => {
          if ("meta" in e) return null;
          if ("extracted_indicators" in e) {
            return (
              <div className="indicators" key={i}>
                <p>
                  <strong>Extracted indicators → Nigrani verification pipeline:</strong>
                </p>
                <p>
                  {e.extracted_indicators.vpas.map((v) => (
                    <code key={v}>{v}</code>
                  ))}
                  {e.extracted_indicators.phones.map((p) => (
                    <code key={p}>{p}</code>
                  ))}
                </p>
                <p className="hint">{e.outcome}</p>
              </div>
            );
          }
          return (
            <div className={`bubble ${e.from}`} key={i}>
              <div className="who">{e.from === "jaal" ? "🕸 Jaal (decoy persona)" : "☠ Scammer"}</div>
              {e.text}
            </div>
          );
        })}
      </div>
      {shown < events.length && <p className="hint">…</p>}
    </section>
  );
}
