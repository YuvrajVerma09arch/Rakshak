// Typed client for the Rakshak API. Mirrors backend/app/capsule.py.

export type Channel = "sms" | "call" | "upi" | "qr" | "whatsapp" | "link";
export type ActionVerdict = "allow" | "warn" | "friction" | "block" | "guardian";
export type Language = "hi" | "gu" | "en";

export interface TraceEntry {
  agent: string;
  ms: number;
  cost_inr: number;
  notes: string;
}

export interface RiskCapsule {
  event_id: string;
  channel: Channel;
  language: string;
  raw_text: string;
  actor: { phone: string | null; vpa: string | null; known_to_user: boolean };
  ask: { type: string; amount_inr: number | null; urgency: string };
  payment_rail: { rail: string | null; recipient_first_seen: boolean };
  evidence: {
    matched_rules: string[];
    reputation_hits: string[];
    similar_cases: string[];
    community_reports_24h: number;
  };
  verdict: {
    evidence_score: number;
    harm_score: number;
    action: ActionVerdict;
    reasons: string[];
    vakeel_veto: boolean;
  };
  panchayat_trace: TraceEntry[];
  vulnerability_mode: boolean;
}

export interface AnalyzeResponse {
  capsule: RiskCapsule;
  warning_text: string;
  panchayat_convened: boolean;
}

export interface Scenario {
  id: string;
  title: string;
  channel: Channel;
  language: Language;
  online: boolean;
  vulnerability_mode: boolean;
  known_contacts: string[];
  text: string;
  note: string;
}

export type JaalEvent =
  | { meta: { label: string; persona: string; trigger: string } }
  | { from: "jaal" | "scammer"; text: string }
  | { extracted_indicators: { vpas: string[]; phones: string[] }; outcome: string };

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  analyze: (body: {
    text: string;
    channel: Channel;
    language: Language;
    online: boolean;
    vulnerability_mode: boolean;
    known_contacts: string[];
  }) => request<AnalyzeResponse>("/analyze", { method: "POST", body: JSON.stringify(body) }),

  scenarios: () => request<Scenario[]>("/scenarios"),

  jaalReplay: () => request<JaalEvent[]>("/jaal/replay"),

  report: (identifier: string, reporter_id: string, reason: string) =>
    request<{ level: string; report_count: number; promoted: boolean }>("/report", {
      method: "POST",
      body: JSON.stringify({ identifier, reporter_id, reason }),
    }),
};
