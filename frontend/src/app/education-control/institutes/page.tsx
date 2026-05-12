"use client";

import { useEffect, useState } from "react";
import { SchoolShell } from "@/components/layout/school-shell";
import { apiGet, apiPost } from "@/lib/api";

type Institute = {
  id: string;
  code: string | null;
  name_ar: string;
  institute_type: string | null;
  education_stage: string | null;
  zone_name: string | null;
  administration_name: string | null;
};

export default function InstitutesPage() {
  const [items, setItems] = useState<Institute[]>([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      setItems(await apiGet<Institute[]>("/api/v1/education-control/institutes"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "فشل التحميل");
    }
  }

  async function submit(formData: FormData) {
    try {
      await apiPost("/api/v1/education-control/institutes", {
        code: String(formData.get("code") || ""),
        name_ar: String(formData.get("name_ar") || ""),
        institute_type: String(formData.get("institute_type") || ""),
        education_stage: String(formData.get("education_stage") || ""),
        zone_name: String(formData.get("zone_name") || ""),
        administration_name: String(formData.get("administration_name") || "")
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "فشل الحفظ");
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <SchoolShell>
      <section className="card hero"><h1>المعاهد والمدارس</h1><p>إدارة بيانات المعاهد والمدارس.</p></section>

      <form action={submit} className="card form mt">
        <input className="input" name="code" placeholder="كود المعهد" />
        <input className="input" name="name_ar" placeholder="اسم المعهد" required />
        <input className="input" name="institute_type" placeholder="نوع المعهد" />
        <input className="input" name="education_stage" placeholder="المرحلة" />
        <input className="input" name="zone_name" placeholder="المنطقة" />
        <input className="input" name="administration_name" placeholder="الإدارة" />
        <button className="btn" type="submit">حفظ المعهد</button>
      </form>

      {error ? <div className="error">{error}</div> : null}

      <section className="card mt table-wrap">
        <table>
          <thead><tr><th>الكود</th><th>الاسم</th><th>النوع</th><th>المرحلة</th><th>المنطقة</th><th>الإدارة</th></tr></thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.code}</td><td><strong>{item.name_ar}</strong></td><td>{item.institute_type}</td>
                <td>{item.education_stage}</td><td>{item.zone_name}</td><td>{item.administration_name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </SchoolShell>
  );
}
