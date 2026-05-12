"use client";

import { useEffect, useMemo, useState } from "react";

type Row = Record<string, any>;

const sampleCsv = `day,period,class,subject,teacher,room
الأحد,1,1A,لغة عربية,أحمد محمد,فصل 1
الأحد,2,1A,رياضيات,منى علي,فصل 1
الإثنين,1,1A,علوم,سعيد حسن,معمل علوم`;

const API = "/api/timetable";

async function apiGet<T = any>(path: string): Promise<T> {
  const res = await fetch(`${API}/${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiPost<T = any>(path: string, body: any = {}): Promise<T> {
  const res = await fetch(`${API}/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function value(row: Row | null | undefined, key: string, fallback = "—") {
  const v = row?.[key];
  return v === null || v === undefined || v === "" ? fallback : String(v);
}

function Metric({ label, value: v }: { label: string; value: any }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{v ?? 0}</strong>
    </div>
  );
}

function SmallTable({
  rows,
  columns,
  empty,
}: {
  rows: Row[];
  columns: { key: string; label: string }[];
  empty: string;
}) {
  if (!rows.length) return <p>{empty}</p>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={String(row.id ?? idx)}>
              {columns.map((c) => (
                <td key={c.key}>{value(row, c.key)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function TimetablePage() {
  const [summary, setSummary] = useState<Row | null>(null);
  const [readiness, setReadiness] = useState<Row | null>(null);
  const [quality, setQuality] = useState<Row[]>([]);
  const [grid, setGrid] = useState<Row[]>([]);
  const [teacherLoad, setTeacherLoad] = useState<Row[]>([]);
  const [conflicts, setConflicts] = useState<Row[]>([]);
  const [versions, setVersions] = useState<Row[]>([]);
  const [runs, setRuns] = useState<Row[]>([]);

  const [teachers, setTeachers] = useState<Row[]>([]);
  const [subjects, setSubjects] = useState<Row[]>([]);
  const [classes, setClasses] = useState<Row[]>([]);
  const [classrooms, setClassrooms] = useState<Row[]>([]);
  const [periods, setPeriods] = useState<Row[]>([]);
  const [weekDays, setWeekDays] = useState<Row[]>([]);
  const [plans, setPlans] = useState<Row[]>([]);
  const [constraints, setConstraints] = useState<Row[]>([]);

  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("جاهز للعمل");
  const [csv, setCsv] = useState(sampleCsv);

  const [teacherForm, setTeacherForm] = useState({
    teacher_code: "",
    teacher_name_ar: "",
    phone: "",
    specialization: "",
  });
  const [subjectForm, setSubjectForm] = useState({
    subject_code: "",
    subject_name_ar: "",
    color_code: "#8b5e34",
  });
  const [classForm, setClassForm] = useState({
    class_code: "",
    class_name_ar: "",
    stage_name_ar: "",
    grade_name_ar: "",
    capacity: 0,
  });
  const [roomForm, setRoomForm] = useState({
    room_code: "",
    room_name_ar: "",
    capacity: 0,
    floor_name: "",
  });
  const [periodForm, setPeriodForm] = useState({
    period_no: 1,
    name_ar: "الحصة 1",
    starts_at: "08:00",
    ends_at: "08:45",
    is_break: false,
  });
  const [planForm, setPlanForm] = useState({
    school_class_id: "",
    subject_id: "",
    teacher_id: "",
    classroom_id: "",
    weekly_lessons: 1,
    priority: 100,
  });
  const [constraintForm, setConstraintForm] = useState({
    constraint_type: "hard",
    target_scope: "teacher",
    target_id: "",
    rule_code: "manual_rule",
    rule_payload: "{}",
    weight: 10,
  });
  const [versionForm, setVersionForm] = useState({
    name_ar: "نسخة جدول جديدة",
    is_current: true,
  });
  const [slotForm, setSlotForm] = useState({
    timetable_version_id: "",
    school_class_id: "",
    week_day_id: 2,
    period_id: "",
    subject_name_ar: "",
    teacher_id: "",
    classroom_id: "",
    notes: "",
  });
  const [runForm, setRunForm] = useState({
    name_ar: "توليد آلي من Curriculum Matrix",
    clear_existing: true,
    make_current: true,
  });

  async function refresh() {
    const [
      s,
      r,
      q,
      g,
      tl,
      cf,
      vs,
      rn,
      t,
      sub,
      cls,
      rooms,
      pr,
      days,
      cp,
      cons,
    ] = await Promise.all([
      apiGet("summary"),
      apiGet("readiness"),
      apiGet("quality"),
      apiGet("grid"),
      apiGet("teacher-load"),
      apiGet("conflicts"),
      apiGet("versions"),
      apiGet("runs"),
      apiGet("teachers"),
      apiGet("subjects"),
      apiGet("classes"),
      apiGet("classrooms"),
      apiGet("periods"),
      apiGet("week-days"),
      apiGet("curriculum-plans"),
      apiGet("constraints"),
    ]);

    setSummary(s);
    setReadiness(r);
    setQuality(q);
    setGrid(g);
    setTeacherLoad(tl);
    setConflicts(cf);
    setVersions(vs);
    setRuns(rn);
    setTeachers(t);
    setSubjects(sub);
    setClasses(cls);
    setClassrooms(rooms);
    setPeriods(pr);
    setWeekDays(days);
    setPlans(cp);
    setConstraints(cons);

    setPlanForm((old) => ({
      ...old,
      school_class_id: old.school_class_id || cls?.[0]?.id || "",
      subject_id: old.subject_id || sub?.[0]?.id || "",
      teacher_id: old.teacher_id || t?.[0]?.id || "",
      classroom_id: old.classroom_id || rooms?.[0]?.id || "",
    }));
    setSlotForm((old) => ({
      ...old,
      timetable_version_id: old.timetable_version_id || vs?.[0]?.id || "",
      school_class_id: old.school_class_id || cls?.[0]?.id || "",
      period_id: old.period_id || pr?.[0]?.id || "",
      teacher_id: old.teacher_id || t?.[0]?.id || "",
      classroom_id: old.classroom_id || rooms?.[0]?.id || "",
      subject_name_ar: old.subject_name_ar || sub?.[0]?.subject_name_ar || "",
      week_day_id: old.week_day_id || days?.[0]?.id || 2,
    }));
  }

  async function action(label: string, fn: () => Promise<any>) {
    setBusy(true);
    setNotice(`جاري التنفيذ: ${label}`);
    try {
      const result = await fn();
      setNotice(`${label}: تم بنجاح`);
      await refresh();
      return result;
    } catch (err: any) {
      setNotice(`${label}: فشل - ${err?.message || String(err)}`);
      throw err;
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    refresh().catch((err) => setNotice(`فشل تحميل البيانات: ${err.message}`));
  }, []);

  const currentVersion = useMemo(
    () => versions.find((v) => v.is_current) || versions[0],
    [versions],
  );

  async function chooseFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setCsv(await file.text());
  }

  async function importCsv() {
    await action("استيراد CSV", () =>
      apiPost("import/time-table-csv", {
        batch_name: "استيراد من واجهة Phase 3",
        csv_text: csv,
      }),
    );
  }

  async function exportCsv() {
    const result = await action("تصدير CSV", () => apiPost("exports/csv"));
    const blob = new Blob([result.csv_text || ""], {
      type: result.content_type || "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = result.file_name || "school-timetable.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  async function createConstraint() {
    let parsed: Row = {};
    try {
      parsed = JSON.parse(constraintForm.rule_payload || "{}");
    } catch {
      throw new Error("rule_payload يجب أن يكون JSON صحيح");
    }
    await action("إضافة قيد", () =>
      apiPost("constraints", {
        ...constraintForm,
        target_id: constraintForm.target_id || null,
        rule_payload: parsed,
        weight: Number(constraintForm.weight || 10),
      }),
    );
  }

  async function createSlot() {
    await action("إضافة حصة يدوية", () =>
      apiPost("slots", {
        timetable_version_id: slotForm.timetable_version_id || null,
        school_class_id: slotForm.school_class_id,
        week_day_id: Number(slotForm.week_day_id),
        period_id: slotForm.period_id,
        subject_name_ar: slotForm.subject_name_ar,
        teacher_id: slotForm.teacher_id || null,
        classroom_id: slotForm.classroom_id || null,
        notes: slotForm.notes || null,
      }),
    );
  }

  return (
    <main>
      <header className="header">
        <div className="container header-inner">
          <a className="brand" href="/">
            <span className="logo">MK</span>
            <span>
              <strong style={{ display: "block" }}>ERP تعليمي موحد</strong>
              <small>Core + HR + School + Timetable + Control</small>
            </span>
          </a>
          <nav className="nav">
            <a href="/platform">النواة المشتركة</a>
            <a href="/hr">برنامج الموظفين</a>
            <a href="/school">برنامج المدارس</a>
            <a href="/timetable">الجدول المدرسي</a>
            <a href="/education-control">برنامج الكنترول</a>
          </nav>
        </div>
      </header>

      <div className="container page">
        <section className="hero surface">
          <div>
            <div className="eyebrow">Phase 3 Timetable Builder</div>
            <h1>منصة بناء الجداول المدرسية</h1>
            <p>
              إدارة الموارد، الخطة الأسبوعية، القيود، الاستيراد، التوليد، المراجعة،
              الاعتماد والنشر من شاشة تشغيل واحدة.
            </p>
          </div>
          <div className="hero-actions">
            <span className="badge">{readiness?.ready ? "جاهز" : "غير مكتمل"}</span>
            <button className="btn btn-secondary" disabled={busy} onClick={() => action("تحديث البيانات", refresh)}>
              تحديث
            </button>
            <button className="btn" disabled={busy} onClick={() => action("تجهيز الأيام والحصص", () => apiPost("bootstrap"))}>
              تجهيز أساسي
            </button>
          </div>
        </section>

        <section className="surface section-pad mt">
          <strong>الحالة:</strong> {notice}
        </section>

        <section className="grid stats mt">
          <Metric label="مدرسون" value={summary?.teachers_count} />
          <Metric label="مرتبطون HR" value={summary?.hr_linked_teachers_count} />
          <Metric label="فصول" value={summary?.classes_count} />
          <Metric label="مواد" value={summary?.subjects_count} />
          <Metric label="خطة أسبوعية" value={summary?.planned_weekly_lessons_count} />
          <Metric label="قاعات" value={summary?.classrooms_count} />
          <Metric label="حصص اليوم" value={summary?.periods_count} />
          <Metric label="نسخ الجدول" value={summary?.versions_count} />
          <Metric label="دروس الجدول" value={summary?.slots_count} />
          <Metric label="تعارضات صارمة" value={summary?.hard_conflicts_count} />
        </section>

        <section className="split mt">
          <div className="surface section-pad">
            <h2>جاهزية التنفيذ</h2>
            <div className="check-list">
              {(readiness?.checks || []).map((check: Row) => (
                <div className="check-row" key={check.code}>
                  <span className={check.ready ? "badge" : "badge danger"}>{check.ready ? "جاهز" : "ناقص"}</span>
                  <strong>{check.name_ar}</strong>
                  <small>{check.message_ar}</small>
                </div>
              ))}
            </div>
          </div>

          <div className="surface section-pad">
            <h2>تشغيل الوثيقة</h2>
            <div className="action-stack">
              <button className="btn" disabled={busy} onClick={() => action("مزامنة المدرسين من HR", () => apiPost("sync/hr-teachers"))}>
                مزامنة المدرسين من HR
              </button>
              <button className="btn btn-secondary" disabled={busy} onClick={() => action("تشغيل Validation", () => apiPost("validation/run"))}>
                فحص الجاهزية والقيود
              </button>
              <button className="btn btn-secondary" disabled={busy} onClick={exportCsv}>
                تصدير CSV
              </button>
            </div>
            <p>لا يتم الاعتماد أو النشر عند وجود تعارضات صارمة.</p>
          </div>
        </section>

        <section className="split mt">
          <div className="surface section-pad">
            <h2>إضافة مدرس</h2>
            <input className="input" placeholder="كود المدرس" value={teacherForm.teacher_code} onChange={(e) => setTeacherForm({ ...teacherForm, teacher_code: e.target.value })} />
            <input className="input mt-small" placeholder="اسم المدرس" value={teacherForm.teacher_name_ar} onChange={(e) => setTeacherForm({ ...teacherForm, teacher_name_ar: e.target.value })} />
            <input className="input mt-small" placeholder="الهاتف" value={teacherForm.phone} onChange={(e) => setTeacherForm({ ...teacherForm, phone: e.target.value })} />
            <input className="input mt-small" placeholder="التخصص" value={teacherForm.specialization} onChange={(e) => setTeacherForm({ ...teacherForm, specialization: e.target.value })} />
            <button className="btn mt-small" disabled={busy || !teacherForm.teacher_name_ar} onClick={() => action("إضافة مدرس", () => apiPost("teachers", { ...teacherForm, teacher_code: teacherForm.teacher_code || null, phone: teacherForm.phone || null, specialization: teacherForm.specialization || null }))}>
              حفظ المدرس
            </button>
            <SmallTable rows={teachers.slice(0, 8)} empty="لا توجد بيانات مدرسين" columns={[
              { key: "teacher_code", label: "الكود" },
              { key: "teacher_name_ar", label: "المدرس" },
              { key: "specialization", label: "التخصص" },
            ]} />
          </div>

          <div className="surface section-pad">
            <h2>إضافة مادة</h2>
            <input className="input" placeholder="كود المادة" value={subjectForm.subject_code} onChange={(e) => setSubjectForm({ ...subjectForm, subject_code: e.target.value })} />
            <input className="input mt-small" placeholder="اسم المادة" value={subjectForm.subject_name_ar} onChange={(e) => setSubjectForm({ ...subjectForm, subject_name_ar: e.target.value })} />
            <input className="input mt-small" placeholder="لون المادة" value={subjectForm.color_code} onChange={(e) => setSubjectForm({ ...subjectForm, color_code: e.target.value })} />
            <button className="btn mt-small" disabled={busy || !subjectForm.subject_name_ar} onClick={() => action("إضافة مادة", () => apiPost("subjects", { ...subjectForm, subject_code: subjectForm.subject_code || null, color_code: subjectForm.color_code || null }))}>
              حفظ المادة
            </button>
            <SmallTable rows={subjects.slice(0, 8)} empty="لا توجد مواد" columns={[
              { key: "subject_code", label: "الكود" },
              { key: "subject_name_ar", label: "المادة" },
              { key: "color_code", label: "اللون" },
            ]} />
          </div>
        </section>

        <section className="split mt">
          <div className="surface section-pad">
            <h2>إضافة فصل</h2>
            <input className="input" placeholder="كود الفصل مثل 1A" value={classForm.class_code} onChange={(e) => setClassForm({ ...classForm, class_code: e.target.value })} />
            <input className="input mt-small" placeholder="اسم الفصل" value={classForm.class_name_ar} onChange={(e) => setClassForm({ ...classForm, class_name_ar: e.target.value })} />
            <input className="input mt-small" placeholder="المرحلة" value={classForm.stage_name_ar} onChange={(e) => setClassForm({ ...classForm, stage_name_ar: e.target.value })} />
            <input className="input mt-small" placeholder="الصف" value={classForm.grade_name_ar} onChange={(e) => setClassForm({ ...classForm, grade_name_ar: e.target.value })} />
            <input className="input mt-small" type="number" placeholder="السعة" value={classForm.capacity} onChange={(e) => setClassForm({ ...classForm, capacity: Number(e.target.value) })} />
            <button className="btn mt-small" disabled={busy || !classForm.class_code || !classForm.class_name_ar} onClick={() => action("إضافة فصل", () => apiPost("classes", { ...classForm, stage_name_ar: classForm.stage_name_ar || null, grade_name_ar: classForm.grade_name_ar || null }))}>
              حفظ الفصل
            </button>
            <SmallTable rows={classes.slice(0, 8)} empty="لا توجد فصول" columns={[
              { key: "class_code", label: "الكود" },
              { key: "class_name_ar", label: "الفصل" },
              { key: "capacity", label: "السعة" },
            ]} />
          </div>

          <div className="surface section-pad">
            <h2>إضافة قاعة</h2>
            <input className="input" placeholder="كود القاعة" value={roomForm.room_code} onChange={(e) => setRoomForm({ ...roomForm, room_code: e.target.value })} />
            <input className="input mt-small" placeholder="اسم القاعة" value={roomForm.room_name_ar} onChange={(e) => setRoomForm({ ...roomForm, room_name_ar: e.target.value })} />
            <input className="input mt-small" type="number" placeholder="السعة" value={roomForm.capacity} onChange={(e) => setRoomForm({ ...roomForm, capacity: Number(e.target.value) })} />
            <input className="input mt-small" placeholder="الدور" value={roomForm.floor_name} onChange={(e) => setRoomForm({ ...roomForm, floor_name: e.target.value })} />
            <button className="btn mt-small" disabled={busy || !roomForm.room_code || !roomForm.room_name_ar} onClick={() => action("إضافة قاعة", () => apiPost("classrooms", { ...roomForm, floor_name: roomForm.floor_name || null }))}>
              حفظ القاعة
            </button>
            <SmallTable rows={classrooms.slice(0, 8)} empty="لا توجد قاعات" columns={[
              { key: "room_code", label: "الكود" },
              { key: "room_name_ar", label: "القاعة" },
              { key: "capacity", label: "السعة" },
            ]} />
          </div>
        </section>

        <section className="split mt">
          <div className="surface section-pad">
            <h2>إضافة حصة زمنية</h2>
            <input className="input" type="number" value={periodForm.period_no} onChange={(e) => setPeriodForm({ ...periodForm, period_no: Number(e.target.value) })} />
            <input className="input mt-small" placeholder="اسم الحصة" value={periodForm.name_ar} onChange={(e) => setPeriodForm({ ...periodForm, name_ar: e.target.value })} />
            <input className="input mt-small" type="time" value={periodForm.starts_at} onChange={(e) => setPeriodForm({ ...periodForm, starts_at: e.target.value })} />
            <input className="input mt-small" type="time" value={periodForm.ends_at} onChange={(e) => setPeriodForm({ ...periodForm, ends_at: e.target.value })} />
            <label className="mt-small">
              <input type="checkbox" checked={periodForm.is_break} onChange={(e) => setPeriodForm({ ...periodForm, is_break: e.target.checked })} /> فسحة
            </label>
            <button className="btn mt-small" disabled={busy} onClick={() => action("إضافة حصة زمنية", () => apiPost("periods", periodForm))}>
              حفظ الحصة
            </button>
            <SmallTable rows={periods} empty="لا توجد حصص" columns={[
              { key: "period_no", label: "رقم" },
              { key: "name_ar", label: "الحصة" },
              { key: "starts_at", label: "من" },
              { key: "ends_at", label: "إلى" },
            ]} />
          </div>

          <div className="surface section-pad">
            <h2>إنشاء نسخة جدول</h2>
            <input className="input" placeholder="اسم النسخة" value={versionForm.name_ar} onChange={(e) => setVersionForm({ ...versionForm, name_ar: e.target.value })} />
            <label className="mt-small">
              <input type="checkbox" checked={versionForm.is_current} onChange={(e) => setVersionForm({ ...versionForm, is_current: e.target.checked })} /> اجعلها الحالية
            </label>
            <button className="btn mt-small" disabled={busy || !versionForm.name_ar} onClick={() => action("إنشاء نسخة", () => apiPost("versions", versionForm))}>
              حفظ النسخة
            </button>
            <SmallTable rows={versions.slice(0, 8)} empty="لا توجد نسخ" columns={[
              { key: "name_ar", label: "النسخة" },
              { key: "status", label: "الحالة" },
              { key: "is_current", label: "حالية" },
            ]} />
          </div>
        </section>

        <section className="surface section-pad mt">
          <h2>Curriculum Matrix / الخطة الأسبوعية</h2>
          <div className="grid form-grid">
            <select className="input" value={planForm.school_class_id} onChange={(e) => setPlanForm({ ...planForm, school_class_id: e.target.value })}>
              <option value="">اختر الفصل</option>
              {classes.map((x) => <option key={x.id} value={x.id}>{x.class_code} - {x.class_name_ar}</option>)}
            </select>
            <select className="input" value={planForm.subject_id} onChange={(e) => setPlanForm({ ...planForm, subject_id: e.target.value })}>
              <option value="">اختر المادة</option>
              {subjects.map((x) => <option key={x.id} value={x.id}>{x.subject_name_ar}</option>)}
            </select>
            <select className="input" value={planForm.teacher_id} onChange={(e) => setPlanForm({ ...planForm, teacher_id: e.target.value })}>
              <option value="">بدون مدرس</option>
              {teachers.map((x) => <option key={x.id} value={x.id}>{x.teacher_name_ar}</option>)}
            </select>
            <select className="input" value={planForm.classroom_id} onChange={(e) => setPlanForm({ ...planForm, classroom_id: e.target.value })}>
              <option value="">بدون قاعة</option>
              {classrooms.map((x) => <option key={x.id} value={x.id}>{x.room_name_ar || x.name_ar}</option>)}
            </select>
            <input className="input" type="number" min={1} placeholder="عدد الحصص أسبوعيًا" value={planForm.weekly_lessons} onChange={(e) => setPlanForm({ ...planForm, weekly_lessons: Number(e.target.value) })} />
            <input className="input" type="number" placeholder="الأولوية" value={planForm.priority} onChange={(e) => setPlanForm({ ...planForm, priority: Number(e.target.value) })} />
          </div>
          <button className="btn mt-small" disabled={busy || !planForm.school_class_id || !planForm.subject_id} onClick={() => action("حفظ خطة أسبوعية", () => apiPost("curriculum-plans", { ...planForm, teacher_id: planForm.teacher_id || null, classroom_id: planForm.classroom_id || null }))}>
            حفظ الخطة
          </button>
          <SmallTable rows={plans} empty="لا توجد خطة أسبوعية" columns={[
            { key: "class_code", label: "الفصل" },
            { key: "subject_name_ar", label: "المادة" },
            { key: "teacher_name_ar", label: "المدرس" },
            { key: "room_name_ar", label: "القاعة" },
            { key: "weekly_lessons", label: "أسبوعيًا" },
            { key: "priority", label: "أولوية" },
          ]} />
        </section>

        <section className="split mt">
          <div className="surface section-pad">
            <h2>القيود Hard / Soft</h2>
            <select className="input" value={constraintForm.constraint_type} onChange={(e) => setConstraintForm({ ...constraintForm, constraint_type: e.target.value })}>
              <option value="hard">Hard</option>
              <option value="soft">Soft</option>
            </select>
            <input className="input mt-small" placeholder="target_scope مثل teacher/class/room" value={constraintForm.target_scope} onChange={(e) => setConstraintForm({ ...constraintForm, target_scope: e.target.value })} />
            <input className="input mt-small" placeholder="target_id اختياري UUID" value={constraintForm.target_id} onChange={(e) => setConstraintForm({ ...constraintForm, target_id: e.target.value })} />
            <input className="input mt-small" placeholder="rule_code" value={constraintForm.rule_code} onChange={(e) => setConstraintForm({ ...constraintForm, rule_code: e.target.value })} />
            <textarea className="input csv-area" value={constraintForm.rule_payload} onChange={(e) => setConstraintForm({ ...constraintForm, rule_payload: e.target.value })} />
            <input className="input mt-small" type="number" value={constraintForm.weight} onChange={(e) => setConstraintForm({ ...constraintForm, weight: Number(e.target.value) })} />
            <button className="btn mt-small" disabled={busy} onClick={createConstraint}>حفظ القيد</button>
          </div>

          <div className="surface section-pad">
            <h2>تشغيل التوليد</h2>
            <input className="input" value={runForm.name_ar} onChange={(e) => setRunForm({ ...runForm, name_ar: e.target.value })} />
            <label className="mt-small">
              <input type="checkbox" checked={runForm.clear_existing} onChange={(e) => setRunForm({ ...runForm, clear_existing: e.target.checked })} /> حذف حصص النسخة قبل التوليد
            </label>
            <label className="mt-small">
              <input type="checkbox" checked={runForm.make_current} onChange={(e) => setRunForm({ ...runForm, make_current: e.target.checked })} /> اجعل النسخة Current
            </label>
            <button className="btn mt-small" disabled={busy} onClick={() => action("توليد الجدول", () => apiPost("runs", runForm))}>
              توليد من Curriculum Matrix
            </button>
            <SmallTable rows={runs.slice(0, 6)} empty="لا توجد تشغيلات توليد" columns={[
              { key: "status", label: "الحالة" },
              { key: "total_cards", label: "المطلوب" },
              { key: "scheduled_lessons", label: "المجدول" },
              { key: "quality_score", label: "الجودة" },
            ]} />
          </div>
        </section>

        <section className="surface section-pad mt">
          <h2>إضافة حصة يدوية</h2>
          <div className="grid form-grid">
            <select className="input" value={slotForm.timetable_version_id} onChange={(e) => setSlotForm({ ...slotForm, timetable_version_id: e.target.value })}>
              <option value="">النسخة الحالية تلقائيًا</option>
              {versions.map((x) => <option key={x.id} value={x.id}>{x.name_ar} - {x.status}</option>)}
            </select>
            <select className="input" value={slotForm.school_class_id} onChange={(e) => setSlotForm({ ...slotForm, school_class_id: e.target.value })}>
              <option value="">اختر الفصل</option>
              {classes.map((x) => <option key={x.id} value={x.id}>{x.class_code}</option>)}
            </select>
            <select className="input" value={slotForm.week_day_id} onChange={(e) => setSlotForm({ ...slotForm, week_day_id: Number(e.target.value) })}>
              {weekDays.map((x) => <option key={x.id} value={x.id}>{x.name_ar}</option>)}
            </select>
            <select className="input" value={slotForm.period_id} onChange={(e) => setSlotForm({ ...slotForm, period_id: e.target.value })}>
              <option value="">اختر الحصة</option>
              {periods.map((x) => <option key={x.id} value={x.id}>{x.period_no} - {x.name_ar}</option>)}
            </select>
            <input className="input" placeholder="اسم المادة" value={slotForm.subject_name_ar} onChange={(e) => setSlotForm({ ...slotForm, subject_name_ar: e.target.value })} />
            <select className="input" value={slotForm.teacher_id} onChange={(e) => setSlotForm({ ...slotForm, teacher_id: e.target.value })}>
              <option value="">بدون مدرس</option>
              {teachers.map((x) => <option key={x.id} value={x.id}>{x.teacher_name_ar}</option>)}
            </select>
            <select className="input" value={slotForm.classroom_id} onChange={(e) => setSlotForm({ ...slotForm, classroom_id: e.target.value })}>
              <option value="">بدون قاعة</option>
              {classrooms.map((x) => <option key={x.id} value={x.id}>{x.room_name_ar || x.name_ar}</option>)}
            </select>
            <input className="input" placeholder="ملاحظات" value={slotForm.notes} onChange={(e) => setSlotForm({ ...slotForm, notes: e.target.value })} />
          </div>
          <button className="btn mt-small" disabled={busy || !slotForm.school_class_id || !slotForm.period_id || !slotForm.subject_name_ar} onClick={createSlot}>
            حفظ الحصة اليدوية
          </button>
        </section>

        <section className="split mt">
          <div className="surface section-pad">
            <h2>دورة الاعتماد والنشر</h2>
            <p>النسخة الحالية: {currentVersion ? `${currentVersion.name_ar} / ${currentVersion.status}` : "لا توجد نسخة"}</p>
            <div className="action-stack">
              <button className="btn btn-secondary" disabled={busy || !currentVersion?.id} onClick={() => action("اعتماد النسخة", () => apiPost(`versions/${currentVersion.id}/approve`))}>
                اعتماد
              </button>
              <button className="btn" disabled={busy || !currentVersion?.id} onClick={() => action("نشر النسخة", () => apiPost(`versions/${currentVersion.id}/publish`))}>
                نشر
              </button>
              <button className="btn btn-secondary" disabled={busy || !currentVersion?.id} onClick={() => action("أرشفة النسخة", () => apiPost(`versions/${currentVersion.id}/archive`))}>
                أرشفة
              </button>
            </div>
          </div>

          <div className="surface section-pad">
            <h2>Quality Score</h2>
            <SmallTable rows={quality} empty="لا توجد بيانات جودة" columns={[
              { key: "timetable_name_ar", label: "النسخة" },
              { key: "status", label: "الحالة" },
              { key: "quality_score", label: "الجودة" },
              { key: "hard_conflicts", label: "Hard" },
              { key: "soft_warnings", label: "Soft" },
            ]} />
          </div>
        </section>

        <section className="surface section-pad mt">
          <h2>استيراد TimeTable CSV</h2>
          <input className="input mt-small" type="file" accept=".csv,.txt,text/csv" onChange={chooseFile} />
          <textarea className="input csv-area" value={csv} onChange={(e) => setCsv(e.target.value)} />
          <button className="btn" disabled={busy || !csv.trim()} onClick={importCsv}>استيراد الجدول</button>
        </section>

        <section className="surface section-pad mt">
          <h2>جدول الحصص</h2>
          <SmallTable rows={grid} empty="لا توجد دروس بعد" columns={[
            { key: "day_name_ar", label: "اليوم" },
            { key: "period_no", label: "الحصة" },
            { key: "class_code", label: "الفصل" },
            { key: "subject_name_ar", label: "المادة" },
            { key: "teacher_name_ar", label: "المدرس" },
            { key: "room_name_ar", label: "القاعة" },
          ]} />
        </section>

        <section className="split mt">
          <div className="surface section-pad">
            <h2>التعارضات</h2>
            <SmallTable rows={conflicts} empty="لا توجد تعارضات" columns={[
              { key: "severity", label: "الخطورة" },
              { key: "conflict_type", label: "النوع" },
              { key: "message_ar", label: "الرسالة" },
            ]} />
          </div>

          <div className="surface section-pad">
            <h2>نصاب المدرسين</h2>
            <SmallTable rows={teacherLoad} empty="لا توجد بيانات نصاب" columns={[
              { key: "teacher_name_ar", label: "المدرس" },
              { key: "weekly_lessons_count", label: "حصص أسبوعيًا" },
            ]} />
          </div>
        </section>

        <section className="surface section-pad mt">
          <h2>قائمة القيود</h2>
          <SmallTable rows={constraints} empty="لا توجد قيود مخصصة" columns={[
            { key: "constraint_type", label: "النوع" },
            { key: "target_scope", label: "النطاق" },
            { key: "rule_code", label: "الكود" },
            { key: "weight", label: "الوزن" },
          ]} />
        </section>
      </div>
    </main>
  );
}
