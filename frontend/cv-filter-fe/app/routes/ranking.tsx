import type { Route } from "./+types/ranking";
import "./section.css";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Ranking | CV Filter" },
    { name: "description", content: "Ranking workspace." },
  ];
}

export default function Ranking() {
  return (
    <div className="section-page">
      <main className="section-content">
        <section className="section-card">
          <h1>Ranking</h1>
          <p>
            Configure ranking criteria and review scored candidates to build your
            shortlist.
          </p>
        </section>
      </main>
    </div>
  );
}
