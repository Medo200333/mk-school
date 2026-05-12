import Link from "next/link";
import { SchoolShell } from "@/components/layout/school-shell";
import { apiGet } from "@/lib/api";
import { PlatformModule } from "@/data/platform";

type ApiModule = {
  code: string;
  status: string;
  counts: Record<string, number>;
  acceptance: string[];
};

async function loadApiModule(code: string) {
  try {
    const modules = await apiGet<ApiModule[]>("/api/v1/platform/modules");
    return { module: modules.find((item) => item.code === code) ?? null, error: "" };
  } catch (err) {
    return {
      module: null,
      error: err instanceof Error ? err.message : "فشل الاتصال بالباك إند"
    };
  }
}

export async function ModulePage({ module }: { module: PlatformModule }) {
  const { module: apiModule, error } = await loadApiModule(module.code);
  const counts = apiModule?.counts ?? {};
  const acceptance = apiModule?.acceptance ?? ["Migration", "API Contract", "Frontend Route", "Audit Ready"];

  return (
    <SchoolShell>
      <section className="hero surface">
        <div>
          <div className="eyebrow">{module.scope}</div>
          <h1>{module.title}</h1>
          <p>{module.description}</p>
        </div>
        <div className="hero-actions">
          <span className="badge">{apiModule?.status ?? module.status}</span>
          <Link href="/" className="btn btn-secondary">المنصة الموحدة</Link>
        </div>
      </section>

      {error ? <div className="error">{error}</div> : null}

      <section className="grid stats mt">
        {module.metrics.map((metric) => (
          <div key={metric} className="metric">
            <span>{metric}</span>
            <strong>{counts[metric] ?? 0}</strong>
          </div>
        ))}
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>نطاق التنفيذ</h2>
          <div className="list">
            {module.responsibilities.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>
        <div className="surface section-pad">
          <h2>معيار التحديث</h2>
          <div className="list">
            {acceptance.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>
      </section>
    </SchoolShell>
  );
}
