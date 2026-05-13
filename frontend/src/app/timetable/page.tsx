"use client";

import { useEffect, useMemo, useState } from "react";

type Row = Record<string, any>;

const sampleCsv = `day,period,class,subject,teacher,room
الأحد,1,1A,لغة عربية,أحمد محمد,فصل 1
الأحد,2,1A,رياضيات,منى علي,فصل 1
الإثنين,1,1A,علوم,سعيد حسن,معمل علوم
`;

async function apiGet(path: string) {
  const res = await fetch(`/api/timetable/${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiPost(path: string, body: any = {}) {
  const res = await fetch(`/api/timetable/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiDelete(path: string) {
  const res = await fetch(`/api/timetable/${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function text(v: any) {
  if (v === null || v === undefined || v === "") return "—";
  return String(v);
}

function Metric({ label, value }: { label: string; value: any }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value ?? 0}</strong>
    </div>
  );
}

function cleanupLabel(key: string) {
  const labels: Record<string, string> = {
    teachers: "مدرسون",
    subjects: "مواد",
    classes: "فصول",
    classrooms: "قاعات",
    constraints: "قيود",
    versions: "نسخ جدول",
    slots_by_content: "حصص بعلامات اختبار",
    slots_by_version: "حصص داخل نسخ اختبار",
    generation_runs_by_version: "تشغيلات توليد",
    export_jobs_by_version: "مهام تصدير",
  };
  return labels[key] || key;
}

function cleanupPreviewText(value: any) {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function StatusBadge({ status }: { status: string }) {
  const label =
    status === "published" ? "منشور" :
    status === "approved" ? "معتمد" :
    status === "archived" ? "مؤرشف" :
    status === "generation" ? "توليد" :
    "مسودة";

  return <span className={`badge status-${status || "draft"}`}>{label}</span>;
}

function SmallTable({
  rows,
  columns,
  empty,
}: {
  rows: Row[];
  columns: { key: string; label: string; render?: (row: Row) => any }[];
  empty: string;
}) {
  if (!rows.length) return <p className="muted">{empty}</p>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((c) => <th key={c.key}>{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id || i}>
              {columns.map((c) => (
                <td key={c.key}>{c.render ? c.render(row) : text(row[c.key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


type RozCanonicalTeacher = {
  teacher_name_ar: string;
  confidence?: number;
  offset?: number;
  source_kind?: string;
};

type RozCanonicalSubject = {
  subject_name_ar: string;
  confidence?: number;
  offset?: number;
  source_kind?: string;
};

type RozInspectResult = {
  file_name?: string;
  file_size?: number;
  sha256?: string;
  safe_to_import?: boolean;
  parser_stage?: string;
  detected?: {
    academic_years?: string[];
    periods?: string[];
    classes?: string[];
  };
  semantic_preview?: {
    period_labels?: string[];
    class_labels?: string[];
    class_timetable_blocks?: unknown[];
    structured_entities?: {
      canonical_entities?: {
        teachers_count?: number;
        subjects_count?: number;
        teachers?: RozCanonicalTeacher[];
        subjects?: RozCanonicalSubject[];
        quality_notes_ar?: string[];
      };
    };
  };
};

export default function TimetableStudioPage() {
  const [summary, setSummary] = useState<Row | null>(null);
  const [readiness, setReadiness] = useState<Row | null>(null);
  const [weekDays, setWeekDays] = useState<Row[]>([]);
  const [periods, setPeriods] = useState<Row[]>([]);
  const [grid, setGrid] = useState<Row[]>([]);
  const [teacherLoad, setTeacherLoad] = useState<Row[]>([]);
  const [conflicts, setConflicts] = useState<Row[]>([]);
  const [quality, setQuality] = useState<Row[]>([]);
  const [versions, setVersions] = useState<Row[]>([]);
  const [runs, setRuns] = useState<Row[]>([]);
  const [teachers, setTeachers] = useState<Row[]>([]);
  const [subjects, setSubjects] = useState<Row[]>([]);
  const [classes, setClasses] = useState<Row[]>([]);
  const [classrooms, setClassrooms] = useState<Row[]>([]);
  const [curriculumPlans, setCurriculumPlans] = useState<Row[]>([]);
  const [constraints, setConstraints] = useState<Row[]>([]);

  const [selectedVersionId, setSelectedVersionId] = useState("");
  const [compareBaseVersionId, setCompareBaseVersionId] = useState("");
  const [compareTargetVersionId, setCompareTargetVersionId] = useState("");
  const [compareResult, setCompareResult] = useState<Row | null>(null);
  const [cleanupResult, setCleanupResult] = useState<Row | null>(null);

  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const [csv, setCsv] = useState(sampleCsv);
  const [fileName, setFileName] = useState("");
  const [rozFilePath, setRozFilePath] = useState("import_samples/mmmmmmmmmmm2-2.roz");
  const [rozPreview, setRozPreview] = useState<RozInspectResult | null>(null);

  const [subjectForm, setSubjectForm] = useState({ subject_code: "", subject_name_ar: "", color_code: "#8b5a2b" });
  const [teacherForm, setTeacherForm] = useState({ teacher_code: "", teacher_name_ar: "", phone: "", specialization: "" });
  const [classForm, setClassForm] = useState({ class_code: "", class_name_ar: "", stage_name_ar: "", grade_name_ar: "", capacity: 35 });
  const [roomForm, setRoomForm] = useState({ room_code: "", room_name_ar: "", capacity: 35, floor_name: "" });
  const [versionForm, setVersionForm] = useState({ name_ar: "", is_current: true });
  const [runForm, setRunForm] = useState({ name_ar: "توليد آلي من الاستوديو", clear_existing: true, make_current: true });
  const [planForm, setPlanForm] = useState({
    school_class_id: "",
    subject_id: "",
    teacher_id: "",
    classroom_id: "",
    weekly_lessons: 3,
    priority: 10,
  });
  const [slotForm, setSlotForm] = useState({
    timetable_version_id: "",
    school_class_id: "",
    week_day_id: "",
    period_id: "",
    subject_name_ar: "",
    teacher_id: "",
    classroom_id: "",
    notes: "",
  });
  const [constraintForm, setConstraintForm] = useState({
    constraint_type: "soft",
    target_scope: "global",
    target_id: "",
    rule_code: "",
    rule_payload_text: "{\n  \"note\": \"قاعدة من الاستوديو\"\n}",
    weight: 10,
  });

  const currentVersion = useMemo(() => {
    return versions.find((v) => v.id === selectedVersionId) || versions.find((v) => v.is_current) || versions[0] || null;
  }, [versions, selectedVersionId]);

  const versionGrid = useMemo(() => {
    if (!currentVersion?.id) return grid;
    return grid.filter((slot) => slot.timetable_version_id === currentVersion.id);
  }, [grid, currentVersion]);

  const gridMap = useMemo(() => {
    const m = new Map<string, Row[]>();
    for (const slot of versionGrid) {
      const key = `${slot.day_order || slot.week_day_id}:${slot.period_no}`;
      const arr = m.get(key) || [];
      arr.push(slot);
      m.set(key, arr);
    }
    return m;
  }, [versionGrid]);

  const currentQuality = useMemo(() => {
    if (!currentVersion?.id) return quality[0];
    return quality.find((q) => q.timetable_version_id === currentVersion.id) || quality[0];
  }, [quality, currentVersion]);

  async function refresh() {
    const [
      summaryData,
      readinessData,
      weekDayData,
      periodData,
      gridData,
      teacherLoadData,
      conflictData,
      qualityData,
      versionData,
      runData,
      teacherData,
      subjectData,
      classData,
      classroomData,
      planData,
      constraintData,
    ] = await Promise.all([
      apiGet("summary"),
      apiGet("readiness"),
      apiGet("week-days"),
      apiGet("periods"),
      apiGet("grid"),
      apiGet("teacher-load"),
      apiGet("conflicts"),
      apiGet("quality"),
      apiGet("versions"),
      apiGet("runs"),
      apiGet("teachers"),
      apiGet("subjects"),
      apiGet("classes"),
      apiGet("classrooms"),
      apiGet("curriculum-plans"),
      apiGet("constraints"),
    ]);

    setSummary(summaryData);
    setReadiness(readinessData);
    setWeekDays(weekDayData);
    setPeriods(periodData);
    setGrid(gridData);
    setTeacherLoad(teacherLoadData);
    setConflicts(conflictData);
    setQuality(qualityData);
    setVersions(versionData);
    setRuns(runData);
    setTeachers(teacherData);
    setSubjects(subjectData);
    setClasses(classData);
    setClassrooms(classroomData);
    setCurriculumPlans(planData);
    setConstraints(constraintData);

    const current = versionData.find((v: Row) => v.is_current) || versionData[0];
    if (!selectedVersionId && current?.id) {
      setSelectedVersionId(current.id);
      setSlotForm((s) => ({ ...s, timetable_version_id: current.id }));
    }
  }

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function action(label: string, fn: () => Promise<any>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await fn();
      setNotice(`${label}: تم بنجاح`);
      await refresh();
      return result;
    } catch (e: any) {
      setError(`${label}: ${String(e.message || e)}`);
    } finally {
      setBusy(false);
    }
  }

  async function chooseFile(event: React.ChangeEvent<HTMLInputElement>) {
    const f = event.target.files?.[0];
    if (!f) return;
    setFileName(f.name);
    setCsv(await f.text());
  }

  function syncSlotFromCell(day: Row, period: Row) {
    setSlotForm((s) => ({
      ...s,
      timetable_version_id: currentVersion?.id || s.timetable_version_id,
      week_day_id: String(day.id),
      period_id: String(period.id),
    }));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function createSlot() {
    const subjectName =
      slotForm.subject_name_ar ||
      subjects.find((s) => s.id === planForm.subject_id)?.subject_name_ar ||
      "";
    return action("إضافة حصة", () =>
      apiPost("slots", {
        timetable_version_id: slotForm.timetable_version_id || currentVersion?.id || null,
        school_class_id: slotForm.school_class_id,
        week_day_id: Number(slotForm.week_day_id),
        period_id: slotForm.period_id,
        subject_name_ar: subjectName,
        teacher_id: slotForm.teacher_id || null,
        classroom_id: slotForm.classroom_id || null,
        notes: slotForm.notes || null,
      })
    );
  }

  async function deleteSlot(slotId: string) {
    if (!confirm("حذف الحصة من نسخة الجدول؟")) return;
    return action("حذف الحصة", () => apiDelete(`slots/${slotId}`));
  }

  async function importCsv() {
    return action("استيراد CSV", () =>
      apiPost("import/time-table-csv", {
        batch_name: fileName || "استيراد من Timetable Studio",
        csv_text: csv,
      })
    );
  }

  
  async function runVersionCompare() {
    if (!compareBaseVersionId || !compareTargetVersionId) {
      alert("اختر نسخة الأساس ونسخة المقارنة");
      return;
    }

    if (compareBaseVersionId === compareTargetVersionId) {
      alert("لا يمكن مقارنة النسخة بنفسها");
      return;
    }

    const result = await apiGet(
      `versions/compare?base_version_id=${encodeURIComponent(compareBaseVersionId)}&target_version_id=${encodeURIComponent(compareTargetVersionId)}`
    );
    setCompareResult(result);
  }

  async function runCleanupDryRun() {
    return action("فحص بيانات الاختبار", async () => {
      const result = await apiPost("admin/cleanup-smoke-data", {
        confirm: "DELETE_SMOKE_DATA",
        dry_run: true,
      });
      setCleanupResult(result);
      return result;
    });
  }

  const cleanupCounts = cleanupResult?.counts || {};
  const cleanupTotal = Object.values(cleanupCounts).reduce((sum: number, value: any) => sum + Number(value || 0), 0);
  const cleanupPreview = cleanupResult?.preview || {};
  const cleanupPreviewSections = Object.entries(cleanupPreview).filter(([, rows]: [string, any]) => Array.isArray(rows) && rows.length > 0);



  async function inspectRozPreview() {
    await action("معاينة ROZ", async () => {
      const result = await apiPost("import/asctt-roz/inspect", {
        file_path: rozFilePath || "import_samples/mmmmmmmmmmm2-2.roz",
        max_records: 300,
      });
      setRozPreview(result);
    });
  }

async function exportCsv() {
    return action("تصدير CSV", async () => {
      const result = await apiPost("exports/csv", { version_id: currentVersion?.id || null });
      const blob = new Blob([result.csv_text], { type: result.content_type || "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.file_name || "school-timetable.csv";
      link.click();
      URL.revokeObjectURL(url);
      return result;
    });
  }

  function printStudio() {
    window.print();
  }

  async function createConstraint() {
    let payload: Row = {};
    try {
      payload = JSON.parse(constraintForm.rule_payload_text || "{}");
    } catch {
      setError("صيغة JSON في Payload غير صحيحة");
      return;
    }

    return action("إضافة قيد", () =>
      apiPost("constraints", {
        constraint_type: constraintForm.constraint_type,
        target_scope: constraintForm.target_scope,
        target_id: constraintForm.target_id || null,
        rule_code: constraintForm.rule_code,
        rule_payload: payload,
        weight: Number(constraintForm.weight),
      })
    );
  }

  return (
    <div className="container page timetable-studio">
      <section className="hero surface">
        <div>
          <div className="eyebrow">Phase 4 · Professional Timetable Studio</div>
          <h1>استوديو بناء الجدول المدرسي</h1>
          <p>
            شبكة تحرير مرئية للجدول: إدارة النسخ، إضافة وحذف الحصص، توليد آلي، فحص التعارضات،
            اعتماد ونشر، طباعة وتصدير CSV.
          </p>
        </div>
        <div className="hero-actions">
          <button className="btn" disabled={busy} onClick={() => action("تحديث البيانات", refresh)}>تحديث</button>
          <button className="btn btn-secondary" onClick={printStudio}>طباعة</button>
          <button className="btn btn-secondary" disabled={busy} onClick={exportCsv}>تصدير CSV</button>
        </div>
      </section>

      {(notice || error) && (
        <section className={`surface section-pad mt ${error ? "alert-error" : "alert-ok"}`}>
          {error || notice}
        </section>
      )}

      <section className="grid stats mt">
        <Metric label="مدرسون" value={summary?.teachers_count} />
        <Metric label="فصول" value={summary?.classes_count} />
        <Metric label="مواد" value={summary?.subjects_count} />
        <Metric label="قاعات" value={summary?.classrooms_count} />
        <Metric label="خطة أسبوعية" value={summary?.planned_weekly_lessons_count} />
        <Metric label="دروس الجدول" value={summary?.slots_count} />
        <Metric label="تشغيلات التوليد" value={summary?.generation_runs_count} />
        <Metric label="تعارضات صارمة" value={summary?.hard_conflicts_count} />
      </section>

      <section className="surface section-pad mt">
        <div className="studio-toolbar">
          <div>
            <h2>نسخة العمل</h2>
            <p className="muted">
              الحالية: {currentVersion ? `${currentVersion.name_ar} · ${currentVersion.status}` : "لا توجد نسخة"}
            </p>
          </div>
          <select
            className="input"
            value={currentVersion?.id || ""}
            onChange={(e) => {
              setSelectedVersionId(e.target.value);
              setSlotForm((s) => ({ ...s, timetable_version_id: e.target.value }));
            }}
          >
            {versions.map((v) => (
              <option key={v.id} value={v.id}>{v.name_ar} - {v.status}{v.is_current ? " - الحالية" : ""}</option>
            ))}
          </select>
          {currentVersion && <StatusBadge status={currentVersion.status} />}
        </div>

        <div className="action-row mt-small">
          <input
            className="input"
            placeholder="اسم نسخة جديدة"
            value={versionForm.name_ar}
            onChange={(e) => setVersionForm({ ...versionForm, name_ar: e.target.value })}
          />
          <button className="btn btn-secondary" disabled={busy || !versionForm.name_ar} onClick={() => action("إنشاء نسخة", () => apiPost("versions", versionForm))}>
            إنشاء نسخة
          </button>
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
      </section>

      <section className="split mt studio-top">
        <div className="surface section-pad">
          <h2>إضافة حصة مباشرة</h2>
          <div className="grid form-grid">
            <select className="input" value={slotForm.school_class_id} onChange={(e) => setSlotForm({ ...slotForm, school_class_id: e.target.value })}>
              <option value="">اختر الفصل</option>
              {classes.map((x) => <option key={x.id} value={x.id}>{x.class_name_ar || x.class_code}</option>)}
            </select>

            <select className="input" value={slotForm.week_day_id} onChange={(e) => setSlotForm({ ...slotForm, week_day_id: e.target.value })}>
              <option value="">اختر اليوم</option>
              {weekDays.map((x) => <option key={x.id} value={x.id}>{x.name_ar}</option>)}
            </select>

            <select className="input" value={slotForm.period_id} onChange={(e) => setSlotForm({ ...slotForm, period_id: e.target.value })}>
              <option value="">اختر الحصة</option>
              {periods.map((x) => <option key={x.id} value={x.id}>{x.name_ar || `الحصة ${x.period_no}`}</option>)}
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
          </div>
          <input className="input mt-small" placeholder="ملاحظات" value={slotForm.notes} onChange={(e) => setSlotForm({ ...slotForm, notes: e.target.value })} />
          <button
            className="btn mt-small"
            disabled={busy || !slotForm.school_class_id || !slotForm.week_day_id || !slotForm.period_id || !slotForm.subject_name_ar}
            onClick={createSlot}
          >
            إضافة الحصة للشبكة
          </button>
        </div>

        <div className="surface section-pad">
          <h2>التوليد الآلي</h2>
          <input className="input" value={runForm.name_ar} onChange={(e) => setRunForm({ ...runForm, name_ar: e.target.value })} />
          <div className="check-list mt-small">
            <label><input type="checkbox" checked={runForm.clear_existing} onChange={(e) => setRunForm({ ...runForm, clear_existing: e.target.checked })} /> حذف القديم داخل النسخة الجديدة</label>
            <label><input type="checkbox" checked={runForm.make_current} onChange={(e) => setRunForm({ ...runForm, make_current: e.target.checked })} /> جعلها النسخة الحالية</label>
          </div>
          <button className="btn mt-small" disabled={busy} onClick={() => action("توليد جدول", () => apiPost("runs", runForm))}>
            تشغيل التوليد
          </button>
          <button className="btn btn-secondary mt-small" disabled={busy} onClick={() => action("فحص Validation", () => apiPost("validation/run"))}>
            فحص التعارضات والجودة
          </button>
          <p className="muted mt-small">
            الجودة الحالية: {currentQuality?.quality_score ?? "—"} · الدروس المجدولة: {currentQuality?.scheduled_lessons ?? "—"}
          </p>
        </div>
      </section>

      
      <section className="surface section-pad mt version-compare-panel">
        <div className="studio-toolbar">
          <div>
            <h2>مقارنة نسختين من الجدول</h2>
            <p className="muted">
              قارن بين نسخة أساس ونسخة هدف لمعرفة الحصص المضافة، المحذوفة، والمتغيرة قبل الاعتماد أو النشر.
            </p>
          </div>
          {compareResult?.summary && (
            <span className="badge">
              فروقات: {compareResult.summary.delta_count}
            </span>
          )}
        </div>

        <div className="grid form-grid mt-small">
          <select
            className="input"
            value={compareBaseVersionId}
            onChange={(event) => setCompareBaseVersionId(event.target.value)}
          >
            <option value="">اختر نسخة الأساس</option>
            {versions.map((version) => (
              <option key={version.id} value={version.id}>
                {version.name_ar} · {version.status} · {version.is_current ? "حالية" : "غير حالية"}
              </option>
            ))}
          </select>

          <select
            className="input"
            value={compareTargetVersionId}
            onChange={(event) => setCompareTargetVersionId(event.target.value)}
          >
            <option value="">اختر نسخة المقارنة</option>
            {versions.map((version) => (
              <option key={version.id} value={version.id}>
                {version.name_ar} · {version.status} · {version.is_current ? "حالية" : "غير حالية"}
              </option>
            ))}
          </select>

          <button
            className="btn"
            disabled={busy || !compareBaseVersionId || !compareTargetVersionId || compareBaseVersionId === compareTargetVersionId}
            onClick={runVersionCompare}
          >
            مقارنة النسختين
          </button>
        </div>

        {compareResult?.summary && (
          <>
            <div className="compare-summary mt">
              <div className="metric">
                <span>حصص الأساس</span>
                <strong>{compareResult.summary.base_slots}</strong>
              </div>
              <div className="metric">
                <span>حصص المقارنة</span>
                <strong>{compareResult.summary.target_slots}</strong>
              </div>
              <div className="metric">
                <span>مضافة</span>
                <strong>{compareResult.summary.added_count}</strong>
              </div>
              <div className="metric">
                <span>محذوفة</span>
                <strong>{compareResult.summary.removed_count}</strong>
              </div>
              <div className="metric">
                <span>متغيرة</span>
                <strong>{compareResult.summary.changed_count}</strong>
              </div>
              <div className="metric">
                <span>بدون تغيير</span>
                <strong>{compareResult.summary.unchanged_count}</strong>
              </div>
            </div>

            <div className="compare-columns mt">
              <div className="compare-card added">
                <h3>الحصص المضافة</h3>
                {(compareResult.added || []).slice(0, 12).map((slot: Row) => (
                  <div className="compare-row" key={slot.id}>
                    <strong>{slot.class_name_ar || slot.class_code}</strong>
                    <span>{slot.day_name_ar} · {slot.period_name_ar}</span>
                    <small>{slot.subject_name_ar} · {slot.teacher_name_ar || "بدون مدرس"} · {slot.room_name_ar || "بدون قاعة"}</small>
                  </div>
                ))}
                {(!compareResult.added || compareResult.added.length === 0) && <p className="muted">لا توجد حصص مضافة.</p>}
              </div>

              <div className="compare-card removed">
                <h3>الحصص المحذوفة</h3>
                {(compareResult.removed || []).slice(0, 12).map((slot: Row) => (
                  <div className="compare-row" key={slot.id}>
                    <strong>{slot.class_name_ar || slot.class_code}</strong>
                    <span>{slot.day_name_ar} · {slot.period_name_ar}</span>
                    <small>{slot.subject_name_ar} · {slot.teacher_name_ar || "بدون مدرس"} · {slot.room_name_ar || "بدون قاعة"}</small>
                  </div>
                ))}
                {(!compareResult.removed || compareResult.removed.length === 0) && <p className="muted">لا توجد حصص محذوفة.</p>}
              </div>

              <div className="compare-card changed">
                <h3>الحصص المتغيرة</h3>
                {(compareResult.changed || []).slice(0, 12).map((item: Row) => (
                  <div className="compare-row" key={item.slot_key}>
                    <strong>{item.target?.class_name_ar || item.base?.class_name_ar || item.slot_key}</strong>
                    <span>{item.target?.day_name_ar || item.base?.day_name_ar} · {item.target?.period_name_ar || item.base?.period_name_ar}</span>
                    <small>
                      {Object.keys(item.changes || {}).join(" / ") || "تغيير غير محدد"}
                    </small>
                  </div>
                ))}
                {(!compareResult.changed || compareResult.changed.length === 0) && <p className="muted">لا توجد حصص متغيرة.</p>}
              </div>
            </div>
          </>
        )}
      </section>

      <section className="surface section-pad mt cleanup-dry-run-panel">
        <div className="studio-toolbar">
          <div>
            <div className="eyebrow">Production Cleanup Dry-Run</div>
            <h2>فحص بيانات الاختبار قبل تنظيف الإنتاج</h2>
            <p className="muted">
              هذه اللوحة لا تحذف أي بيانات. تعرض فقط عدد السجلات التي تحمل علامات اختبار مثل SMOKE / PH3E / PH4B / PH5 / اختبار / تثبيت / Guard.
            </p>
          </div>
          <span className={cleanupTotal > 0 ? "badge warning-badge" : "badge"}>
            {cleanupResult ? `${cleanupTotal} مرشح تنظيف` : "لم يتم الفحص"}
          </span>
        </div>

        <div className="action-row mt-small">
          <button className="btn" disabled={busy} onClick={runCleanupDryRun}>
            تشغيل Dry-Run
          </button>
          <span className="muted">
            الحذف الفعلي مقفول من الـ API في هذه المرحلة، ولا يتم تنفيذ إلا dry_run=true.
          </span>
        </div>

        {cleanupResult?.counts && (
          <div className="cleanup-grid mt">
            {Object.entries(cleanupResult.counts).map(([key, value]) => (
              <div className="cleanup-card" key={key}>
                <span>{cleanupLabel(key)}</span>
                <strong>{String(value)}</strong>
              </div>
            ))}
          </div>
        )}

        {cleanupPreviewSections.length > 0 && (
          <div className="cleanup-preview mt">
            <div className="studio-toolbar">
              <div>
                <h3>معاينة السجلات المرشحة</h3>
                <p className="muted">
                  عرض أسماء وأكواد وعينات من السجلات التي يطابقها فحص التنظيف. هذه المعاينة لا تنفذ حذفًا.
                </p>
              </div>
              <span className="badge warning-badge">
                Preview
              </span>
            </div>

            <div className="cleanup-preview-grid mt-small">
              {cleanupPreviewSections.map(([sectionKey, rows]: [string, any]) => (
                <div className="cleanup-preview-section" key={sectionKey}>
                  <h4>{cleanupLabel(sectionKey)} · {rows.length}</h4>
                  <div className="cleanup-preview-list">
                    {rows.slice(0, 8).map((row: Row, index: number) => (
                      <div className="cleanup-preview-row" key={row.id || `${sectionKey}-${index}`}>
                        <strong>{cleanupPreviewText(row.name)}</strong>
                        <span>{cleanupPreviewText(row.code)}</span>
                        <small>{cleanupPreviewText(row.extra)}</small>
                        <code>{cleanupPreviewText(row.id)}</code>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {cleanupResult?.markers && (
          <div className="cleanup-markers mt-small">
            {(cleanupResult.markers || []).map((marker: string) => (
              <span key={marker}>{marker}</span>
            ))}
          </div>
        )}
      </section>

<section className="surface section-pad mt studio-board">
        <div className="studio-toolbar">
          <div>
            <h2>الشبكة المرئية</h2>
            <p className="muted">اضغط على أي خلية فارغة لتجهيز اليوم والحصة في فورم الإضافة.</p>
          </div>
          <span className="badge">{versionGrid.length} حصة في النسخة المختارة</span>
        </div>

        <div className="visual-grid">
          <div className="grid-head period-head">الحصة / اليوم</div>
          {weekDays.map((day) => <div className="grid-head" key={day.id}>{day.name_ar}</div>)}

          {periods.filter((p) => !p.is_break).map((period) => (
            <div className="grid-row-fragment" key={period.id}>
              <div className="period-cell">
                <strong>{period.name_ar || `الحصة ${period.period_no}`}</strong>
                <small>{text(period.starts_at)} - {text(period.ends_at)}</small>
              </div>

              {weekDays.map((day) => {
                const slots = gridMap.get(`${day.sort_order || day.id}:${period.period_no}`) || [];
                return (
                  <button className={`slot-cell ${slots.length ? "has-slot" : ""}`} key={`${day.id}-${period.id}`} onClick={() => syncSlotFromCell(day, period)}>
                    {slots.length ? slots.map((slot) => (
                      <span className="slot-card" key={slot.id}>
                        <strong>{slot.subject_name_ar}</strong>
                        <small>{slot.class_name_ar || slot.class_code}</small>
                        <small>{slot.teacher_name_ar}</small>
                        <small>{slot.room_name_ar}</small>
                        <span
                          className="mini-danger"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteSlot(slot.id);
                          }}
                        >
                          حذف
                        </span>
                      </span>
                    )) : <span className="empty-slot">+ إضافة</span>}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>Curriculum Matrix</h2>
          <div className="grid form-grid">
            <select className="input" value={planForm.school_class_id} onChange={(e) => setPlanForm({ ...planForm, school_class_id: e.target.value })}>
              <option value="">الفصل</option>
              {classes.map((x) => <option key={x.id} value={x.id}>{x.class_name_ar || x.class_code}</option>)}
            </select>
            <select className="input" value={planForm.subject_id} onChange={(e) => setPlanForm({ ...planForm, subject_id: e.target.value })}>
              <option value="">المادة</option>
              {subjects.map((x) => <option key={x.id} value={x.id}>{x.subject_name_ar}</option>)}
            </select>
            <select className="input" value={planForm.teacher_id} onChange={(e) => setPlanForm({ ...planForm, teacher_id: e.target.value })}>
              <option value="">المدرس</option>
              {teachers.map((x) => <option key={x.id} value={x.id}>{x.teacher_name_ar}</option>)}
            </select>
            <select className="input" value={planForm.classroom_id} onChange={(e) => setPlanForm({ ...planForm, classroom_id: e.target.value })}>
              <option value="">القاعة</option>
              {classrooms.map((x) => <option key={x.id} value={x.id}>{x.room_name_ar || x.name_ar}</option>)}
            </select>
            <input className="input" type="number" min={1} value={planForm.weekly_lessons} onChange={(e) => setPlanForm({ ...planForm, weekly_lessons: Number(e.target.value) })} />
            <input className="input" type="number" value={planForm.priority} onChange={(e) => setPlanForm({ ...planForm, priority: Number(e.target.value) })} />
          </div>
          <button
            className="btn mt-small"
            disabled={busy || !planForm.school_class_id || !planForm.subject_id}
            onClick={() => action("حفظ خطة أسبوعية", () => apiPost("curriculum-plans", {
              ...planForm,
              teacher_id: planForm.teacher_id || null,
              classroom_id: planForm.classroom_id || null,
            }))}
          >
            حفظ خطة أسبوعية
          </button>

          <SmallTable
            rows={curriculumPlans.slice(0, 8)}
            empty="لا توجد خطط أسبوعية"
            columns={[
              { key: "class_name_ar", label: "الفصل" },
              { key: "subject_name_ar", label: "المادة" },
              { key: "teacher_name_ar", label: "المدرس" },
              { key: "weekly_lessons", label: "أسبوعيًا" },
            ]}
          />
        </div>

        <div className="surface section-pad">
          <h2>استيراد ومعاينة TimeTable</h2>

          <div className="alert-ok">
            <strong>ROZ / ASCTT Preview</strong>
            <p>
              معاينة آمنة للملف الثنائي ROZ بدون إدخال في قاعدة البيانات. تعرض المدرسين والمواد والفصول والحصص المستخرجة قبل مرحلة الربط النهائي.
            </p>
          </div>

          <input
            className="input mt-small"
            value={rozFilePath}
            onChange={(e) => setRozFilePath(e.target.value)}
            placeholder="مسار ملف ROZ داخل import_samples"
          />

          <button className="btn mt-small" disabled={busy || !rozFilePath.trim()} onClick={inspectRozPreview}>
            معاينة ملف ROZ
          </button>

          {rozPreview ? (
            <div className="roz-preview-panel mt-small">
              <div className="roz-preview-head">
                <div>
                  <strong>{rozPreview.file_name || "ROZ file"}</strong>
                  <small>{rozPreview.file_size ? `${rozPreview.file_size} bytes` : ""}</small>
                </div>
                <span className="status-generation">
                  {rozPreview.safe_to_import ? "جاهز للاستيراد" : "Preview فقط"}
                </span>
              </div>

              <div className="roz-preview-metrics">
                <span>السنة: {(rozPreview.detected?.academic_years || []).join("، ") || "غير محدد"}</span>
                <span>الحصص: {rozPreview.semantic_preview?.period_labels?.length || 0}</span>
                <span>الفصول: {rozPreview.semantic_preview?.class_labels?.length || 0}</span>
                <span>CLASSTT Blocks: {rozPreview.semantic_preview?.class_timetable_blocks?.length || 0}</span>
                <span>المدرسون: {rozPreview.semantic_preview?.structured_entities?.canonical_entities?.teachers_count || 0}</span>
                <span>المواد: {rozPreview.semantic_preview?.structured_entities?.canonical_entities?.subjects_count || 0}</span>
              </div>

              <div className="roz-entity-grid">
                <div>
                  <h3>المدرسون المستخرجون</h3>
                  <div className="chip-list">
                    {(rozPreview.semantic_preview?.structured_entities?.canonical_entities?.teachers || []).map((teacher) => (
                      <span className="chip" key={`${teacher.teacher_name_ar}-${teacher.offset}`}>
                        {teacher.teacher_name_ar}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h3>المواد المستخرجة</h3>
                  <div className="chip-list">
                    {(rozPreview.semantic_preview?.structured_entities?.canonical_entities?.subjects || []).map((subject) => (
                      <span className="chip" key={`${subject.subject_name_ar}-${subject.offset}`}>
                        {subject.subject_name_ar}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <details className="mt-small">
                <summary>ملاحظات الجودة</summary>
                <ul>
                  {(rozPreview.semantic_preview?.structured_entities?.canonical_entities?.quality_notes_ar || []).map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
                <small className="muted">SHA256: {rozPreview.sha256}</small>
              </details>
            </div>
          ) : null}

          <div className="mt">
            <h3>استيراد CSV التقليدي</h3>
            <input className="input" type="file" accept=".csv,.txt,text/csv" onChange={chooseFile} />
            <textarea className="input csv-area mt-small" value={csv} onChange={(e) => setCsv(e.target.value)} />
            <button className="btn mt-small" disabled={busy || !csv.trim()} onClick={importCsv}>استيراد CSV</button>
          </div>
        </div>
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>إدارة الموارد السريعة</h2>
          <div className="grid form-grid">
            <input className="input" placeholder="كود المادة" value={subjectForm.subject_code} onChange={(e) => setSubjectForm({ ...subjectForm, subject_code: e.target.value })} />
            <input className="input" placeholder="اسم المادة" value={subjectForm.subject_name_ar} onChange={(e) => setSubjectForm({ ...subjectForm, subject_name_ar: e.target.value })} />
            <button className="btn" disabled={busy || !subjectForm.subject_name_ar} onClick={() => action("إضافة مادة", () => apiPost("subjects", { ...subjectForm, subject_code: subjectForm.subject_code || null }))}>إضافة مادة</button>

            <input className="input" placeholder="كود المدرس" value={teacherForm.teacher_code} onChange={(e) => setTeacherForm({ ...teacherForm, teacher_code: e.target.value })} />
            <input className="input" placeholder="اسم المدرس" value={teacherForm.teacher_name_ar} onChange={(e) => setTeacherForm({ ...teacherForm, teacher_name_ar: e.target.value })} />
            <button className="btn" disabled={busy || !teacherForm.teacher_name_ar} onClick={() => action("إضافة مدرس", () => apiPost("teachers", { ...teacherForm, teacher_code: teacherForm.teacher_code || null }))}>إضافة مدرس</button>

            <input className="input" placeholder="كود الفصل" value={classForm.class_code} onChange={(e) => setClassForm({ ...classForm, class_code: e.target.value })} />
            <input className="input" placeholder="اسم الفصل" value={classForm.class_name_ar} onChange={(e) => setClassForm({ ...classForm, class_name_ar: e.target.value })} />
            <button className="btn" disabled={busy || !classForm.class_code || !classForm.class_name_ar} onClick={() => action("إضافة فصل", () => apiPost("classes", classForm))}>إضافة فصل</button>

            <input className="input" placeholder="كود القاعة" value={roomForm.room_code} onChange={(e) => setRoomForm({ ...roomForm, room_code: e.target.value })} />
            <input className="input" placeholder="اسم القاعة" value={roomForm.room_name_ar} onChange={(e) => setRoomForm({ ...roomForm, room_name_ar: e.target.value })} />
            <button className="btn" disabled={busy || !roomForm.room_code || !roomForm.room_name_ar} onClick={() => action("إضافة قاعة", () => apiPost("classrooms", roomForm))}>إضافة قاعة</button>
          </div>
        </div>

        <div className="surface section-pad">
          <h2>القيود والتعارضات</h2>
          <div className="grid form-grid">
            <select className="input" value={constraintForm.constraint_type} onChange={(e) => setConstraintForm({ ...constraintForm, constraint_type: e.target.value })}>
              <option value="soft">Soft</option>
              <option value="hard">Hard</option>
            </select>
            <input className="input" placeholder="target_scope" value={constraintForm.target_scope} onChange={(e) => setConstraintForm({ ...constraintForm, target_scope: e.target.value })} />
            <input className="input" placeholder="rule_code" value={constraintForm.rule_code} onChange={(e) => setConstraintForm({ ...constraintForm, rule_code: e.target.value })} />
            <input className="input" type="number" value={constraintForm.weight} onChange={(e) => setConstraintForm({ ...constraintForm, weight: Number(e.target.value) })} />
          </div>
          <textarea className="input csv-area mt-small" value={constraintForm.rule_payload_text} onChange={(e) => setConstraintForm({ ...constraintForm, rule_payload_text: e.target.value })} />
          <button className="btn mt-small" disabled={busy || !constraintForm.rule_code} onClick={createConstraint}>إضافة قيد</button>

          <SmallTable
            rows={conflicts.slice(0, 10)}
            empty="لا توجد تعارضات"
            columns={[
              { key: "severity", label: "الشدة" },
              { key: "conflict_type", label: "النوع" },
              { key: "message_ar", label: "الرسالة" },
            ]}
          />
        </div>
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>نصاب المدرسين</h2>
          <SmallTable
            rows={teacherLoad}
            empty="لا توجد بيانات نصاب"
            columns={[
              { key: "teacher_name_ar", label: "المدرس" },
              { key: "weekly_lessons_count", label: "حصص أسبوعية" },
              { key: "days_count", label: "أيام" },
            ]}
          />
        </div>

        <div className="surface section-pad">
          <h2>الجودة والتشغيلات</h2>
          <SmallTable
            rows={quality.slice(0, 8)}
            empty="لا توجد جودة محسوبة"
            columns={[
              { key: "timetable_name_ar", label: "النسخة" },
              { key: "scheduled_lessons", label: "مجدول" },
              { key: "required_lessons", label: "مطلوب" },
              { key: "quality_score", label: "الجودة" },
            ]}
          />

          <SmallTable
            rows={runs.slice(0, 5)}
            empty="لا توجد تشغيلات"
            columns={[
              { key: "status", label: "الحالة" },
              { key: "scheduled_lessons", label: "مجدول" },
              { key: "conflict_count", label: "تعارضات" },
              { key: "quality_score", label: "الجودة" },
            ]}
          />
        </div>
      </section>

      <section className="surface section-pad mt">
        <h2>سجل النسخ</h2>
        <SmallTable
          rows={versions}
          empty="لا توجد نسخ"
          columns={[
            { key: "name_ar", label: "النسخة" },
            { key: "status", label: "الحالة", render: (r) => <StatusBadge status={r.status} /> },
            { key: "is_current", label: "الحالية", render: (r) => r.is_current ? "نعم" : "لا" },
            { key: "effective_from", label: "من" },
            { key: "effective_to", label: "إلى" },
          ]}
        />
      </section>
    </div>
  );
}
