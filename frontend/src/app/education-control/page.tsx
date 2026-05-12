import Link from "next/link";
import { SchoolShell } from "@/components/layout/school-shell";
import { apiGet } from "@/lib/api";
import { educationControlCards } from "@/data/education-control";

type Readiness = {
  counts: {
    institutes_count: number;
    students_count: number;
    subjects_count: number;
    activations_count: number;
  };
};

export default async function EducationControlPage() {
  let readiness: Readiness | null = null;
  let error = "";

  try {
    readiness = await apiGet<Readiness>("/api/v1/education-control/readiness");
  } catch (err) {
    error = err instanceof Error ? err.message : "فشل الاتصال بالباك إند";
  }

  return (
    <SchoolShell>
      <section className="card hero">
        <div className="eyebrow">EDUCATION CONTROL</div>
        <h1>لوحة كنترول النقل</h1>
        <p>مركز تشغيل الكنترول: المعاهد، الطلاب، المواد، التفعيل، الرصد، والنتائج.</p>
      </section>

      {error ? <div className="error">{error}</div> : null}

      <section className="grid stats mt">
        <div className="card card-link"><p>المعاهد</p><h2>{readiness?.counts.institutes_count ?? 0}</h2></div>
        <div className="card card-link"><p>الطلاب</p><h2>{readiness?.counts.students_count ?? 0}</h2></div>
        <div className="card card-link"><p>المواد</p><h2>{readiness?.counts.subjects_count ?? 0}</h2></div>
        <div className="card card-link"><p>التفعيلات</p><h2>{readiness?.counts.activations_count ?? 0}</h2></div>
      </section>

      <section className="grid grid-3 mt">
        {educationControlCards.slice(1).map((card) => (
          <Link key={card.href} href={card.href} className="card card-link">
            <span className="badge">{card.badge}</span>
            <h2 style={{ marginTop: 16 }}>{card.title}</h2>
            <p>{card.description}</p>
          </Link>
        ))}
      </section>
    </SchoolShell>
  );
}
