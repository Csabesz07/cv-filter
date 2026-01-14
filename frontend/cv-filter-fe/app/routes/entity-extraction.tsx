import type { Route } from "./+types/entity-extraction";
import "./section.css";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Entity Extraction | CV Filter" },
    { name: "description", content: "Entity extraction workspace." },
  ];
}

export default function EntityExtraction() {
  return (
    <div className="section-page">
      <main className="section-content">
        <section className="section-card">
          <h1>Entity Extraction</h1>
          <p>
            Review extracted entities such as skills, titles, and contact details
            from candidate CVs.
          </p>
        </section>
      </main>
    </div>
  );
}
