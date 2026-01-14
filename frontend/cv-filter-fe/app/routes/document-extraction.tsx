import { useMemo, useState } from "react";

import type { Route } from "./+types/document-extraction";

type ExtractResponse = {
  success?: boolean;
  extracted_text?: string;
  metadata?: Record<string, string | number | boolean | null>;
  method?: string;
  output_file?: string | null;
  error?: string;
};

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Document Extraction | CV Filter" },
    { name: "description", content: "Extract text from CV documents." },
  ];
}

const MAX_FILE_BYTES = 50 * 1024 * 1024;
const ALLOWED_EXTS = [".pdf", ".doc", ".docx"];

function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
  const value = bytes / Math.pow(1024, i);
  return `${value.toFixed(value >= 10 || i === 0 ? 0 : 1)} ${sizes[i]}`;
}

function isLikelyUrl(value: string) {
  return /^https?:\/\//i.test(value);
}

export default function DocumentExtraction() {
  const [file, setFile] = useState<File | null>(null);
  const [timeoutSeconds, setTimeoutSeconds] = useState(30);
  const [saveToFile, setSaveToFile] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const tokenWarning = useMemo(() => {
    if (typeof window === "undefined") return false;
    return !localStorage.getItem("access_token");
  }, []);

  const fileInfo = file
    ? `${file.name} • ${formatBytes(file.size)}`
    : "No file selected";

  const handleFile = (selected: File | null) => {
    setError(null);
    setResult(null);
    setFile(selected);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const dropped = event.dataTransfer.files?.[0] || null;
    handleFile(dropped);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setIsSubmitting(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("timeout_seconds", String(timeoutSeconds));
    formData.append("save_to_file", saveToFile ? "true" : "false");

    const headers: HeadersInit = {};
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch("/api/cv/upload/", {
        method: "POST",
        headers,
        body: formData,
      });

      const contentType = response.headers.get("content-type") || "";
      let body: ExtractResponse | null = null;

      if (contentType.includes("application/json")) {
        body = (await response.json()) as ExtractResponse;
      } else {
        const text = await response.text();
        if (!response.ok) {
          setError(text || "Unexpected server error.");
          return;
        }
        body = { success: true, extracted_text: text };
      }

      if (!response.ok || body?.success === false) {
        setError(body?.error || "Extraction failed.");
        setResult(body);
        return;
      }

      setResult(body);
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const canSubmit = file && file.size <= MAX_FILE_BYTES;

  const handleDownload = () => {
    if (!result?.output_file) return;
    const output = result.output_file;
    if (isLikelyUrl(output)) {
      window.open(output, "_blank", "noopener,noreferrer");
      return;
    }
    const text = result.extracted_text || "";
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "extracted-text.txt";
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCopyError = async () => {
    if (!error) return;
    try {
      await navigator.clipboard.writeText(error);
    } catch {
      // ignore clipboard errors
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-5xl px-4 py-10">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold">CV Extractor</h1>
            <p className="text-sm text-slate-400">
              Upload a CV and extract structured text in one shot.
            </p>
          </div>
        </div>

        {tokenWarning ? (
          <div className="mb-6 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
            Not logged in. Extraction may be limited.
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="space-y-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div>
              <h2 className="text-lg font-semibold">Upload</h2>
              <p className="text-sm text-slate-400">
                Drag and drop a CV file or browse to upload.
              </p>
            </div>

            <div
              className={`rounded-2xl border-2 border-dashed px-6 py-8 transition ${
                isDragging
                  ? "border-emerald-400/70 bg-emerald-500/10"
                  : "border-slate-700 bg-slate-950/60"
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <input
                id="file-input"
                type="file"
                className="hidden"
                accept={ALLOWED_EXTS.join(",")}
                onChange={(event) => handleFile(event.target.files?.[0] || null)}
              />
              <label
                htmlFor="file-input"
                className="flex cursor-pointer flex-col items-center gap-2 text-center"
              >
                <span className="text-sm font-medium text-slate-200">
                  Drop file here or click to browse
                </span>
                <span className="text-xs text-slate-400">{fileInfo}</span>
              </label>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-3 text-xs text-slate-400">
              Allowed: .pdf, .doc, .docx • Max size: 50 MB
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-200">
                  Timeout seconds
                </label>
                <input
                  type="number"
                  min={5}
                  max={300}
                  value={timeoutSeconds}
                  onChange={(event) =>
                    setTimeoutSeconds(Number(event.target.value))
                  }
                  className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-400"
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-200">
                <input
                  type="checkbox"
                  checked={saveToFile}
                  onChange={(event) => setSaveToFile(event.target.checked)}
                  className="h-4 w-4 accent-emerald-400"
                />
                Save extracted text to file
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                disabled={!canSubmit || isSubmitting}
                onClick={handleSubmit}
                className="rounded-xl bg-emerald-400 px-5 py-2 text-sm font-semibold text-slate-900 transition enabled:hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? "Extracting..." : "Extract"}
              </button>
              {file && file.size > MAX_FILE_BYTES ? (
                <span className="text-xs text-rose-300">
                  File is too large.
                </span>
              ) : null}
            </div>
          </section>

          <section className="space-y-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div>
              <h2 className="text-lg font-semibold">Results</h2>
              <p className="text-sm text-slate-400">
                Extraction output, metadata, and method info.
              </p>
            </div>

            {error ? (
              <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                <div className="mb-2 font-semibold">Error</div>
                <div className="whitespace-pre-wrap text-xs text-rose-100/90">
                  {error}
                </div>
                <button
                  type="button"
                  onClick={handleCopyError}
                  className="mt-3 rounded-lg border border-rose-400/50 px-3 py-1 text-xs text-rose-100 hover:border-rose-300"
                >
                  Copy error
                </button>
              </div>
            ) : null}

            {result ? (
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Extracted text
                  </label>
                  <textarea
                    readOnly
                    value={result.extracted_text || ""}
                    className="mt-2 h-48 w-full resize-none rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-xs text-slate-100"
                  />
                </div>

                <div className="space-y-2 text-sm">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Metadata
                  </div>
                  <div className="overflow-hidden rounded-xl border border-slate-800">
                    <table className="w-full text-left text-xs">
                      <tbody>
                        {result.metadata
                          ? Object.entries(result.metadata).map(([key, value]) => (
                              <tr key={key} className="border-b border-slate-800 last:border-none">
                                <td className="px-3 py-2 font-medium text-slate-200">
                                  {key}
                                </td>
                                <td className="px-3 py-2 text-slate-400">
                                  {value === null ? "-" : String(value)}
                                </td>
                              </tr>
                            ))
                          : (
                            <tr>
                              <td className="px-3 py-2 text-slate-400">
                                No metadata
                              </td>
                              <td className="px-3 py-2 text-slate-400" />
                            </tr>
                          )}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="text-xs text-slate-400">
                  Method: <span className="text-slate-200">{result.method || "-"}</span>
                </div>

                {result.output_file ? (
                  <button
                    type="button"
                    onClick={handleDownload}
                    className="rounded-xl border border-emerald-400/60 px-4 py-2 text-xs font-semibold text-emerald-200 hover:border-emerald-300"
                  >
                    Download extracted text
                  </button>
                ) : null}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-800 px-4 py-6 text-center text-xs text-slate-500">
                Run an extraction to see results here.
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
