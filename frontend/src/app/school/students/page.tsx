"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SchoolShell } from "@/components/layout/school-shell";
import { apiGet } from "@/lib/api";

type GuardianLink = {
  id: string;
  full_name_ar: string;
  national_id: string | null;
  phone: string | null;
  relation_type: string | null;
  is_primary: boolean;
};

type Student = {
  id: string;
  legacy_access_id: string | null;
  national_id: string | null;
  student_name_ar: string;
  gender: string | null;
  nationality: string | null;
  religion: string | null;
  health_status: string | null;
  class_name: string | null;
  enrollment_status: string;
  institute_name_ar: string | null;
  grade_name_ar: string | null;
  guardians: GuardianLink[];
};

type Guardian = {
  id: string;
  national_id: string | null;
  full_name_ar: string;
  phone: string | null;
  relation_type: string | null;
  students: Array<{
    id: string;
    student_name_ar: string;
    class_name: string | null;
    relation_type: string | null;
    is_primary: boolean;
  }>;
};

type AttendanceRecord = {
  id: string;
  employee_name_ar: string;
  employee_no: string | null;
  attendance_date: string;
  check_in: string | null;
  check_out: string | null;
  status: string;
  notes: string | null;
};

type Overview = {
  counts: {
    students_count: number;
    guardians_count: number;
    student_guardian_links_count: number;
    staff_attendance_records_count: number;
  };
};

export default function SchoolStudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [guardians, setGuardians] = useState<Guardian[]>([]);
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [overviewData, studentData, guardianData, attendanceData] = await Promise.all([
        apiGet<Overview>("/api/v1/school-core/overview"),
        apiGet<Student[]>("/api/v1/school-core/students?limit=300"),
        apiGet<Guardian[]>("/api/v1/school-core/guardians?limit=300"),
        apiGet<AttendanceRecord[]>("/api/v1/school-core/attendance?limit=200")
      ]);
      setOverview(overviewData);
      setStudents(studentData);
      setGuardians(guardianData);
      setAttendance(attendanceData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "فشل تحميل عمليات المدرسة");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <SchoolShell>
      <section className="hero surface school-core-hero">
        <div>
          <div className="eyebrow">SCHOOL CORE · READ ONLY</div>
          <h1>الطلاب وأولياء الأمور والحضور</h1>
          <p>
            شاشة تشغيل للقراءة فقط تعرض ملف الطالب وروابط أولياء الأمور وحضور الموظفين المتاح حاليًا.
            هذه المرحلة لا تضيف جداول ولا تكتب في قاعدة البيانات.
          </p>
        </div>
        <div className="hero-actions">
          <button className="btn" type="button" onClick={load} disabled={loading}>
            {loading ? "جاري التحديث..." : "تحديث"}
          </button>
          <Link href="/school" className="btn btn-secondary">رجوع لعمليات المدرسة</Link>
        </div>
      </section>

      {error ? <div className="error mt">{error}</div> : null}

      <section className="grid stats mt school-core-stats">
        <div className="metric"><span>الطلاب</span><strong>{overview?.counts.students_count ?? students.length}</strong></div>
        <div className="metric"><span>أولياء الأمور</span><strong>{overview?.counts.guardians_count ?? guardians.length}</strong></div>
        <div className="metric"><span>روابط طالب/ولي أمر</span><strong>{overview?.counts.student_guardian_links_count ?? 0}</strong></div>
        <div className="metric"><span>سجلات حضور الموظفين</span><strong>{overview?.counts.staff_attendance_records_count ?? attendance.length}</strong></div>
      </section>

      <section className="surface section-pad mt">
        <div className="studio-toolbar">
          <div>
            <h2>ملف الطلاب</h2>
            <p className="muted">مصدر البيانات: school.students مع ربط school.guardians عند وجوده.</p>
          </div>
          <span className="badge">read-only</span>
        </div>

        <div className="table-wrap mt-small">
          <table>
            <thead>
              <tr>
                <th>كود Access</th>
                <th>الرقم القومي</th>
                <th>اسم الطالب</th>
                <th>الفصل</th>
                <th>الصف</th>
                <th>أولياء الأمور</th>
                <th>الحالة</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr key={student.id}>
                  <td>{student.legacy_access_id || "—"}</td>
                  <td>{student.national_id || "—"}</td>
                  <td><strong>{student.student_name_ar}</strong></td>
                  <td>{student.class_name || "—"}</td>
                  <td>{student.grade_name_ar || "—"}</td>
                  <td>
                    {student.guardians?.length ? (
                      <div className="school-core-inline-list">
                        {student.guardians.map((guardian) => (
                          <span key={guardian.id}>
                            {guardian.full_name_ar}
                            {guardian.relation_type ? ` · ${guardian.relation_type}` : ""}
                          </span>
                        ))}
                      </div>
                    ) : "—"}
                  </td>
                  <td>{student.enrollment_status}</td>
                </tr>
              ))}
              {!students.length ? (
                <tr><td colSpan={7}>لا توجد بيانات طلاب للعرض.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="surface section-pad mt">
        <div className="studio-toolbar">
          <div>
            <h2>أولياء الأمور</h2>
            <p className="muted">مصدر البيانات: school.guardians و school.student_guardians.</p>
          </div>
          <span className="badge">read-only</span>
        </div>

        <div className="table-wrap mt-small">
          <table>
            <thead>
              <tr>
                <th>الاسم</th>
                <th>الرقم القومي</th>
                <th>الهاتف</th>
                <th>الصفة</th>
                <th>الطلاب المرتبطون</th>
              </tr>
            </thead>
            <tbody>
              {guardians.map((guardian) => (
                <tr key={guardian.id}>
                  <td><strong>{guardian.full_name_ar}</strong></td>
                  <td>{guardian.national_id || "—"}</td>
                  <td>{guardian.phone || "—"}</td>
                  <td>{guardian.relation_type || "—"}</td>
                  <td>
                    {guardian.students?.length ? (
                      <div className="school-core-inline-list">
                        {guardian.students.map((student) => (
                          <span key={student.id}>
                            {student.student_name_ar}
                            {student.class_name ? ` · ${student.class_name}` : ""}
                          </span>
                        ))}
                      </div>
                    ) : "—"}
                  </td>
                </tr>
              ))}
              {!guardians.length ? (
                <tr><td colSpan={5}>لا توجد بيانات أولياء أمور للعرض.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="surface section-pad mt">
        <div className="studio-toolbar">
          <div>
            <h2>حضور الموظفين الحالي</h2>
            <p className="muted">
              الجدول الموجود حاليًا هو hr.attendance_records للموظفين. حضور الطلاب يحتاج قرار DB مستقل لاحقًا.
            </p>
          </div>
          <span className="badge">no student attendance table yet</span>
        </div>

        <div className="table-wrap mt-small">
          <table>
            <thead>
              <tr>
                <th>الموظف</th>
                <th>رقم الموظف</th>
                <th>التاريخ</th>
                <th>دخول</th>
                <th>خروج</th>
                <th>الحالة</th>
                <th>ملاحظات</th>
              </tr>
            </thead>
            <tbody>
              {attendance.map((row) => (
                <tr key={row.id}>
                  <td><strong>{row.employee_name_ar}</strong></td>
                  <td>{row.employee_no || "—"}</td>
                  <td>{row.attendance_date}</td>
                  <td>{row.check_in || "—"}</td>
                  <td>{row.check_out || "—"}</td>
                  <td>{row.status}</td>
                  <td>{row.notes || "—"}</td>
                </tr>
              ))}
              {!attendance.length ? (
                <tr><td colSpan={7}>لا توجد سجلات حضور موظفين للعرض.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="surface section-pad mt">
        <h2>تعهدات الأمان في Phase 8D</h2>
        <div className="list">
          <span>database_impact=None</span>
          <span>database_writes_performed=False</span>
          <span>migrations_run=False</span>
          <span>source scope: school-core read-only API + UI only</span>
          <span>safe_to_import_slots=False</span>
          <span>ROZ slot import remains blocked</span>
        </div>
      </section>
    </SchoolShell>
  );
}
