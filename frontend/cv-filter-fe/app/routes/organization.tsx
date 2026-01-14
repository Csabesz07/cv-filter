import { useMemo, useState } from "react";

import type { Route } from "./+types/organization";

type OrgResponse = {
  organization?: {
    id?: string;
    name?: string;
    slug?: string;
  };
  detail?: string;
};

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Organization | CV Filter" },
    { name: "description", content: "Manage your organization." },
  ];
}

export default function Organization() {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [organization, setOrganization] = useState<OrgResponse["organization"] | null>(
    null
  );

  const tokenWarning = useMemo(() => {
    if (typeof window === "undefined") return false;
    return !localStorage.getItem("access_token");
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setMessage(null);

    const accessToken =
      typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

    if (!accessToken) {
      setError("You must be logged in to create an organization.");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/orgs/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          name: name.trim(),
          slug: slug.trim(),
        }),
      });

      const contentType = response.headers.get("content-type") || "";
      let body: OrgResponse | null = null;

      if (contentType.includes("application/json")) {
        body = (await response.json()) as OrgResponse;
      } else {
        const text = await response.text();
        if (!response.ok) {
          setError(text || "Unexpected server error.");
          return;
        }
        body = null;
      }

      if (!response.ok) {
        setError(body?.detail || "Failed to create organization.");
        return;
      }

      setOrganization(body?.organization || null);
      setMessage("Organization created.");
      setName("");
      setSlug("");
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
          <h1 className="text-3xl font-semibold">Organization</h1>
          <p className="text-sm text-slate-400">
            Create an organization to manage users and candidates.
          </p>
        </div>

        {tokenWarning ? (
          <div className="mb-6 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
            Not logged in. Sign in to create an organization.
          </div>
        ) : null}

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="text-sm font-medium text-slate-200">
                Organization name
              </label>
              <input
                className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-400"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Acme Recruiting"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-200">Slug</label>
              <input
                className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-400"
                value={slug}
                onChange={(event) => setSlug(event.target.value)}
                placeholder="acme-recruiting"
              />
              <p className="mt-2 text-xs text-slate-400">
                Optional. If blank, we will generate one from the name.
              </p>
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
              {isSubmitting ? "Creating..." : "Create organization"}
            </button>
          </form>
        </div>

        {organization ? (
          <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="text-lg font-semibold">Current organization</h2>
            <table className="mt-4 w-full text-left text-sm">
              <tbody>
                <tr className="border-b border-slate-800">
                  <td className="py-2 font-medium text-slate-200">Name</td>
                  <td className="py-2 text-slate-400">{organization.name || "-"}</td>
                </tr>
                <tr>
                  <td className="py-2 font-medium text-slate-200">Slug</td>
                  <td className="py-2 text-slate-400">{organization.slug || "-"}</td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </main>
  );
}
