import Link from "next/link";
import { SchoolShell } from "@/components/layout/school-shell";
import { apiGet } from "@/lib/api";
import { platformModules } from "@/data/platform";

type PlatformOverview = {
  product: string;
  principle: string;
  modules: Array<{
    code: string;
    status: string;
    counts: Record<string, number>;
  }>;
};

async function loadOverview() {
  try {
    return { data: await apiGet<PlatformOverview>("/api/v1/platform/overview"), error: "" };
  } catch (err) {
    return {
      data: null,
      error: err instanceof Error ? err.message : "فشل الاتصال بالباك إند"
    };
  }
}

export default async function HomePage() {
  const { data, error } = await loadOverview();

  return (
    <SchoolShell>
      <section className="hero surface">
        <div>
          <div className="eyebrow">MK SCHOOL ERP</div>
          <h1>{data?.product ?? "ERP تعليمي متكامل"}</h1>
          <p>
            {data?.principle ??
              "منصة موحدة تجمع النواة المشتركة، الموظفين، المدارس، الجدول المدرسي، الكنترول، ومرآة Access."}
          </p>
        </div>
        <div className="hero-actions">
          <Link href="/platform" className="btn">فتح النواة</Link>
          <Link href="/education-control" className="btn btn-secondary">فتح الكنترول</Link>
        </div>
      </section>

      {error ? <div className="error">{error}</div> : null}

      <section className="grid grid-3 mt">
        {platformModules.map((card) => {
          const apiModule = data?.modules.find((item) => item.code === card.code);
          return (
            <Link key={card.href} href={card.href} className="surface module-link">
              <span className="badge">{card.badge}</span>
              <h2>{card.title}</h2>
              <p>{card.description}</p>
              <strong>{apiModule?.status ?? card.status}</strong>
            </Link>
          );
        })}
      </section>
    </SchoolShell>
  );
}
