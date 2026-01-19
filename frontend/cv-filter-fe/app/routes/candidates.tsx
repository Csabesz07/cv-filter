import { useEffect, useMemo, useState } from "react";

import type { Route } from "./+types/candidates";

type CandidateResponse = {
  candidate?: {
    id?: string;
    first_name?: string;
    last_name?: string;
    email?: string;
  };
  detail?: string;
};

type Candidate = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
};

type CandidateListResponse = {
  results?: Candidate[];
  detail?: string;
};

type CVFile = {
  id: string;
  candidate: Candidate;
  extracted_text: string;
  parsed_at: string | null;
  original_filename: string;
};

type CVFileListResponse = {
  results?: CVFile[];
  detail?: string;
};

type StructuredData = {
  id: string;
  candidate_id: string;
  candidate_name: string;
  structured_json: {
    email?: string;
    phone?: string;
    linkedin?: string;
    github?: string;
    websites?: string[];
    programming_languages?: string[];
    frameworks?: string[];
    databases?: string[];
    tools?: string[];
    cloud_platforms?: string[];
    soft_skills?: string[];
    languages?: string[];
    degrees?: string[];
    certifications?: string[];
    job_titles?: string[];
  };
  headline: string | null;
  primary_location: string | null;
  top_skills: string | null;
  experience_years: number | null;
  created_at: string;
};

type StructuredDataResponse = {
  detail?: string;
} & Partial<StructuredData>;

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Candidates | CV Filter" },
    { name: "description", content: "Register and review candidates." },
  ];
}

export default function Candidates() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [files, setFiles] = useState<CVFile[]>([]);
  const [structuredData, setStructuredData] = useState<Map<string, StructuredData>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(
    null
  );

  const accessToken = useMemo(() => {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem("access") || localStorage.getItem("access_token");
  }, []);

  const fetchCandidates = async () => {
    if (!accessToken) {
      setLoadError("You need to sign in to view candidates.");
      return;
    }
    const response = await fetch("/api/candidates/", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const contentType = response.headers.get("content-type") || "";
    let body: CandidateListResponse | null = null;
    if (contentType.includes("application/json")) {
      body = (await response.json()) as CandidateListResponse;
    }
    if (!response.ok) {
      throw new Error(body?.detail || "Failed to load candidates.");
    }
    setCandidates(body?.results || []);
  };

  const fetchFiles = async () => {
    if (!accessToken) {
      return;
    }
    const response = await fetch("/api/cv/files/", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const contentType = response.headers.get("content-type") || "";
    let body: CVFileListResponse | null = null;
    if (contentType.includes("application/json")) {
      body = (await response.json()) as CVFileListResponse;
    }
    if (!response.ok) {
      throw new Error(body?.detail || "Failed to load extracted text.");
    }
    setFiles(body?.results || []);
  };

  const fetchStructuredData = async (candidateId: string) => {
    if (!accessToken) {
      return;
    }
    try {
      const response = await fetch(`/api/candidates/${candidateId}/structured/`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const contentType = response.headers.get("content-type") || "";
      let body: StructuredDataResponse | null = null;
      if (contentType.includes("application/json")) {
        body = (await response.json()) as StructuredDataResponse;
      }
      if (response.ok && body?.id) {
        setStructuredData(prev => new Map(prev).set(candidateId, body as StructuredData));
      }
    } catch {
      // Ignore errors for structured data - it's optional
    }
  };

  const loadData = async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      await Promise.all([fetchCandidates(), fetchFiles()]);
    } catch (loadErr) {
      setLoadError(
        loadErr instanceof Error ? loadErr.message : "Failed to load candidates."
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  // Fetch structured data when candidates change
  useEffect(() => {
    if (accessToken && candidates.length > 0) {
      candidates.forEach(candidate => {
        if (!structuredData.has(candidate.id)) {
          void fetchStructuredData(candidate.id);
        }
      });
    }
  }, [candidates, accessToken]);

  const candidateSummaries = useMemo(() => {
    const map = new Map<
      string,
      {
        combinedText: string;
        latestText: string;
        parsedAt: string | null;
        count: number;
      }
    >();

    const byCandidate = new Map<string, CVFile[]>();
    for (const file of files) {
      const candidateId = file.candidate?.id;
      if (!candidateId) continue;
      const bucket = byCandidate.get(candidateId) || [];
      bucket.push(file);
      byCandidate.set(candidateId, bucket);
    }

    for (const [candidateId, bucket] of byCandidate.entries()) {
      const texts = bucket.map((file) => file.extracted_text || "").filter(Boolean);
      const combinedText = texts.join("\n\n");
      const latestFile = bucket
        .slice()
        .sort((a, b) => {
          const aTime = a.parsed_at ? Date.parse(a.parsed_at) : 0;
          const bTime = b.parsed_at ? Date.parse(b.parsed_at) : 0;
          return bTime - aTime;
        })[0];
      map.set(candidateId, {
        combinedText,
        latestText: latestFile?.extracted_text || "",
        parsedAt: latestFile?.parsed_at || null,
        count: bucket.length,
      });
    }

    return candidates.map((candidate) => {
      const summary = map.get(candidate.id);
      return {
        candidate,
        combinedText: summary?.combinedText || "",
        latestText: summary?.latestText || "",
        parsedAt: summary?.parsedAt || null,
        count: summary?.count || 0,
      };
    });
  }, [candidates, files]);

  const filteredCandidates = useMemo(() => {
    const term = searchQuery.trim().toLowerCase();
    if (!term) return candidateSummaries;
    return candidateSummaries.filter((entry) => {
      const name = `${entry.candidate.first_name} ${entry.candidate.last_name}`.trim();
      const haystack = `${name} ${entry.candidate.email} ${entry.combinedText}`.toLowerCase();
      return haystack.includes(term);
    });
  }, [candidateSummaries, searchQuery]);

  useEffect(() => {
    if (!selectedCandidateId && filteredCandidates.length) {
      setSelectedCandidateId(filteredCandidates[0].candidate.id);
      return;
    }
    if (
      selectedCandidateId &&
      !filteredCandidates.some((entry) => entry.candidate.id === selectedCandidateId)
    ) {
      setSelectedCandidateId(filteredCandidates[0]?.candidate.id || null);
    }
  }, [filteredCandidates, selectedCandidateId]);

  const selectedCandidate =
    filteredCandidates.find((entry) => entry.candidate.id === selectedCandidateId) ||
    null;

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage(null);
    setError(null);

    if (!accessToken) {
      setError("You need to sign in to create a candidate.");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/candidates/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          email: email.trim(),
        }),
      });

      const contentType = response.headers.get("content-type") || "";
      let body: CandidateResponse | null = null;
      if (contentType.includes("application/json")) {
        body = (await response.json()) as CandidateResponse;
      }

      if (!response.ok) {
        setError(body?.detail || "Failed to create candidate.");
        return;
      }

      setMessage("Candidate created.");
      setFirstName("");
      setLastName("");
      setEmail("");
      await fetchCandidates();
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteCandidate = async (candidateId: string) => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      // Handle case where user is not authenticated
      return;
    }

    try {
      const response = await fetch(`/api/candidates/${candidateId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        // On successful deletion, refresh the candidate list
        loadData();
        setSelectedCandidateId(null);
      } else {
        // Handle error
        console.error('Failed to delete candidate');
      }
    } catch (error) {
      console.error('An error occurred while deleting the candidate:', error);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="mb-6">
          <h1 className="text-3xl font-semibold">Candidates</h1>
          <p className="text-sm text-slate-400">
            Register candidates, browse extracted CV text, and search by keywords.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="mb-4">
                <h2 className="text-lg font-semibold">Candidate registration</h2>
                <p className="text-sm text-slate-400">
                  Add a candidate by name and email.
                </p>
              </div>
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label className="text-sm font-medium text-slate-200">
                    First name
                  </label>
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-400"
                    value={firstName}
                    onChange={(event) => setFirstName(event.target.value)}
                    placeholder="Jane"
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-200">
                    Last name
                  </label>
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-400"
                    value={lastName}
                    onChange={(event) => setLastName(event.target.value)}
                    placeholder="Doe"
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-200">Email</label>
                  <input
                    type="email"
                    className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-400"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="jane@example.com"
                    required
                  />
                </div>

                {message ? (
                  <div className="rounded-xl border border-emerald-400/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                    {message}
                  </div>
                ) : null}
                {error ? (
                  <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                    {error}
                  </div>
                ) : null}

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-xl bg-emerald-400 px-5 py-2 text-sm font-semibold text-slate-900 transition enabled:hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? "Saving..." : "Create candidate"}
                </button>
              </form>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">Candidate list</h2>
                  <p className="text-sm text-slate-400">
                    Search across names and extracted CV text.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => loadData()}
                  className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300 hover:border-emerald-400/70 hover:text-emerald-200"
                  disabled={isLoading}
                >
                  {isLoading ? "Refreshing..." : "Refresh"}
                </button>
              </div>

              {loadError ? (
                <div className="mt-4 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                  {loadError}
                </div>
              ) : null}

              <div className="mt-4">
                <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Search candidates
                </label>
                <input
                  className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-400"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Search by name or extracted text"
                />
              </div>

              <div className="mt-4 space-y-3">
                {filteredCandidates.length === 0 && !isLoading ? (
                  <div className="rounded-xl border border-dashed border-slate-800 px-4 py-6 text-center text-xs text-slate-500">
                    No candidates found.
                  </div>
                ) : null}

                {filteredCandidates.map((entry) => {
                  const name = `${entry.candidate.first_name} ${entry.candidate.last_name}`.trim();
                  return (
                    <button
                      key={entry.candidate.id}
                      type="button"
                      onClick={() => setSelectedCandidateId(entry.candidate.id)}
                      className={`w-full rounded-xl border px-4 py-3 text-left transition ${
                        selectedCandidateId === entry.candidate.id
                          ? "border-emerald-400/60 bg-emerald-500/10"
                          : "border-slate-800 bg-slate-950/40 hover:border-slate-700"
                      }`}
                    >
                      <div className="text-sm font-semibold text-slate-100">
                        {name || entry.candidate.email}
                      </div>
                      <div className="text-xs text-slate-400">
                        {entry.candidate.email}
                      </div>
                      <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
                        <span>CVs: {entry.count}</span>
                        <span>
                          Parsed:{" "}
                          {entry.parsedAt
                            ? new Date(entry.parsedAt).toLocaleString()
                            : "Not parsed"}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          <section className="space-y-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="mb-4">
                <h2 className="text-lg font-semibold">Extracted Skills & Data</h2>
                <p className="text-sm text-slate-400">
                  Structured information extracted from CV.
                </p>
              </div>

              {selectedCandidate ? (
                <div className="space-y-4">
                  {(() => {
                    const data = structuredData.get(selectedCandidate.candidate.id);
                    if (!data) {
                      return (
                        <div className="rounded-xl border border-dashed border-slate-800 px-4 py-6 text-center text-xs text-slate-500">
                          No structured data available. Upload a CV to extract entities.
                        </div>
                      );
                    }

                    const { structured_json, headline, top_skills } = data;

                    return (
                      <>
                        {headline && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Headline
                            </label>
                            <div className="mt-1 text-sm text-slate-200">{headline}</div>
                          </div>
                        )}

                        {top_skills && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Top Skills
                            </label>
                            <div className="mt-1 text-sm text-slate-200">{top_skills}</div>
                          </div>
                        )}

                        {structured_json.programming_languages && structured_json.programming_languages.length > 0 && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Programming Languages
                            </label>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {structured_json.programming_languages.map((lang, idx) => (
                                <span
                                  key={idx}
                                  className="rounded-lg bg-emerald-500/20 px-2 py-1 text-xs text-emerald-200"
                                >
                                  {lang}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {structured_json.frameworks && structured_json.frameworks.length > 0 && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Frameworks
                            </label>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {structured_json.frameworks.map((fw, idx) => (
                                <span
                                  key={idx}
                                  className="rounded-lg bg-blue-500/20 px-2 py-1 text-xs text-blue-200"
                                >
                                  {fw}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {structured_json.databases && structured_json.databases.length > 0 && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Databases
                            </label>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {structured_json.databases.map((db, idx) => (
                                <span
                                  key={idx}
                                  className="rounded-lg bg-purple-500/20 px-2 py-1 text-xs text-purple-200"
                                >
                                  {db}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {structured_json.tools && structured_json.tools.length > 0 && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Tools
                            </label>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {structured_json.tools.map((tool, idx) => (
                                <span
                                  key={idx}
                                  className="rounded-lg bg-amber-500/20 px-2 py-1 text-xs text-amber-200"
                                >
                                  {tool}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {structured_json.cloud_platforms && structured_json.cloud_platforms.length > 0 && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Cloud Platforms
                            </label>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {structured_json.cloud_platforms.map((cloud, idx) => (
                                <span
                                  key={idx}
                                  className="rounded-lg bg-sky-500/20 px-2 py-1 text-xs text-sky-200"
                                >
                                  {cloud}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {structured_json.degrees && structured_json.degrees.length > 0 && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Education
                            </label>
                            <div className="mt-2 space-y-1">
                              {structured_json.degrees.map((degree, idx) => (
                                <div key={idx} className="text-sm text-slate-200">
                                  • {degree}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {structured_json.certifications && structured_json.certifications.length > 0 && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Certifications
                            </label>
                            <div className="mt-2 space-y-1">
                              {structured_json.certifications.map((cert, idx) => (
                                <div key={idx} className="text-sm text-slate-200">
                                  • {cert}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {structured_json.job_titles && structured_json.job_titles.length > 0 && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Job Titles
                            </label>
                            <div className="mt-2 space-y-1">
                              {structured_json.job_titles.map((title, idx) => (
                                <div key={idx} className="text-sm text-slate-200">
                                  • {title}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {structured_json.languages && structured_json.languages.length > 0 && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Languages
                            </label>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {structured_json.languages.map((lang, idx) => (
                                <span
                                  key={idx}
                                  className="rounded-lg bg-slate-700 px-2 py-1 text-xs text-slate-200"
                                >
                                  {lang}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {structured_json.email && (
                          <div>
                            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Contact
                            </label>
                            <div className="mt-1 space-y-1 text-sm text-slate-200">
                              {structured_json.email && <div>📧 {structured_json.email}</div>}
                              {structured_json.phone && <div>📱 {structured_json.phone}</div>}
                              {structured_json.linkedin && (
                                <div>
                                  🔗{" "}
                                  <a
                                    href={structured_json.linkedin}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-emerald-400 hover:underline"
                                  >
                                    LinkedIn
                                  </a>
                                </div>
                              )}
                              {structured_json.github && (
                                <div>
                                  💻{" "}
                                  <a
                                    href={structured_json.github}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-emerald-400 hover:underline"
                                  >
                                    GitHub
                                  </a>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-slate-800 px-4 py-6 text-center text-xs text-slate-500">
                  Select a candidate to see structured data.
                </div>
              )}

              {selectedCandidate && (
                <div className="flex justify-end">
                  <button
                    onClick={() => {
                      if (window.confirm('Are you sure you want to delete this candidate? This will permanently delete all associated data (CVs, analyses).')) {
                        handleDeleteCandidate(selectedCandidate.candidate.id);
                      }
                    }}
                    className="rounded-md bg-red-600 px-3 py-1 text-sm font-semibold text-white hover:bg-red-700"
                  >
                    Delete Candidate
                  </button>
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="mb-4">
                <h2 className="text-lg font-semibold">Raw Extracted Text</h2>
                <p className="text-sm text-slate-400">
                  Full text extracted from CV.
                </p>
              </div>

              {selectedCandidate ? (
                <div className="space-y-3">
                  <textarea
                    readOnly
                    value={selectedCandidate.latestText || ""}
                    className="h-64 w-full resize-none rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-xs text-slate-100"
                  />
                  {!selectedCandidate.latestText ? (
                    <p className="text-xs text-slate-400">
                      No extracted text available yet. Upload a CV to generate it.
                    </p>
                  ) : null}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-slate-800 px-4 py-6 text-center text-xs text-slate-500">
                  Select a candidate to see extracted text.
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
