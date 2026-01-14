import type { Route } from "./+types/summarization";
import "./section.css";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Summarization | CV Filter" },
    { name: "description", content: "Summarization workspace." },
  ];
}

export default function Summarization() {
  return (
    <div className="section-page">
      <main className="section-content">
        <section className="section-card">
          <h1>Summarization</h1>
          <p>
            Generate concise summaries of candidate profiles and highlight key
            strengths.
          </p>
        </section>
      </main>
    </div>
  );
}
