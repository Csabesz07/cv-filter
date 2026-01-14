import { useEffect, useMemo, useState } from "react";

import type { Route } from "./+types/files";

type Candidate = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
};

type CVFile = {
  id: string;
  candidate: Candidate;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  upload_status: string;
  uploaded_at: string;
  extracted_text: string;
  parsed_at: string | null;
};

type CVFileListResponse = {
  results?: CVFile[];
  detail?: string;
};

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Uploaded Files | CV Filter" },
    { name: "description", content: "Manage uploaded CV files." },
  ];
}

function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
  const value = bytes / Math.pow(1024, i);
  return `${value.toFixed(value >= 10 || i === 0 ? 0 : 1)} ${sizes[i]}`;
}

export default function Files() {
  const [files, setFiles] = useState<CVFile[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

  const accessToken = useMemo(() => {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem("access") || localStorage.getItem("access_token");
  }, []);

  const loadFiles = async () => {
    if (!accessToken) {
      setError("You need to sign in to view files.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/cv/files/", {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const contentType = response.headers.get("content-type") || "";
      let body: CVFileListResponse | null = null;
      if (contentType.includes("application/json")) {
        body = (await response.json()) as CVFileListResponse;
      }
      if (!response.ok) {
        setError(body?.detail || "Failed to load files.");
        return;
      }
      setFiles(body?.results || []);
    } catch {
      setError("Failed to load files.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadFiles();
  }, []);

  const selectedFile = files.find((file) => file.id === selectedId) || null;

  const handleDelete = async (cvFile: CVFile) => {
    if (!accessToken) {
      setError("You need to sign in to delete files.");
      return;
    }
    const confirmed = window.confirm(
      `Delete ${cvFile.original_filename}? This cannot be undone.`
    );
    if (!confirmed) {
      return;
    }
    setIsDeleting(cvFile.id);
    setError(null);
    try {
      const response = await fetch(`/api/cv/files/${cvFile.id}/`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) {
        setError("Failed to delete file.");
        return;
      }
      setFiles((prev) => prev.filter((item) => item.id !== cvFile.id));
      if (selectedId === cvFile.id) {
        setSelectedId(null);
      }
    } catch {
      setError("Failed to delete file.");
    } finally {
      setIsDeleting(null);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="mb-6">
          <h1 className="text-3xl font-semibold">Uploaded files</h1>
          <p className="text-sm text-slate-400">
            Review uploads, extracted text, and remove files.
          </p>
        </div>

        {error ? (
          <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            {error}
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Files</h2>
              <button
                type="button"
                onClick={() => loadFiles()}
                className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:border-emerald-400/70 hover:text-emerald-200"
                disabled={isLoading}
              >
                {isLoading ? "Refreshing..." : "Refresh"}
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {files.length === 0 && !isLoading ? (
                <div className="rounded-xl border border-dashed border-slate-800 px-4 py-6 text-center text-xs text-slate-500">
                  No files uploaded yet.
                </div>
              ) : null}

              {files.map((file) => (
                <div
                  key={file.id}
                  className={`rounded-xl border px-4 py-3 ${
                    selectedId === file.id
                      ? "border-emerald-400/60 bg-emerald-500/10"
                      : "border-slate-800 bg-slate-950/40"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold">
                        {file.original_filename}
                      </div>
                      <div className="text-xs text-slate-400">
                        {file.candidate.first_name} {file.candidate.last_name} •{" "}
                        {file.candidate.email}
                      </div>
                      <div className="text-xs text-slate-500">
                        {formatBytes(file.file_size_bytes)} • {file.mime_type}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <button
                        type="button"
                        onClick={() => setSelectedId(file.id)}
                        className="rounded-full border border-slate-700 px-3 py-1 text-slate-200 hover:border-emerald-400/70"
                      >
                        View
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(file)}
                        disabled={isDeleting === file.id}
                        className="rounded-full border border-rose-500/60 px-3 py-1 text-rose-100 hover:border-rose-400 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {isDeleting === file.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="text-lg font-semibold">Extracted text</h2>
            {selectedFile ? (
              <div className="mt-4 space-y-3">
                <div className="text-xs text-slate-400">
                  Parsed at:{" "}
                  <span className="text-slate-200">
                    {selectedFile.parsed_at || "Not parsed"}
                  </span>
                </div>
                <textarea
                  readOnly
                  value={selectedFile.extracted_text || ""}
                  className="h-80 w-full resize-none rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-xs text-slate-100"
                />
                {!selectedFile.extracted_text ? (
                  <p className="text-xs text-slate-400">
                    No extracted text stored for this file.
                  </p>
                ) : null}
              </div>
            ) : (
              <div className="mt-4 rounded-xl border border-dashed border-slate-800 px-4 py-6 text-center text-xs text-slate-500">
                Select a file to view extracted text.
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
