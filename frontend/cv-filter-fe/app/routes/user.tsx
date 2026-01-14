import { useEffect, useState } from "react";

import type { Route } from "./+types/user";
import "./user.css";

type AlertState = {
  type: "error" | "success";
  message: string;
};

export function meta({}: Route.MetaArgs) {
  return [
    { title: "User Settings | CV Filter" },
    { name: "description", content: "Manage your CV Filter account." },
  ];
}

export default function UserSettings() {
  const [username, setUsername] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [alert, setAlert] = useState<AlertState | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const raw = sessionStorage.getItem("user");
    if (!raw) {
      return;
    }
    try {
      const user = JSON.parse(raw) as StoredUser;
      if (user.username) {
        setUsername(user.username);
      }
    } catch {
      // ignore invalid stored user
    }
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAlert(null);

    const accessToken =
      sessionStorage.getItem("access") || localStorage.getItem("access_token");
    if (!accessToken) {
      setAlert({ type: "error", message: "You need to sign in again." });
      return;
    }

    const payload: {
      username?: string;
      current_password?: string;
      new_password?: string;
    } = {};

    if (username.trim()) {
      payload.username = username.trim();
    }
    if (newPassword.trim()) {
      payload.new_password = newPassword;
      payload.current_password = currentPassword;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/me/", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(payload),
      });

      const body = (await response.json()) as
        | { user?: StoredUser; detail?: string; current_password?: string[] }
        | undefined;

      if (!response.ok) {
        const message =
          body?.detail ||
          body?.current_password?.[0] ||
          "Failed to update profile.";
        setAlert({ type: "error", message });
        return;
      }

      if (body?.user) {
        sessionStorage.setItem("user", JSON.stringify(body.user));
      }
      setCurrentPassword("");
      setNewPassword("");
      setAlert({ type: "success", message: "Profile updated." });
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
    <div className="user-page">
      <main className="user-content">
        <section className="user-card">
          <h1>User management</h1>
          <p className="subtitle">Update your username or password.</p>

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
                value={username}
                onChange={(event) => setUsername(event.target.value)}
              />
            </div>
            <div>
              <label htmlFor="current-password">Current password</label>
              <input
                id="current-password"
                name="current-password"
                type="password"
                placeholder="********"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
              />
            </div>
            <div>
              <label htmlFor="new-password">New password</label>
              <input
                id="new-password"
                name="new-password"
                type="password"
                placeholder="********"
                autoComplete="new-password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
              />
            </div>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save changes"}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
