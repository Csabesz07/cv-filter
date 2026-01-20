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
import "./app.css";import { clearAuthTokens } from "./utils/auth";
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
  const hideHeader =
    location.pathname === "/" ||
    location.pathname === "/login" ||
    location.pathname === "/register";

  // Protected routes - require authentication
  const publicRoutes = ["/", "/login", "/register"];
  const isPublicRoute = publicRoutes.includes(location.pathname);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    // Check authentication for protected routes
    if (!isPublicRoute) {
      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access");
      if (!token) {
        navigate("/login");
        return;
      }
      
      // Verify token is valid by making a test API call
      const verifyToken = async () => {
        try {
          const response = await fetch("/api/candidates/", {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          
          if (response.status === 401 || response.status === 403) {
            // Token is invalid or expired
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            sessionStorage.removeItem("access");
            sessionStorage.removeItem("refresh");
            sessionStorage.removeItem("user");
            navigate("/login");
            return;
          }
        } catch (error) {
          // Network error - don't redirect, just log
          console.error("Token verification failed:", error);
        }
      };
      
      verifyToken();
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
  }, [location.pathname, navigate, isPublicRoute]);

  const handleLogout = () => {
    clearAuthTokens();
    navigate("/login");
  };

  return (
    <>
      {hideHeader ? null : (
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
                to="/organization"
              >
                Organization
              </Link>
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/candidates"
            >
              Candidates
            </Link>
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/search"
            >
              Search
            </Link>
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/audit"
            >
              Audit
            </Link>
            <Link
              className="rounded-full px-3 py-1 font-medium text-slate-200 hover:bg-emerald-500/10 hover:text-emerald-200"
              to="/files"
            >
              Files
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
      )}
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
