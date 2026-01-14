import { useState } from "react";

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

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Candidates | CV Filter" },
    { name: "description", content: "Register a candidate." },
  ];
}

export default function Candidates() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage(null);
    setError(null);

    const accessToken =
      sessionStorage.getItem("access") || localStorage.getItem("access_token");
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
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-4xl px-4 py-10">
        <div className="mb-6">
          <h1 className="text-3xl font-semibold">Candidate registration</h1>
          <p className="text-sm text-slate-400">
            Add a candidate by name and email.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
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
      </div>
    </main>
  );
}
