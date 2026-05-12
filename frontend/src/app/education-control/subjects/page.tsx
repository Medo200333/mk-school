import { SchoolShell } from "@/components/layout/school-shell";
import { apiGet } from "@/lib/api";

type Subject = { id: string; code: string; name_ar: string; max_score: number | null; min_score: number | null; };

export default async function SubjectsPage() {
  let subjects: Subject[] = [];
  let error = "";

  try {
    subjects = await apiGet<Subject[]>("/api/v1/education-control/subjects");
  } catch (err) {
    error = err instanceof Error ? err.message : "فشل التحميل";
  }

  return (
    <SchoolShell>
      <section className="card hero"><h1>المواد والدرجات</h1><p>تعريف المواد والدرجات.</p></section>
      {error ? <div className="error">{error}</div> : null}
      <section className="grid grid-3 mt">
        {subjects.length === 0 ? <div className="card card-link">لا توجد مواد بعد.</div> : subjects.map((s) => (
          <div key={s.id} className="card card-link">
            <span className="badge">{s.code}</span>
            <h2 style={{ marginTop: 16 }}>{s.name_ar}</h2>
            <p>العظمى: {s.max_score ?? "-"} / الصغرى: {s.min_score ?? "-"}</p>
          </div>
        ))}
      </section>
    </SchoolShell>
  );
}
