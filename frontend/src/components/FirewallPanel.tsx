import { useEffect, useState } from "react";
import { api, type AnalyzeResponse, type Channel, type Language, type Scenario } from "../api";
import VerdictCard from "./VerdictCard";

const CHANNELS: Channel[] = ["sms", "whatsapp", "call", "upi", "qr", "link"];
const LANGUAGES: { code: Language; label: string }[] = [
  { code: "hi", label: "हिन्दी" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "en", label: "English" },
];

export default function FirewallPanel() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [channel, setChannel] = useState<Channel>("sms");
  const [language, setLanguage] = useState<Language>("hi");
  const [online, setOnline] = useState(true);
  const [elderMode, setElderMode] = useState(false);
  const [knownContacts, setKnownContacts] = useState<string[]>([]);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .scenarios()
      .then((list) => {
        setScenarios(list);
        // Deep-link for stage demos: /?scenario=prize auto-loads and runs that preset.
        const wanted = new URLSearchParams(window.location.search).get("scenario");
        const s = list.find((x) => x.id === wanted);
        if (s) {
          loadScenario(s);
          void runAnalysis(s.text, s.channel, s.language, s.online, s.vulnerability_mode, s.known_contacts);
        }
      })
      .catch(() => setError("Backend not reachable — is the API running on :8000?"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function loadScenario(s: Scenario) {
    setSelected(s.id);
    setText(s.text);
    setChannel(s.channel);
    setLanguage(s.language);
    setOnline(s.online);
    setElderMode(s.vulnerability_mode);
    setKnownContacts(s.known_contacts);
    setResult(null);
  }

  async function runAnalysis(
    t: string,
    ch: Channel,
    lang: Language,
    isOnline: boolean,
    vuln: boolean,
    contacts: string[],
  ) {
    if (!t.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setResult(
        await api.analyze({
          text: t,
          channel: ch,
          language: lang,
          online: isOnline,
          vulnerability_mode: vuln,
          known_contacts: contacts,
        }),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setBusy(false);
    }
  }

  const analyze = () => runAnalysis(text, channel, language, online, elderMode, knownContacts);

  return (
    <>
      <section className="card">
        <h2>Decision moment — what did the user just receive?</h2>
        <div className="chips">
          {scenarios.map((s) => (
            <button
              key={s.id}
              className={`chip ${selected === s.id ? "selected" : ""}`}
              title={s.note}
              onClick={() => loadScenario(s)}
            >
              {s.title}
            </button>
          ))}
        </div>
        <textarea
          value={text}
          placeholder="Paste an SMS, WhatsApp message, UPI collect request, or QR payload…"
          onChange={(e) => {
            setText(e.target.value);
            setSelected(null);
          }}
        />
        <div className="controls">
          <label>
            Channel
            <select value={channel} onChange={(e) => setChannel(e.target.value as Channel)}>
              {CHANNELS.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label>
            Language
            <select value={language} onChange={(e) => setLanguage(e.target.value as Language)}>
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
          </label>
          <label className="toggle">
            <input type="checkbox" checked={!online} onChange={(e) => setOnline(!e.target.checked)} />
            ✈ Airplane mode (Drishti only, ₹0)
          </label>
          <label className="toggle">
            <input type="checkbox" checked={elderMode} onChange={(e) => setElderMode(e.target.checked)} />
            🛡 Elder profile (guardian routing)
          </label>
          <button className="analyze-btn" onClick={analyze} disabled={busy || !text.trim()}>
            {busy ? "Council deliberating…" : "Check before I pay"}
          </button>
        </div>
        {knownContacts.length > 0 && (
          <p className="hint">Known contacts for this run: {knownContacts.join(", ")}</p>
        )}
        {error && <p className="error-note">{error}</p>}
      </section>

      {result && <VerdictCard result={result} />}
    </>
  );
}
