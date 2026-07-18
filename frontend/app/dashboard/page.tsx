'use client';

import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

const API = 'http://127.0.0.1:8000/api';

interface Summary {
  documents: { total: number; total_chunks: number; total_embeddings: number };
  conversations: { total: number; average_latency: number; average_confidence: number };
  governance: { hallucination_count: number; policy_violations: number; human_reviews: number; pass_rate: number };
  providers: Record<string, number>;
}

interface Analytics {
  conversation_volume: { hour: string; count: number }[];
  provider_usage: { provider: string; count: number }[];
  confidence_distribution: Record<string, number>;
  governance_outcomes: { passed: number; policy_violations: number; toxicity_flagged: number; bias_flagged: number; hallucination_flagged: number };
  latency_trend: { timestamp: string; latency: number }[];
  policy_violations: { timestamp: string; question: string; provider: string }[];
  total_events: number;
}

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${color || 'text-white'}`}>{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

function SimpleBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-24 shrink-0 text-slate-400">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-700">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-slate-400">{value}</span>
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [sumRes, anaRes] = await Promise.all([
        axios.get(`${API}/dashboard/summary/`),
        axios.get(`${API}/dashboard/analytics/`),
      ]);
      setSummary(sumRes.data as Summary);
      setAnalytics(anaRes.data as Analytics);
    } catch {
      // Silently handle
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-8 text-center text-sm text-slate-400">
        Loading dashboard...
      </div>
    );
  }

  const s = summary;
  const a = analytics;
  const maxProvider = a ? Math.max(...a.provider_usage.map((p) => p.count), 1) : 1;
  const maxConf = a ? Math.max(...Object.values(a.confidence_distribution), 1) : 1;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-8 space-y-4">
        <h1 className="text-2xl font-semibold text-white">Monitoring Dashboard</h1>
        <p className="text-sm text-slate-400">
          Real-time metrics for the Responsible AI governance pipeline.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Documents"
          value={s?.documents.total ?? 0}
          sub={`${s?.documents.total_chunks ?? 0} chunks, ${s?.documents.total_embeddings ?? 0} embeddings`}
          color="text-cyan-300"
        />
        <StatCard
          label="Conversations"
          value={s?.conversations.total ?? 0}
          sub={`Avg latency: ${(s?.conversations.average_latency ?? 0).toFixed(2)}s`}
          color="text-emerald-300"
        />
        <StatCard
          label="Average Confidence"
          value={`${(s?.conversations.average_confidence ?? 0).toFixed(1)}%`}
          color="text-amber-300"
        />
        <StatCard
          label="Governance Pass Rate"
          value={`${s?.governance.pass_rate ?? 0}%`}
          sub={`${s?.governance.human_reviews ?? 0} human reviews`}
          color={ (s?.governance.pass_rate ?? 0) >= 80 ? 'text-emerald-300' : 'text-amber-300' }
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Provider Usage */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">Provider Usage</h2>
          {a && a.provider_usage.length > 0 ? (
            <div className="space-y-2">
              {a.provider_usage.map((p) => (
                <SimpleBar key={p.provider} label={p.provider} value={p.count} max={maxProvider} color="bg-cyan-500" />
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No provider data yet.</p>
          )}
        </div>

        {/* Confidence Distribution */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">Confidence Distribution</h2>
          {a ? (
            <div className="space-y-2">
              {Object.entries(a.confidence_distribution).map(([level, count]) => (
                <SimpleBar
                  key={level}
                  label={level.replace('_', ' ')}
                  value={count}
                  max={maxConf}
                  color={
                    level === 'very_high' || level === 'high'
                      ? 'bg-emerald-500'
                      : level === 'medium'
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                  }
                />
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No confidence data yet.</p>
          )}
        </div>

        {/* Governance Outcomes */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">Governance Outcomes</h2>
          {a ? (
            <div className="space-y-2">
              <SimpleBar label="Passed" value={a.governance_outcomes.passed} max={a.total_events || 1} color="bg-emerald-500" />
              <SimpleBar label="Policy Violations" value={a.governance_outcomes.policy_violations} max={a.total_events || 1} color="bg-red-500" />
              <SimpleBar label="Toxicity Flagged" value={a.governance_outcomes.toxicity_flagged} max={a.total_events || 1} color="bg-red-400" />
              <SimpleBar label="Hallucination Flagged" value={a.governance_outcomes.hallucination_flagged} max={a.total_events || 1} color="bg-amber-500" />
            </div>
          ) : (
            <p className="text-xs text-slate-500">No governance data yet.</p>
          )}
        </div>

        {/* Latency Trend */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">Latency Trend (Last 20)</h2>
          {a && a.latency_trend.length > 0 ? (
            <div className="space-y-1">
              {a.latency_trend.map((point, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span className="w-32 shrink-0 truncate text-slate-500">
                    {point.timestamp.slice(11, 19)}
                  </span>
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-700">
                    <div
                      className="h-full rounded-full bg-cyan-500"
                      style={{ width: `${Math.min(100, point.latency * 50)}%` }}
                    />
                  </div>
                  <span className="w-12 text-right text-slate-400">{point.latency.toFixed(2)}s</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No latency data yet.</p>
          )}
        </div>
      </div>

      {/* Policy Violations */}
      {a && a.policy_violations.length > 0 && (
        <div className="mt-6 rounded-xl border border-slate-700/50 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">Recent Policy Violations</h2>
          <div className="space-y-2">
            {a.policy_violations.slice(0, 10).map((v, i) => (
              <div key={i} className="rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-red-300">{v.provider}</span>
                  <span className="text-slate-500">{v.timestamp.slice(11, 19)}</span>
                </div>
                <p className="mt-0.5 text-slate-400">{v.question}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conversation Volume */}
      {a && a.conversation_volume.length > 0 && (
        <div className="mt-6 rounded-xl border border-slate-700/50 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">Conversation Volume</h2>
          <div className="flex items-end gap-1" style={{ height: '80px' }}>
            {a.conversation_volume.map((point, i) => {
              const maxVol = Math.max(...a.conversation_volume.map((p) => p.count), 1);
              const height = (point.count / maxVol) * 100;
              return (
                <div
                  key={i}
                  className="flex-1 rounded-t bg-cyan-500/60 transition hover:bg-cyan-400"
                  style={{ height: `${height}%` }}
                  title={`${point.hour}: ${point.count} conversations`}
                />
              );
            })}
          </div>
          <p className="mt-2 text-xs text-slate-500">Conversations per hour</p>
        </div>
      )}
    </div>
  );
}