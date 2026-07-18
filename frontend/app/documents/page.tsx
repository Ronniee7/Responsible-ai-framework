'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';

interface Document {
  id: string;
  title: string;
  filename: string;
  file_size: number | null;
  status: string;
  upload_date: string;
  chunk_count: number;
}

const API = 'http://127.0.0.1:8000/api';

function formatFileSize(bytes: number | null): string {
  if (!bytes) return 'Unknown';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/documents/`);
      setDocuments(data as Document[]);
    } catch {
      // Silently handle
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name.replace(/\.pdf$/i, ''));
      await axios.post(`${API}/documents/upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await fetchDocuments();
    } catch {
      // Silently handle
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await axios.delete(`${API}/documents/${id}/`);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch {
      // Silently handle
    }
  };

  const handleReprocess = async (id: string) => {
    try {
      await axios.post(`${API}/documents/${id}/reprocess/`);
      await fetchDocuments();
    } catch {
      // Silently handle
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.toLowerCase().endsWith('.pdf')) {
      handleUpload(file);
    }
  };

  const filtered = documents.filter(
    (doc) =>
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-8 space-y-4">
        <h1 className="text-2xl font-semibold text-white">Document Management</h1>
        <p className="text-sm text-slate-400">
          Upload, manage, and reprocess PDF documents for the RAG pipeline.
        </p>
      </div>

      {/* Upload Area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`mb-8 cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition ${
          dragOver
            ? 'border-cyan-400 bg-cyan-400/5'
            : 'border-slate-700 bg-slate-900/50 hover:border-slate-500'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleUpload(file);
          }}
        />
        <div className="text-3xl">📄</div>
        <p className="mt-2 text-sm font-medium text-slate-300">
          {uploading ? 'Uploading...' : 'Drop a PDF here or click to upload'}
        </p>
        <p className="mt-1 text-xs text-slate-500">Only PDF files are supported</p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search documents by title or filename..."
          className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 outline-none placeholder:text-slate-500"
        />
      </div>

      {/* Document List */}
      {loading ? (
        <div className="text-center text-sm text-slate-400">Loading documents...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center text-sm text-slate-400">
          {searchQuery ? 'No documents match your search.' : 'No documents uploaded yet.'}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((doc) => (
            <div
              key={doc.id}
              className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-4 transition hover:border-slate-600"
            >
              <div className="mb-3 flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="truncate text-sm font-semibold text-slate-200">{doc.title}</h3>
                  <p className="truncate text-xs text-slate-500">{doc.filename}</p>
                </div>
                <span
                  className={`ml-2 shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                    doc.status === 'ready'
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : doc.status === 'processing'
                      ? 'bg-amber-500/20 text-amber-300'
                      : 'bg-red-500/20 text-red-300'
                  }`}
                >
                  {doc.status}
                </span>
              </div>

              <div className="mb-3 space-y-1 text-xs text-slate-400">
                <div className="flex justify-between">
                  <span>Size</span>
                  <span>{formatFileSize(doc.file_size)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Chunks</span>
                  <span>{doc.chunk_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Uploaded</span>
                  <span>{formatDate(doc.upload_date)}</span>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleReprocess(doc.id)}
                  className="flex-1 rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-700"
                >
                  Re-index
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(doc.id)}
                  className="rounded-lg bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-300 transition hover:bg-red-500/20"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}