import { useMemo } from "react";
import { Link, useNavigate } from "react-router";

import type { Route } from "./+types/home";
import "./home.css";

type StoredUser = {
  username?: string;
  email?: string;
};

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Home | CV Filter" },
    { name: "description", content: "Welcome to CV Filter." },
  ];
}

export default function Home() {
  const navigate = useNavigate();
  const userLabel = useMemo(() => {
    if (typeof window === "undefined") {
      return "Guest";
    }

    const raw = sessionStorage.getItem("user");
    if (!raw) {
      return "Guest";
    }

    try {
      const user = JSON.parse(raw) as StoredUser;
      return user.username || user.email || "User";
    } catch {
      return "User";
    }
  }, []);

  const handleLogout = () => {
    sessionStorage.removeItem("access");
    sessionStorage.removeItem("refresh");
    sessionStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <div className="home-page">
      <header className="home-nav">
        <div className="home-nav-inner">
          <Link className="home-brand" to="/">
            cv-filter
          </Link>
          <nav className="home-nav-links">
            <Link className="home-link" to="/home">
              Home
            </Link>
            <Link className="home-user-pill" to="/user">
              {userLabel}
            </Link>
            <button className="home-logout" type="button" onClick={handleLogout}>
              Logout
            </button>
          </nav>
        </div>
      </header>

      <main className="home-content">
        <section className="home-hero">
          <h1>Welcome to CV Filter</h1>
          <p>
            Review, rank, and manage candidate CVs in one place. Your filters,
            uploads, and insights will appear here as you get started.
          </p>
        </section>
      </main>
    </div>
  );
}
