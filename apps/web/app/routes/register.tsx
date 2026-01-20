import { useState } from "react";
import { Link } from "react-router";

import type { Route } from "./+types/register";
import "./login.css";

type AlertState = {
  type: "error" | "success";
  message: string;
};

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Register | CV Filter" },
    { name: "description", content: "Create a CV Filter account." },
  ];
}

export default function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [alert, setAlert] = useState<AlertState | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAlert(null);
    setIsSubmitting(true);

    const payload = {
      username: username.trim(),
      email: email.trim(),
      password,
    };

    try {
      const response = await fetch("/api/auth/register/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      let body:
        | {
            detail?: string;
            username?: string[];
            email?: string[];
            user?: { username?: string; email?: string };
            access?: string;
            refresh?: string;
          }
        | null = null;
      try {
        body = await response.json();
      } catch {
        body = null;
      }

      if (!response.ok) {
        const message =
          body?.detail ||
          body?.username?.[0] ||
          body?.email?.[0] ||
          "Registration failed";
        setAlert({ type: "error", message });
        return;
      }

      setAlert({
        type: "success",
        message: "Account created. You can now sign in.",
      });

      if (body?.user) {
        sessionStorage.setItem("user", JSON.stringify(body.user));
      }
      if (body?.access) {
        sessionStorage.setItem("access", body.access);
        localStorage.setItem("access_token", body.access);
      }
      if (body?.refresh) {
        sessionStorage.setItem("refresh", body.refresh);
        localStorage.setItem("refresh_token", body.refresh);
      }
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
        <h1>Create account</h1>
        <p className="subtitle">Start managing your CV filters today.</p>

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
            <label htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              placeholder="jane@example.com"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              placeholder="********"
              autoComplete="new-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create account"}
          </button>
        </form>

        <p className="auth-muted">
          Already have an account?{" "}
          <Link className="auth-link" to="/login">
            Sign in
          </Link>
        </p>
      </main>
    </div>
  );
}
