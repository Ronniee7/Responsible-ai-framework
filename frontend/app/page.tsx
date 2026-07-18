'use client';

import { useMemo, useState } from 'react';
import axios from 'axios';

const providers = [
  { id: 'openai', label: 'OpenAI', description: 'Fast enterprise-ready chat model', accent: 'from-cyan-500 to-blue-500' },
  { id: 'gemini', label: 'Google Gemini', description: 'Multimodal and flexible inference', accent: 'from-fuchsia-500 to-violet-500' },
  { id: 'ollama', label: 'Ollama', description: 'Local deployment for offline experiments', accent: 'from-emerald-500 to-lime-500' },
];

export default function Home() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [explanation, setExplanation] = useState('');
  const [governance, setGovernance] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [providerStatus, setProviderStatus] = useState('Configured for the selected provider');

  const activeProvider = useMemo(() => providers.find((provider) => provider.id === selectedProvider), [selectedProvider]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setResponse('');
    setExplanation('');
    setGovernance(null);

    try {
      const { data } = await axios.post('http://127.0.0.1:8000/api/chat/', {
        message,
        provider: selectedProvider,
      });

      setResponse(data.response);
      setExplanation(data.explanation);
      setGovernance(data.governance);
      setProviderStatus(`Using ${activeProvider?.label ?? 'the selected provider'}`);
    } catch (error) {
      setResponse('The request could not be completed. Ensure the Django backend is running.');
      setProviderStatus('Request failed. Check backend connectivity or provider configuration.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.16),_transparent_35%),linear-gradient(135deg,_#020617,_#0f172a_55%,_#111827)] px-6 py-12 text-slate-100">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 rounded-[2rem] border border-slate-800/90 bg-slate-950/80 p-8 shadow-[0_30px_120px_rgba(0,0,0,0.45)] backdrop-blur-xl">
        <header className="space-y-4">
          <div className="inline-flex w-fit items-center rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300">
            Responsible AI Framework
          </div>
          <h1 className="text-3xl font-semibold sm:text-4xl">Governance-integrated support experience</h1>
          <p className="max-w-3xl text-base text-slate-300">
            Switch between AI providers dynamically while preserving the governance, explainability, and retrieval pipeline beneath the surface.
          </p>
        </header>

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
                  className={`rounded-2xl border p-4 text-left transition ${isActive ? 'border-cyan-400 bg-slate-800 shadow-lg shadow-cyan-500/10' : 'border-slate-700 bg-slate-950/70 hover:border-slate-500'}`}
                >
                  <div className={`mb-3 h-2 rounded-full bg-gradient-to-r ${provider.accent}`} />
                  <div className="text-sm font-semibold text-white">{provider.label}</div>
                  <div className="mt-1 text-sm text-slate-400">{provider.description}</div>
                </button>
              );
            })}
          </div>
        </section>

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

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
            <h2 className="text-lg font-semibold text-white">Response</h2>
            <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-300">
              {response || 'No response yet.'}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
            <h2 className="text-lg font-semibold text-white">Governance summary</h2>
            {governance ? (
              <ul className="mt-3 space-y-2 text-sm text-slate-300">
                <li>Policy compliant: {String(governance.policy_compliant)}</li>
                <li>Toxicity score: {String(governance.toxicity_score)}</li>
                <li>Risk score: {String(governance.risk_score)}</li>
                <li>Human review: {String(governance.requires_human_review)}</li>
              </ul>
            ) : (
              <p className="mt-3 text-sm text-slate-400">Governance results will appear here.</p>
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
          <h2 className="text-lg font-semibold text-white">Explanation</h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">{explanation || 'Explanation will be generated after the request is evaluated.'}</p>
        </section>
      </div>
    </main>
  );
}
