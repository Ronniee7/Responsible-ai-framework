'use client';

import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

const API = 'http://127.0.0.1:8000/api';

interface Settings {
  provider: string;
  model: Record<string, string>;
  temperature: number;
  max_tokens: number;
  governance_thresholds: {
    hallucination_threshold: number;
    bias_threshold: number;
    toxicity_threshold: number;
    confidence_threshold: number;
  };
}

const PROVIDERS = [
  { id: 'openai', label: 'OpenAI' },
  { id: 'gemini', label: 'Google Gemini' },
  { id: 'ollama', label: 'Ollama' },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/settings/`);
      setSettings(data as Settings);
    } catch {
      // Silently handle
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSave = async () => {
    if (!settings) return;
    setSaving(true);
    setSaved(false);
    try {
      await axios.post(`${API}/settings/`, settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // Silently handle
    } finally {
      setSaving(false);
    }
  };

  const updateThreshold = (key: string, value: number) => {
    if (!settings) return;
    setSettings({
      ...settings,
      governance_thresholds: {
        ...settings.governance_thresholds,
        [key]: value,
      },
    });
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-8 text-center text-sm text-slate-400">
        Loading settings...
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-8 text-center text-sm text-slate-400">
        Could not load settings.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <div className="mb-8 space-y-4">
        <h1 className="text-2xl font-semibold text-white">Settings</h1>
        <p className="text-sm text-slate-400">
          Configure LLM provider, model parameters, and governance thresholds.
        </p>
      </div>

      <div className="space-y-6">
        {/* Provider Selection */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-5">
          <h2 className="mb-4 text-sm font-semibold text-slate-200">LLM Provider</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {PROVIDERS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setSettings({ ...settings, provider: p.id })}
                className={`rounded-xl border p-3 text-left text-sm transition ${
                  settings.provider === p.id
                    ? 'border-cyan-400 bg-slate-800 shadow-lg shadow-cyan-500/10'
                    : 'border-slate-700 bg-slate-950/70 hover:border-slate-500'
                }`}
              >
                <div className="font-semibold text-white">{p.label}</div>
                <div className="mt-1 text-xs text-slate-400">
                  Model: {settings.model[p.id] || 'Default'}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Model Parameters */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-5">
          <h2 className="mb-4 text-sm font-semibold text-slate-200">Model Parameters</h2>
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-400">Temperature</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={settings.temperature}
                  onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
                  className="flex-1 accent-cyan-500"
                />
                <span className="w-10 text-right text-sm font-mono text-slate-300">
                  {settings.temperature.toFixed(1)}
                </span>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-400">Max Tokens</label>
              <input
                type="number"
                min="64"
                max="8192"
                step="64"
                value={settings.max_tokens}
                onChange={(e) => setSettings({ ...settings, max_tokens: parseInt(e.target.value) || 1024 })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none"
              />
            </div>
          </div>
        </div>

        {/* Governance Thresholds */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-5">
          <h2 className="mb-4 text-sm font-semibold text-slate-200">Governance Thresholds</h2>
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-400">
                Hallucination Threshold: {settings.governance_thresholds.hallucination_threshold.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={settings.governance_thresholds.hallucination_threshold}
                onChange={(e) => updateThreshold('hallucination_threshold', parseFloat(e.target.value))}
                className="w-full accent-cyan-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-400">
                Bias Threshold: {settings.governance_thresholds.bias_threshold.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={settings.governance_thresholds.bias_threshold}
                onChange={(e) => updateThreshold('bias_threshold', parseFloat(e.target.value))}
                className="w-full accent-cyan-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-400">
                Toxicity Threshold: {settings.governance_thresholds.toxicity_threshold.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={settings.governance_thresholds.toxicity_threshold}
                onChange={(e) => updateThreshold('toxicity_threshold', parseFloat(e.target.value))}
                className="w-full accent-cyan-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-400">
                Confidence Threshold: {settings.governance_thresholds.confidence_threshold.toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={settings.governance_thresholds.confidence_threshold}
                onChange={(e) => updateThreshold('confidence_threshold', parseFloat(e.target.value))}
                className="w-full accent-cyan-500"
              />
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="rounded-full bg-cyan-500 px-6 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-70"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
          {saved && (
            <span className="text-sm text-emerald-400">Settings saved successfully.</span>
          )}
        </div>
      </div>
    </div>
  );
}