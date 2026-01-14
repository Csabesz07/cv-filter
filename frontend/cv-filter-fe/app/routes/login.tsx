import { useState } from "react";
import { Link } from "react-router";

import type { Route } from "./+types/login";
import "./login.css";

type AlertState = {
  type: "error" | "success";
  message: string;
};

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Login | CV Filter" },
    { name: "description", content: "Sign in to manage your CV filters." },
  ];
}

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [alert, setAlert] = useState<AlertState | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAlert(null);
    setIsSubmitting(true);

    const payload = {
      username: username.trim(),
      password,
    };

    try {
      const response = await fetch("/api/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      let body: { access?: string; refresh?: string; detail?: string } | null =
        null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }

      if (!response.ok) {
        setAlert({
          type: "error",
          message: body?.detail || "Invalid credentials",
        });
        return;
      }

      if (body?.access) {
        sessionStorage.setItem("access", body.access);
      }
      if (body?.refresh) {
        sessionStorage.setItem("refresh", body.refresh);
      }

      setAlert({
        type: "success",
        message: "Login successful. Token stored in sessionStorage.",
      });
    } catch {
      setAlert({
        type: "error",
        message: "Unexpected error. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <main className="auth-card">
        <h1>Welcome back</h1>
        <p className="subtitle">Sign in to manage your CV filters.</p>

        <div aria-live="polite">
          {alert ? (
            <div className={`auth-alert auth-alert-${alert.type}`}>
              {alert.message}
            </div>
          ) : null}
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              name="username"
              placeholder="jane"
              autoComplete="username"
              required
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              placeholder="********"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="auth-muted">
          New here? <Link className="auth-link" to="/register">Create an account</Link>
        </p>
      </main>
    </div>
  );
}
