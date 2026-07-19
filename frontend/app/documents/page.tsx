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
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Core fetch function
  const fetchDocuments = useCallback(async () => {
    try {
      setError(null);
      const { data } = await axios.get(`${API}/documents/`);
      setDocuments(data as Document[]);
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Failed to fetch documents from database.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name.replace(/\.pdf$/i, ''));
      
      // FIX 1: Let Axios automatically generate the multipart boundary string
      // and keep the trailing slash for Django's route compliance.
      await axios.post(`${API}/documents/upload/`, formData);
      
      // FIX 2: Clear input values to allow re-uploading the same file name later
      if (fileInputRef.current) fileInputRef.current.value = '';
      
      // Refresh the database list and counter immediately
      await fetchDocuments();
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload file. Ensure your backend matches /api/documents/upload/');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    
    setError(null);
    try {
      // FIX 3: Matches standard DRF routing layout (requires trailing slash)
      // Endpoint maps directly to /api/documents/{id}/
      await axios.delete(`${API}/documents/${id}/`);
      
      // Optimistically clear local state, then refresh DB baseline counts
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      await fetchDocuments();
    } catch (err) {
      console.error('Delete failed:', err);
      setError('Failed to delete document. Ensure endpoint matches /api/documents/{id}/');
    }
  };

  const handleReprocess = async (id: string) => {
    setError(null);
    try {
      await axios.post(`${API}/documents/${id}/reprocess/`);
      await fetchDocuments();
    } catch (err) {
      console.error('Reprocess failed:', err);
      setError('Failed to reprocess document.');
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
      {/* Header with Counter Component */}
      <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold text-white">Document Management</h1>
          <p className="text-sm text-slate-400">
            Upload, manage, and reprocess PDF documents for the RAG pipeline.
          </p>
        </div>
        
        {/* Dynamic Database Count badge */}
        <div className="shrink-0 rounded-xl border border-slate-800 bg-slate-900/80 px-4 py-2.5 text-center">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Documents</div>
          <div className="text-xl font-bold text-cyan-400">
            {loading ? '...' : documents.length}
          </div>
        </div>
      </div>

      {/* Global Context Error Alert */}
      {error && (
        <div className="mb-6 rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-sm text-red-400">
          ⚠️ {error}
        </div>
      )}

      {/* Upload Area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`mb-8 cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition ${
          uploading ? 'pointer-events-none opacity-60 border-slate-700 bg-slate-900/20' :
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
          disabled={uploading}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleUpload(file);
          }}
        />
        <div className="text-3xl">{uploading ? '⏳' : '📄'}</div>
        <p className="mt-2 text-sm font-medium text-slate-300">
          {uploading ? 'Uploading & Indexing document...' : 'Drop a PDF here or click to upload'}
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
          className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-slate-600"
        />
      </div>

      {/* Document List */}
      {loading ? (
        <div className="text-center text-sm text-slate-400 py-12">Loading documents...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center text-sm text-slate-400 py-12 border border-dashed border-slate-800 rounded-xl">
          {searchQuery ? 'No documents match your search query.' : 'No documents found in database.'}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((doc) => (
            <div
              key={doc.id}
              className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-4 transition hover:border-slate-600 flex flex-col justify-between"
            >
              <div>
                <div className="mb-3 flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="truncate text-sm font-semibold text-slate-200" title={doc.title}>
                      {doc.title}
                    </h3>
                    <p className="truncate text-xs text-slate-500" title={doc.filename}>
                      {doc.filename}
                    </p>
                  </div>
                  <span
                    className={`ml-2 shrink-0 rounded-full px-2 py-0.5 text-xs font-medium uppercase tracking-tight ${
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

                <div className="mb-4 space-y-1 text-xs text-slate-400">
                  <div className="flex justify-between">
                    <span>Size</span>
                    <span className="text-slate-300 font-medium">{formatFileSize(doc.file_size)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Chunks</span>
                    <span className="text-slate-300 font-medium">{doc.chunk_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Uploaded</span>
                    <span className="text-slate-300 font-medium">{formatDate(doc.upload_date)}</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 mt-auto pt-2">
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