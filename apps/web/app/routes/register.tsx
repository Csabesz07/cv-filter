import { useState } from "react";
import { Link, useNavigate } from "react-router";

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
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [userType, setUserType] = useState<"employer" | "job_seeker">("employer");
  const [organizationName, setOrganizationName] = useState("");
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
      user_type: userType,
      ...(userType === "employer" ? { organization_name: organizationName.trim() } : {}),
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
            emai_type?: string[];
            organization_name?: string[];
            userl?: string[];
            password?: string[];
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
        // Log full error for debugging
        console.error("Registration error:", body);
        
        const message =
          body?.detail ||
          body?.username?.[0] ||
          body?.email?.[0] ||
          body?.password?.[0] ||
          (typeof body === 'object' ? JSON.stringify(body) : null) ||
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
       
      
      // Redirect to home after successful registration
      setTimeout(() => {
        navigate("/home");
      }, 1500); localStorage.setItem("refresh_token", body.refresh);
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
            <label htmlFor="user-type">I am a</label>
            <select
              id="user-type"
              name="user_type"
              required
              value={userType}
              onChange={(event) => setUserType(event.target.value as "employer" | "job_seeker")}
            >
              <option value="employer">Employer / Recruiter (Company)</option>
              <option value="job_seeker">Job Seeker (Individual)</option>
            </select>
          </div>
          {userType === "employer" && (
            <div>
              <label htmlFor="organization-name">Company / Organization Name</label>
              <input
                id="organization-name"
                name="organization_name"
                placeholder="Acme Inc."
                value={organizationName}
                onChange={(event) => setOrganizationName(event.target.value)}
              />
              <small style={{ color: "#666", fontSize: "0.85em" }}>
                Leave empty to use "{username || "your username"}'s Organization"
              </small>
            </div>
          )}
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
