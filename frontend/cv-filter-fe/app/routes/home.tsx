import type { Route } from "./+types/home";
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
