'use client';

import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [explanation, setExplanation] = useState('');
  const [governance, setGovernance] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setResponse('');
    setExplanation('');
    setGovernance(null);

    try {
      const { data } = await axios.post('http://127.0.0.1:8000/api/chat/', {
        message,
      });

      setResponse(data.response);
      setExplanation(data.explanation);
      setGovernance(data.governance);
    } catch (error) {
      setResponse('The request could not be completed. Ensure the Django backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <div className="mx-auto flex max-w-5xl flex-col gap-8 rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl shadow-slate-950/30">
        <header className="space-y-3">
          <p className="text-sm uppercase tracking-[0.3em] text-cyan-400">Responsible AI Framework</p>
          <h1 className="text-3xl font-semibold sm:text-4xl">Governance-integrated customer support demo</h1>
          <p className="max-w-3xl text-base text-slate-300">
            This MVP demonstrates a layered architecture where chat responses are evaluated for toxicity, policy compliance, and review risk before being returned.
          </p>
        </header>

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
          <button
            type="submit"
            disabled={loading}
            className="w-fit rounded-full bg-cyan-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? 'Analyzing…' : 'Send to AI'}
          </button>
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
