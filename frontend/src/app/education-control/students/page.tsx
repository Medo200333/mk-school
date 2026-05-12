"use client";

import { useEffect, useState } from "react";
import { SchoolShell } from "@/components/layout/school-shell";
import { apiGet, apiPost } from "@/lib/api";

type Student = {
  id: string;
  legacy_access_id: string | null;
  national_id: string | null;
  student_name_ar: string;
  gender: string | null;
  nationality: string | null;
  class_name: string | null;
  enrollment_status: string;
};

export default function StudentsPage() {
  const [items, setItems] = useState<Student[]>([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      setItems(await apiGet<Student[]>("/api/v1/education-control/students"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "فشل التحميل");
    }
  }

  async function submit(formData: FormData) {
    try {
      await apiPost("/api/v1/education-control/students", {
        legacy_access_id: String(formData.get("legacy_access_id") || ""),
        national_id: String(formData.get("national_id") || ""),
        student_name_ar: String(formData.get("student_name_ar") || ""),
        gender: String(formData.get("gender") || ""),
        nationality: String(formData.get("nationality") || ""),
        religion: String(formData.get("religion") || ""),
        health_status: String(formData.get("health_status") || ""),
        class_name: String(formData.get("class_name") || "")
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "فشل الحفظ");
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <SchoolShell>
      <section className="card hero"><h1>الطلاب</h1><p>إدارة ملف الطالب.</p></section>

      <form action={submit} className="card form mt">
        <input className="input" name="legacy_access_id" placeholder="كود Access" />
        <input className="input" name="national_id" placeholder="الرقم القومي" />
        <input className="input" name="student_name_ar" placeholder="اسم الطالب" required />
        <input className="input" name="gender" placeholder="النوع" />
        <input className="input" name="nationality" placeholder="الجنسية" />
        <input className="input" name="religion" placeholder="الديانة" />
        <input className="input" name="health_status" placeholder="الحالة الصحية" />
        <input className="input" name="class_name" placeholder="الفصل" />
        <button className="btn" type="submit">حفظ الطالب</button>
      </form>

      {error ? <div className="error">{error}</div> : null}

      <section className="card mt table-wrap">
        <table>
          <thead><tr><th>Access</th><th>الرقم القومي</th><th>الاسم</th><th>النوع</th><th>الجنسية</th><th>الفصل</th><th>الحالة</th></tr></thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.legacy_access_id}</td><td>{item.national_id}</td><td><strong>{item.student_name_ar}</strong></td>
                <td>{item.gender}</td><td>{item.nationality}</td><td>{item.class_name}</td><td>{item.enrollment_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </SchoolShell>
  );
}
