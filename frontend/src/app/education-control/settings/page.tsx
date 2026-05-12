import { SchoolShell } from "@/components/layout/school-shell";
import { apiGet } from "@/lib/api";

type Activation = { id: string; source_file: string; activation_code: string; activation_name_ar: string; is_active: boolean; };

export default async function Page() {
  let activations: Activation[] = [];
  let error = "";
  try {
    activations = await apiGet<Activation[]>("/api/v1/education-control/activation-settings");
  } catch (err) {
    error = err instanceof Error ? err.message : "فشل تحميل التفعيل";
  }

  return (
    <SchoolShell>
      <section className="card hero"><h1>الإعدادات والتفعيل</h1><p>إعدادات الفصلين والدور الثاني.</p></section>
      {error ? <div className="error">{error}</div> : null}
      <section className="grid grid-3 mt">
        {activations.map((a) => (
          <div key={a.id} className="card card-link">
            <span className="badge">{a.activation_code}</span>
            <h2 style={{ marginTop: 16 }}>{a.activation_name_ar}</h2>
            <p>{a.source_file}</p>
          </div>
        ))}
      </section>
    </SchoolShell>
  );
}
