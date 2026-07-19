'use client';

import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';

const API = 'http://127.0.0.1:8000/api';

interface ReviewItem {
  id: string;
  question: string;
  retrieved_chunks: Record<string, unknown>[];
  ai_response: string;
  edited_response: string;
  governance_metrics: Record<string, unknown>;
  reviewer_comments: string;
  status: string;
  created_at: string;
  updated_at: string;
  reviewed_by: string;
  reviewed_at: string | null;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    approved: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    rejected: 'bg-red-500/20 text-red-300 border-red-500/30',
    edited: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  };
  const cls = colors[status] || 'bg-slate-500/20 text-slate-300 border-slate-500/30';
  return (
    <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${cls}`}>
      {status}
    </span>
  );
}

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchReviews = useCallback(async () => {
    try {
      setError(null);
      const url = statusFilter
        ? `${API}/governance/reviews/?status=${statusFilter}`
        : `${API}/governance/reviews/`;
      const { data } = await axios.get(url);
      setReviews(data as ReviewItem[]);
    } catch {
      setError('Failed to fetch reviews.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  const handleAction = async (id: string, action: string, comments?: string, editedResponse?: string) => {
    setActionLoading(id);
    try {
      await axios.post(`${API}/governance/reviews/${id}/action/`, {
        action,
        reviewer_comments: comments || '',
        edited_response: editedResponse || '',
        reviewed_by: 'frontend_user',
      });
      await fetchReviews();
      setExpandedId(null);
    } catch {
      setError('Failed to process review action.');
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold text-white">Human Review</h1>
          <p className="text-sm text-slate-400">
            Review, approve, reject, or edit AI responses flagged by the governance pipeline.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-300 outline-none"
          >
            <option value="">All Reviews</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="edited">Edited</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">
          ⚠️ {error}
        </div>
      )}

      {loading ? (
        <div className="text-center text-sm text-slate-400 py-12">Loading reviews...</div>
      ) : reviews.length === 0 ? (
        <div className="text-center text-sm text-slate-400 py-12 border border-dashed border-slate-800 rounded-xl">
          {statusFilter ? `No ${statusFilter} reviews found.` : 'No reviews found. The governance pipeline will create review items when responses need human oversight.'}
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div
              key={review.id}
              className="rounded-xl border border-slate-700/50 bg-slate-900/60 overflow-hidden"
            >
              {/* Summary Header */}
              <button
                type="button"
                onClick={() => setExpandedId(expandedId === review.id ? null : review.id)}
                className="flex w-full items-center justify-between px-4 py-3 text-left transition hover:bg-slate-800/50"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <StatusBadge status={review.status} />
                  <span className="truncate text-sm font-medium text-slate-200">
                    {review.question}
                  </span>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs text-slate-500">{formatDate(review.created_at)}</span>
                  <svg
                    className={`h-4 w-4 text-slate-400 transition ${expandedId === review.id ? 'rotate-180' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              {/* Expanded Details */}
              {expandedId === review.id && (
                <div className="border-t border-slate-700/30 px-4 py-4 space-y-4">
                  {/* Question */}
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Question</p>
                    <p className="text-sm text-slate-200">{review.question}</p>
                  </div>

                  {/* AI Response */}
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">AI Response</p>
                    <div className="rounded-lg bg-slate-800/50 p-3 text-sm text-slate-200 whitespace-pre-line">
                      {review.ai_response}
                    </div>
                  </div>

                  {/* Governance Metrics */}
                  {review.governance_metrics && Object.keys(review.governance_metrics).length > 0 && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Governance Metrics</p>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {Object.entries(review.governance_metrics).map(([key, value]) => (
                          <div key={key} className="rounded-lg bg-slate-800/40 px-3 py-2 text-xs">
                            <span className="text-slate-400">{key.replace(/_/g, ' ')}</span>
                            <span className="ml-2 font-mono text-slate-200">
                              {typeof value === 'number' ? value.toFixed(3) : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Retrieved Chunks */}
                  {review.retrieved_chunks && review.retrieved_chunks.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                        Retrieved Chunks ({review.retrieved_chunks.length})
                      </p>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {review.retrieved_chunks.map((chunk, i) => (
                          <div key={i} className="rounded-lg bg-slate-800/30 p-2 text-xs text-slate-400">
                            <div className="flex gap-2 mb-1">
                              <span className="text-cyan-300">Score: {(chunk as Record<string, unknown>).score as number ?? 'N/A'}</span>
                              <span className="text-slate-500">Source: {(chunk as Record<string, unknown>).source as string ?? 'Unknown'}</span>
                              <span className="text-slate-500">Page: {(chunk as Record<string, unknown>).page as string ?? '?'}</span>
                            </div>
                            <p>{(chunk as Record<string, unknown>).content as string ?? ''}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Reviewer Comments */}
                  {review.reviewer_comments && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Reviewer Comments</p>
                      <p className="text-sm text-slate-300">{review.reviewer_comments}</p>
                    </div>
                  )}

                  {/* Action Buttons (only for pending) */}
                  {review.status === 'pending' && (
                    <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-700/30">
                      <button
                        type="button"
                        disabled={actionLoading === review.id}
                        onClick={() => handleAction(review.id, 'approved', 'Approved via frontend.')}
                        className="rounded-lg bg-emerald-500/20 px-4 py-2 text-xs font-medium text-emerald-300 transition hover:bg-emerald-500/30 disabled:opacity-50"
                      >
                        {actionLoading === review.id ? 'Processing...' : 'Approve'}
                      </button>
                      <button
                        type="button"
                        disabled={actionLoading === review.id}
                        onClick={() => handleAction(review.id, 'rejected', 'Rejected via frontend.')}
                        className="rounded-lg bg-red-500/20 px-4 py-2 text-xs font-medium text-red-300 transition hover:bg-red-500/30 disabled:opacity-50"
                      >
                        {actionLoading === review.id ? 'Processing...' : 'Reject'}
                      </button>
                      <button
                        type="button"
                        disabled={actionLoading === review.id}
                        onClick={() => {
                          const edited = window.prompt('Edit the response:', review.ai_response);
                          if (edited && edited !== review.ai_response) {
                            handleAction(review.id, 'edited', 'Edited via frontend.', edited);
                          }
                        }}
                        className="rounded-lg bg-blue-500/20 px-4 py-2 text-xs font-medium text-blue-300 transition hover:bg-blue-500/30 disabled:opacity-50"
                      >
                        {actionLoading === review.id ? 'Processing...' : 'Edit Response'}
                      </button>
                    </div>
                  )}

                  {/* Show edited response if available */}
                  {review.edited_response && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-1">Edited Response</p>
                      <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-3 text-sm text-slate-200 whitespace-pre-line">
                        {review.edited_response}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}