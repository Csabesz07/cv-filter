import { useEffect, useState } from "react";
import {
  isRouteErrorResponse,
  Link,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLocation,
  useNavigate,
} from "react-router";

import type { Route } from "./+types/root";
import "./app.css";

export const links: Route.LinksFunction = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  {
    rel: "preconnect",
    href: "https://fonts.gstatic.com",
    crossOrigin: "anonymous",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
  },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  const navigate = useNavigate();
  const [userLabel, setUserLabel] = useState("Guest");
  const location = useLocation();

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const raw = sessionStorage.getItem("user");
    if (!raw) {
      setUserLabel("Guest");
      return;
    }
    try {
      const user = JSON.parse(raw) as { username?: string; email?: string };
      setUserLabel(user.username || user.email || "User");
    } catch {
      setUserLabel("User");
    }
  }, [location.pathname]);

  const handleLogout = () => {
    sessionStorage.removeItem("access");
    sessionStorage.removeItem("refresh");
    sessionStorage.removeItem("user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  };

  return (
    <>
      <header className="border-b border-slate-800/80 bg-slate-950/80 text-slate-100 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <Link className="text-lg font-semibold tracking-wide" to="/home">
            cv-filter
          </Link>
          <nav className="flex flex-wrap items-center gap-3 text-sm">
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/home"
            >
              Home
            </Link>
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/document-extraction"
            >
              Document Extraction
            </Link>
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/entity-extraction"
            >
              Entity Extraction
            </Link>
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/ranking"
            >
              Ranking
            </Link>
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/summarization"
            >
              Summarization
            </Link>
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/organization"
            >
              Organization
            </Link>
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/user"
            >
              {userLabel}
            </Link>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-full border border-slate-700 px-3 py-1 font-medium text-slate-300 hover:border-emerald-400/70 hover:text-emerald-200"
            >
              Logout
            </button>
          </nav>
        </div>
      </header>
      <Outlet />
    </>
  );
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "Oops!";
  let details = "An unexpected error occurred.";
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? "404" : "Error";
    details =
      error.status === 404
        ? "The requested page could not be found."
        : error.statusText || details;
  } else if (import.meta.env.DEV && error && error instanceof Error) {
    details = error.message;
    stack = error.stack;
  }

  return (
    <main className="pt-16 p-4 container mx-auto">
      <h1>{message}</h1>
      <p>{details}</p>
      {stack && (
        <pre className="w-full p-4 overflow-x-auto">
          <code>{stack}</code>
        </pre>
      )}
    </main>
  );
}
