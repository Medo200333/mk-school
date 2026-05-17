import Link from "next/link";
import { SchoolShell } from "@/components/layout/school-shell";
import { apiGet } from "@/lib/api";

type SchoolCoreOverview = {
  module: string;
  mode: string;
  database_impact: string;
  safe_to_import_slots: boolean;
  safe_to_confirm: boolean;
  counts: {
    students_count: number;
    guardians_count: number;
    student_guardian_links_count: number;
    classes_count: number;
    grades_count: number;
    institutes_count: number;
    staff_attendance_records_count: number;
    staff_present_count: number;
    staff_exception_count: number;
  };
  latest_students: Array<{
    id: string;
    legacy_access_id: string | null;
    national_id: string | null;
    student_name_ar: string;
    gender: string | null;
    class_name: string | null;
    enrollment_status: string;
    created_at: string | null;
  }>;
  capabilities: string[];
  known_limits: string[];
  actions: Array<{
    title: string;
    description: string;
    href: string;
  }>;
};

async function loadOverview() {
  try {
    return {
      data: await apiGet<SchoolCoreOverview>("/api/v1/school-core/overview"),
      error: ""
    };
  } catch (err) {
    return {
      data: null,
      error: err instanceof Error ? err.message : "فشل الاتصال بواجهة عمليات المدرسة"
    };
  }
}

export default async function SchoolPage() {
  const { data, error } = await loadOverview();
  const counts = data?.counts;

  return (
    <SchoolShell>
      <section className="hero surface school-core-hero">
        <div>
          <div className="eyebrow">PHASE 8D · SCHOOL CORE OPERATIONS</div>
          <h1>عمليات المدرسة الأساسية</h1>
          <p>
            لوحة تشغيل read-only لملفات الطلاب وأولياء الأمور وروابطهم وحضور الموظفين الحالي.
            لا تنفذ هذه الصفحة أي إدخال أو تعديل أو حذف أو ترحيل بيانات.
          </p>
        </div>
        <div className="hero-actions">
          <span className="badge">Read-only</span>
          <Link href="/school/students" className="btn">فتح الطلاب وأولياء الأمور</Link>
          <Link href="/timetable" className="btn btn-secondary">فتح الجدول</Link>
        </div>
      </section>

      {error ? <div className="error mt">{error}</div> : null}

      <section className="grid stats mt school-core-stats">
        <div className="metric"><span>الطلاب</span><strong>{counts?.students_count ?? 0}</strong></div>
        <div className="metric"><span>أولياء الأمور</span><strong>{counts?.guardians_count ?? 0}</strong></div>
        <div className="metric"><span>روابط طالب/ولي أمر</span><strong>{counts?.student_guardian_links_count ?? 0}</strong></div>
        <div className="metric"><span>الفصول</span><strong>{counts?.classes_count ?? 0}</strong></div>
        <div className="metric"><span>المراحل/الصفوف</span><strong>{counts?.grades_count ?? 0}</strong></div>
        <div className="metric"><span>المعاهد</span><strong>{counts?.institutes_count ?? 0}</strong></div>
        <div className="metric"><span>سجلات حضور الموظفين</span><strong>{counts?.staff_attendance_records_count ?? 0}</strong></div>
        <div className="metric"><span>استثناءات الحضور</span><strong>{counts?.staff_exception_count ?? 0}</strong></div>
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>مراكز التشغيل</h2>
          <div className="school-core-actions">
            {(data?.actions ?? [
              { title: "الطلاب وأولياء الأمور", description: "عرض read-only للطلاب والروابط.", href: "/school/students" },
              { title: "الجدول المدرسي", description: "فتح استوديو الجدول الحالي.", href: "/timetable" }
            ]).map((item) => (
              <Link href={item.href} className="school-core-action-card" key={item.href}>
                <strong>{item.title}</strong>
                <span>{item.description}</span>
              </Link>
            ))}
          </div>
        </div>

        <div className="surface section-pad">
          <h2>حواجز الأمان</h2>
          <div className="list">
            <span>database_impact = {data?.database_impact ?? "none"}</span>
            <span>safe_to_import_slots = {String(data?.safe_to_import_slots ?? false)}</span>
            <span>safe_to_confirm = {String(data?.safe_to_confirm ?? false)}</span>
            <span>ROZ slot import remains blocked</span>
          </div>
        </div>
      </section>

      <section className="surface section-pad mt">
        <div className="studio-toolbar">
          <div>
            <h2>أحدث الطلاب</h2>
            <p className="muted">قراءة مباشرة من school.students بدون أي تعديل في قاعدة البيانات.</p>
          </div>
          <Link href="/school/students" className="btn btn-secondary">عرض تفصيلي</Link>
        </div>

        <div className="table-wrap mt-small">
          <table>
            <thead>
              <tr>
                <th>كود Access</th>
                <th>الرقم القومي</th>
                <th>اسم الطالب</th>
                <th>الفصل</th>
                <th>الحالة</th>
              </tr>
            </thead>
            <tbody>
              {(data?.latest_students ?? []).map((student) => (
                <tr key={student.id}>
                  <td>{student.legacy_access_id || "—"}</td>
                  <td>{student.national_id || "—"}</td>
                  <td><strong>{student.student_name_ar}</strong></td>
                  <td>{student.class_name || "—"}</td>
                  <td>{student.enrollment_status}</td>
                </tr>
              ))}
              {(!data?.latest_students || data.latest_students.length === 0) ? (
                <tr>
                  <td colSpan={5}>لا توجد بيانات طلاب للعرض.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="surface section-pad mt">
        <h2>حدود المرحلة الحالية</h2>
        <div className="list">
          {(data?.known_limits ?? [
            "student attendance is not modeled yet; only hr.attendance_records exists now",
            "this API does not create, update, delete, import, or migrate data",
            "ROZ slot import remains blocked"
          ]).map((item) => <span key={item}>{item}</span>)}
        </div>
      </section>
    </SchoolShell>
  );
}
