import type { Route } from "./+types/home";
import { Link } from "react-router";
import "./home.css";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Home | CV Filter" },
    { name: "description", content: "Welcome to CV Filter." },
  ];
}

export default function Home() {
  return (
    <div className="home-page">
      <main className="home-content">
        <section className="home-hero">
          <div className="home-hero-text">
            <span className="home-eyebrow">CV Filter platform</span>
            <h1>Hire with clarity, not chaos.</h1>
            <p>
              CV Filter turns candidate onboarding into a single, searchable
              stream. Register candidates, attach CVs, and let AI extract the
              strongest signals so teams can rank and act with confidence.
            </p>
            <div className="home-hero-actions">
              <span className="home-pill">Candidate registration</span>
              <span className="home-pill">AI extraction</span>
              <span className="home-pill">Organization workspaces</span>
            </div>
          </div>
          <div className="home-hero-panel">
            <div className="home-panel-card">
              <h2>Flow at a glance</h2>
              <ol>
                <li>Register a candidate profile.</li>
                <li>Assign one or many CVs to the profile.</li>
                <li>AI extracts skills, roles, and highlights.</li>
                <li>Teams search and compare within an organization.</li>
              </ol>
            </div>
            <div className="home-panel-metric">
              <span>Search-ready profiles</span>
              <strong>Instantly indexed</strong>
            </div>
          </div>
        </section>

        <section className="home-section">
          <div className="home-section-title">
            <h2>What the platform does</h2>
            <p>
              Everything needed to collect, structure, and surface candidate
              data lives in one place.
            </p>
          </div>
          <div className="home-feature-grid">
            <article className="home-feature-card">
              <h3>Candidate registration</h3>
              <p>
                Create a profile in seconds, capture contact details, and set
                ownership before the first CV arrives.
              </p>
            </article>
            <article className="home-feature-card">
              <h3>CV assignment</h3>
              <p>
                Attach multiple CVs per candidate to track updates, versions, or
                different job applications.
              </p>
            </article>
            <article className="home-feature-card">
              <h3>AI extraction</h3>
              <p>
                Extracts the most relevant information from each CV and
                highlights skills, seniority, and domain focus.
              </p>
            </article>
            <article className="home-feature-card">
              <h3>Organization access</h3>
              <p>
                Users belong to organizations, keeping candidate data scoped to
                the right hiring teams.
              </p>
            </article>
            <article className="home-feature-card">
              <h3>Candidate search</h3>
              <p>
                Use natural language queries to find candidates matching specific requirements (e.g., "3 years Java + English B2").
              </p>
              <Link to="/search" className="text-blue-400 hover:text-blue-300 text-sm">
                Try Natural Language Search →
              </Link>
            </article>
          </div>
        </section>

        <section className="home-section home-section-alt">
          <div className="home-section-title">
            <h2>Purpose-built workflow</h2>
            <p>
              Designed for recruiters, HR teams, and hiring managers who need to
              act on clean, comparable candidate data.
            </p>
          </div>
          <div className="home-workflow">
            <div className="home-workflow-step">
              <span>01</span>
              <h3>Register the candidate</h3>
              <p>
                Build a profile that stores contact info and keeps the hiring
                story consistent.
              </p>
            </div>
            <div className="home-workflow-step">
              <span>02</span>
              <h3>Assign CVs</h3>
              <p>
                Upload and attach CVs so the latest documents are always tied to
                the right person.
              </p>
            </div>
            <div className="home-workflow-step">
              <span>03</span>
              <h3>Extract key details</h3>
              <p>
                AI summarizes skills, roles, and experience to highlight what
                matters most.
              </p>
            </div>
            <div className="home-workflow-step">
              <span>04</span>
              <h3>Search and compare</h3>
              <p>
                Find candidates by organization, keyword, or skill set to move
                faster on shortlists.
              </p>
            </div>
          </div>
        </section>

        <section className="home-cta">
          <div>
            <h2>Turn CVs into a ranked talent pipeline.</h2>
            <p>
              CV Filter keeps every candidate organized, every CV connected, and
              every search fast.
            </p>
          </div>
          <div className="home-cta-card">
            <p>Built for teams who want clarity before the interview.</p>
            <div className="home-cta-tags">
              <span>Structured profiles</span>
              <span>AI-driven insights</span>
              <span>Organization-ready access</span>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
