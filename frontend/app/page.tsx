'use client';

import { useMemo, useState } from 'react';
import axios from 'axios';

// Type definitions for the full governance response
interface RetrievedDocument {
  index: number;
  content_preview: string;
}

interface Confidence {
  confidence_percentage: number;
  confidence_level: string;
}

interface TokenUsage {
  prompt_tokens: number;
  response_tokens: number;
  total_tokens: number;
}

interface GovernanceItem {
  check: string;
  status: string;
  score: number;
  details: string;
}

interface GovernanceSummary {
  overall_status: string;
  requires_human_review: boolean;
  items: GovernanceItem[];
}

interface Explanation {
  reasoning_summary: string;
  retrieved_sources: { index: number; content_preview: string; length: number }[];
  confidence_explanation: string;
  governance_summary: GovernanceSummary;
  human_readable_explanation: string;
  violation_details: { policy_id: string; policy_name: string; severity: string; description: string }[];
}

interface GovernanceResponse {
  response: string;
  provider: string;
  model: string;
  latency: number;
  token_usage: TokenUsage;
  retrieved_chunks: string[];
  retrieved_documents: RetrievedDocument[];
  confidence: Confidence;
  hallucination_score: number;
  bias_score: number;
  toxicity_score: number;
  policy_compliant: boolean;
  requires_human_review: boolean;
  governance_summary: GovernanceSummary;
  explanation: Explanation;
  governance: Record<string, unknown>;
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    PASS: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    WARNING: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    FAIL: 'bg-red-500/20 text-red-300 border-red-500/30',
  };
  const cls = colors[status] || 'bg-slate-500/20 text-slate-300 border-slate-500/30';
  return (
    <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${cls}`}>
      {status}
    </span>
  );
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  const pct = Math.min(100, Math.max(0, score * 100));
  const color = pct > 66 ? 'bg-emerald-500' : pct > 33 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-32 shrink-0 text-slate-400">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-700">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-12 text-right font-mono text-xs text-slate-400">{score.toFixed(2)}</span>
    </div>
  );
}

function ConfidenceBar({ percentage }: { percentage: number }) {
  const color = percentage >= 70 ? 'bg-emerald-500' : percentage >= 50 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-400">Confidence</span>
        <span className="font-mono text-slate-200">{percentage.toFixed(1)}%</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-700">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

function CollapsibleSection({ title, icon, defaultOpen = false, children }: { title: string; icon: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900/60">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left transition hover:bg-slate-800/50"
      >
        <span className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <span className="text-base">{icon}</span>
          {title}
        </span>
        <svg
          className={`h-4 w-4 text-slate-400 transition ${open ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className="border-t border-slate-700/30 px-4 py-3">{children}</div>}
    </div>
  );
}

const providers = [
  { id: 'ollama', label: 'Ollama', description: 'Local deployment for offline experiments', accent: 'from-emerald-500 to-lime-500' },
  { id: 'openai', label: 'OpenAI', description: 'Fast enterprise-ready chat model', accent: 'from-cyan-500 to-blue-500' },
  { id: 'gemini', label: 'Google Gemini', description: 'Multimodal and flexible inference', accent: 'from-fuchsia-500 to-violet-500' },
];

export default function Home() {
  const [message, setMessage] = useState('');
  const [result, setResult] = useState<GovernanceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState('ollama');
  const [providerStatus, setProviderStatus] = useState('Configured for the selected provider');

  const activeProvider = useMemo(() => providers.find((p) => p.id === selectedProvider), [selectedProvider]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const { data } = await axios.post('http://127.0.0.1:8000/api/chat/', {
        message,
        provider: selectedProvider,
      });
      setResult(data as GovernanceResponse);
      setProviderStatus(`Using ${activeProvider?.label ?? 'the selected provider'}`);
    } catch (error) {
  console.error("Full Backend Error context:", error);
  
  if (axios.isAxiosError(error)) {
    if (error.response) {
      // The server received the request and responded with a non-2xx status code
      console.error("Backend Status:", error.response.status);
      console.error("Backend Data:", error.response.data);
      setProviderStatus(`Backend Error (${error.response.status}): Check your browser console.`);
    } else if (error.request) {
      // The request was made but no response was received (e.g., server is down)
      console.error("No response received from backend. Check if Django is running.");
      setProviderStatus("Cannot connect to Django. Verification failed.");
    } else {
      // Something else happened while setting up the request
      console.error("Axios configuration error:", error.message);
      setProviderStatus(`Request Error: ${error.message}`);
    }
  } else {
    setProviderStatus('An unexpected error occurred.');
  }

  setResult(null); 
} finally {
  setLoading(false);
}


  };

  const gs = result?.governance_summary;
  const exp = result?.explanation;
  const govItems = gs?.items ?? [];
  const overallStatus = gs?.overall_status ?? 'PASS';

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.16),_transparent_35%),linear-gradient(135deg,_#020617,_#0f172a_55%,_#111827)] px-6 py-12 text-slate-100">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 rounded-[2rem] border border-slate-800/90 bg-slate-950/80 p-8 shadow-[0_30px_120px_rgba(0,0,0,0.45)] backdrop-blur-xl">
        {/* Header */}
        <header className="space-y-4">
          <div className="inline-flex w-fit items-center rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300">
            Responsible AI Framework
          </div>
          <h1 className="text-3xl font-semibold sm:text-4xl">Governance-integrated support experience</h1>
          <p className="max-w-3xl text-base text-slate-300">
            Every response passes through a complete governance pipeline: hallucination detection, bias analysis, toxicity
            screening, policy validation, and confidence estimation.
          </p>
        </header>

        {/* Provider Selection */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">LLM provider selection</h2>
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
              {providerStatus}
            </span>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {providers.map((provider) => {
              const isActive = selectedProvider === provider.id;
              return (
                <button
                  key={provider.id}
                  type="button"
                  onClick={() => {
                    setSelectedProvider(provider.id);
                    setProviderStatus(`Ready to use ${provider.label}`);
                  }}
                  className={`rounded-2xl border p-4 text-left transition ${
                    isActive
                      ? 'border-cyan-400 bg-slate-800 shadow-lg shadow-cyan-500/10'
                      : 'border-slate-700 bg-slate-950/70 hover:border-slate-500'
                  }`}
                >
                  <div className={`mb-3 h-2 rounded-full bg-gradient-to-r ${provider.accent}`} />
                  <div className="text-sm font-semibold text-white">{provider.label}</div>
                  <div className="mt-1 text-sm text-slate-400">{provider.description}</div>
                </button>
              );
            })}
          </div>
        </section>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
          <label className="text-sm font-medium text-slate-200" htmlFor="message">
            Ask a support question
          </label>
          <textarea
            id="message"
            rows={4}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Try asking about a policy or requesting a password..."
            className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-100 outline-none ring-0 placeholder:text-slate-500"
          />
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={loading}
              className="rounded-full bg-cyan-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? 'Analyzing…' : `Send via ${activeProvider?.label}`}
            </button>
            <span className="text-sm text-slate-400">Current selection: {activeProvider?.label}</span>
          </div>
        </form>

        {/* Results Area */}
        {result && (
          <>
            {/* Overall Governance Status Banner */}
            {result.requires_human_review && (
              <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
                <span className="text-lg">⚠️</span>
                <div>
                  <p className="text-sm font-semibold text-red-300">Human Review Required</p>
                  <p className="text-xs text-red-300/70">This response was flagged by the governance pipeline and needs manual review.</p>
                </div>
              </div>
            )}

            {/* AI Response Card */}
            <CollapsibleSection title="AI Response" icon="💬" defaultOpen={true}>
              <p className="whitespace-pre-line text-sm leading-7 text-slate-200">{result.response}</p>
            </CollapsibleSection>

            <div className="grid gap-6 lg:grid-cols-2">
              {/* Explainability Card */}
              <CollapsibleSection title="Explainability" icon="🔍" defaultOpen={true}>
                <div className="space-y-3 text-sm text-slate-300">
                  {exp?.reasoning_summary && (
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">Reasoning Summary</p>
                      <p>{exp.reasoning_summary}</p>
                    </div>
                  )}
                  {exp?.human_readable_explanation && (
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">Explanation</p>
                      <p>{exp.human_readable_explanation}</p>
                    </div>
                  )}
                  {exp?.confidence_explanation && (
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">Confidence Detail</p>
                      <p>{exp.confidence_explanation}</p>
                    </div>
                  )}
                  {exp?.violation_details && exp.violation_details.length > 0 && (
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-red-400">Policy Violations</p>
                      <ul className="space-y-1">
                        {exp.violation_details.map((v, i) => (
                          <li key={i} className="rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2 text-xs">
                            <span className="font-semibold text-red-300">{v.policy_id}</span> - {v.description}
                            <br />
                            <span className="text-red-300/70">Severity: {v.severity}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CollapsibleSection>

              {/* Governance Summary Card */}
              <CollapsibleSection title="Governance Summary" icon="🛡️" defaultOpen={true}>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">Overall Status</span>
                    <StatusBadge status={overallStatus} />
                  </div>
                  {result.requires_human_review && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Human Review</span>
                      <StatusBadge status="FAIL" />
                    </div>
                  )}
                  <div className="mt-2 space-y-2">
                    {govItems.map((item, i) => (
                      <div key={i} className="flex items-center justify-between rounded-lg bg-slate-800/50 px-3 py-2 text-xs">
                        <span className="text-slate-300">{item.check}</span>
                        <StatusBadge status={item.status} />
                      </div>
                    ))}
                  </div>
                </div>
              </CollapsibleSection>
            </div>

            {/* Confidence Card */}
            <CollapsibleSection title="Confidence" icon="📊" defaultOpen={true}>
              <div className="space-y-4">
                {result.confidence && (
                  <ConfidenceBar percentage={result.confidence.confidence_percentage} />
                )}
                {result.confidence && (
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>Level: <span className="font-semibold text-slate-200">{result.confidence.confidence_level}</span></span>
                  </div>
                )}
              </div>
            </CollapsibleSection>

            {/* Governance Scores */}
            <CollapsibleSection title="Response Metrics" icon="📈" defaultOpen={false}>
              <div className="space-y-3">
                <ScoreBar score={result.hallucination_score} label="Hallucination Score" />
                <ScoreBar score={result.bias_score} label="Bias Score" />
                <ScoreBar score={result.toxicity_score} label="Toxicity Score" />
                <div className="flex items-center gap-2 text-sm">
                  <span className="w-32 shrink-0 text-slate-400">Policy Compliant</span>
                  <StatusBadge status={result.policy_compliant ? 'PASS' : 'FAIL'} />
                </div>
              </div>
            </CollapsibleSection>

            {/* Retrieved Sources Card */}
            <CollapsibleSection title="Retrieved Sources" icon="📄" defaultOpen={false}>
              {result.retrieved_documents && result.retrieved_documents.length > 0 ? (
                <div className="grid gap-3">
                  {result.retrieved_documents.map((doc, i) => (
                    <div key={i} className="rounded-lg border border-slate-700/50 bg-slate-800/40 p-3 transition hover:border-cyan-600/50">
                      <div className="mb-1 flex items-center justify-between">
                        <span className="text-xs font-semibold text-cyan-300">Source {doc.index}</span>
                      </div>
                      <p className="text-xs leading-5 text-slate-400">{doc.content_preview}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400">No retrieved documents.</p>
              )}
            </CollapsibleSection>

            {/* Model Information */}
            <CollapsibleSection title="Model Information" icon="🤖" defaultOpen={false}>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Provider</span>
                  <span className="font-mono text-slate-200">{result.provider || 'N/A'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Model</span>
                  <span className="font-mono text-slate-200">{result.model || 'N/A'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Latency</span>
                  <span className="font-mono text-slate-200">{result.latency.toFixed(2)}s</span>
                </div>
              </div>
            </CollapsibleSection>

            {/* Response Metrics / Audit */}
            <CollapsibleSection title="Audit Information" icon="📋" defaultOpen={false}>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">Token Usage</p>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="rounded-lg bg-slate-800/50 px-3 py-2 text-center">
                      <p className="text-lg font-semibold text-slate-200">{result.token_usage?.prompt_tokens ?? 0}</p>
                      <p className="text-xs text-slate-400">Prompt</p>
                    </div>
                    <div className="rounded-lg bg-slate-800/50 px-3 py-2 text-center">
                      <p className="text-lg font-semibold text-slate-200">{result.token_usage?.response_tokens ?? 0}</p>
                      <p className="text-xs text-slate-400">Response</p>
                    </div>
                    <div className="rounded-lg bg-slate-800/50 px-3 py-2 text-center">
                      <p className="text-lg font-semibold text-slate-200">{result.token_usage?.total_tokens ?? 0}</p>
                      <p className="text-xs text-slate-400">Total</p>
                    </div>
                  </div>
                </div>
                {result.retrieved_chunks && result.retrieved_chunks.length > 0 && (
                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400">Chunks Retrieved</p>
                    <p className="text-lg font-semibold text-slate-200">{result.retrieved_chunks.length}</p>
                  </div>
                )}
              </div>
            </CollapsibleSection>
          </>
        )}
      </div>
    </main>
  );
}