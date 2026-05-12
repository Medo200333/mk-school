// @ts-nocheck
"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { SchoolShell } from "@/components/layout/school-shell";

async function getApi(path) {
  const res = await fetch(`/api/timetable/${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function postApi(path, body) {
  const res = await fetch(`/api/timetable/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

const sample = `day,period,class,subject,teacher,room
الأحد,1,1A,لغة عربية,أحمد محمد,فصل 1
الأحد,2,1A,رياضيات,منى علي,فصل 1
الإثنين,1,1A,علوم,سعيد حسن,معمل علوم`;

export default function TimetablePage() {
  const [summary, setSummary] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [grid, setGrid] = useState([]);
  const [loads, setLoads] = useState([]);
  const [versions, setVersions] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [quality, setQuality] = useState([]);
  const [runs, setRuns] = useState([]);
  const [plans, setPlans] = useState([]);
  const [constraints, setConstraints] = useState([]);
  const [csv, setCsv] = useState(sample);
  const [file, setFile] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const currentVersion = useMemo(
    () => versions.find((item) => item.is_current) ?? versions[0],
    [versions]
  );

  async function load() {
    setError("");
    setLoading(true);
    try {
      const [
        nextSummary,
        nextReadiness,
        nextGrid,
        nextLoads,
        nextVersions,
        nextConflicts,
        nextQuality,
        nextRuns,
        nextPlans,
        nextConstraints
      ] =
        await Promise.all([
          getApi("summary"),
          getApi("readiness"),
          getApi("grid"),
          getApi("teacher-load"),
          getApi("versions"),
          getApi("conflicts"),
          getApi("quality"),
          getApi("runs"),
          getApi("curriculum-plans"),
          getApi("constraints")
        ]);
      setSummary(nextSummary);
      setReadiness(nextReadiness);
      setGrid(nextGrid);
      setLoads(nextLoads);
      setVersions(nextVersions);
      setConflicts(nextConflicts);
      setQuality(nextQuality);
      setRuns(nextRuns);
      setPlans(nextPlans);
      setConstraints(nextConstraints);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function runAction(path, successMessage, body) {
    setMessage("");
    setError("");
    try {
      const result = await postApi(path, body);
      setMessage(typeof successMessage === "function" ? successMessage(result) : successMessage);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function importCsv() {
    await runAction(
      "import/time-table-csv",
      (result) => `تم الاستيراد: إجمالي ${result.total_rows} / مقبول ${result.accepted_rows} / مرفوض ${result.rejected_rows}`,
      { batch_name: file || "استيراد جدول", csv_text: csv }
    );
  }

  async function runValidation() {
    await runAction(
      "validation/run",
      (result) => `تم الفحص: الجاهزية ${result.readiness.ready ? "مكتملة" : "غير مكتملة"} / التعارضات ${result.conflicts.length}`,
    );
  }

  async function runGeneration() {
    await runAction(
      "runs",
      (result) => `تم التوليد: ${result.scheduled_lessons}/${result.total_cards} حصة / جودة ${result.quality_score}`,
      { name_ar: "توليد آلي من Curriculum Matrix", clear_existing: true, make_current: true }
    );
  }

  async function exportCsv() {
    setMessage("");
    setError("");
    try {
      const result = await postApi("exports/csv");
      const blob = new Blob([result.csv_text], { type: result.content_type || "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.file_name || "school-timetable.csv";
      link.click();
      URL.revokeObjectURL(url);
      setMessage(`تم تجهيز ملف التصدير: ${result.file_name}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function chooseFile(event) {
    const selected = event.target.files?.[0];
    if (!selected) return;
    setFile(selected.name);
    setCsv(await selected.text());
    setMessage(`تم اختيار الملف: ${selected.name}`);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <SchoolShell>
      <section className="hero surface">
        <div>
          <div className="eyebrow">School Timetable</div>
          <h1>منصة الجداول المدرسية</h1>
          <p>
            تنفيذ وثيقة الجداول داخل المنصة الموحدة: ربط المدرسين من HR، موارد المدرسة،
            منع التعارضات، الاستيراد، المراجعة، الاعتماد، والنشر.
          </p>
        </div>
        <div className="hero-actions">
          <span className="badge">{readiness?.ready ? "جاهز للمراجعة" : "قيد التجهيز"}</span>
          <Link href="/hr" className="btn btn-secondary">برنامج الموظفين</Link>
          <Link href="/school" className="btn btn-secondary">برنامج المدارس</Link>
          <Link href="/education-control" className="btn btn-secondary">برنامج الكنترول</Link>
        </div>
      </section>

      {error ? <pre className="error">{error}</pre> : null}
      {message ? <div className="success mt">{message}</div> : null}
      {loading ? <div className="surface section-pad mt">جاري تحميل بيانات الجدول...</div> : null}

      <section className="grid stats mt">
        <Metric label="مدرسون" value={summary?.teachers_count} />
        <Metric label="مرتبطون بـ HR" value={summary?.hr_linked_teachers_count} />
        <Metric label="فصول" value={summary?.classes_count} />
        <Metric label="مواد" value={summary?.subjects_count} />
        <Metric label="خطة أسبوعية" value={summary?.planned_weekly_lessons_count} />
        <Metric label="قاعات" value={summary?.classrooms_count} />
        <Metric label="دروس الجدول" value={summary?.slots_count} />
        <Metric label="تشغيلات التوليد" value={summary?.generation_runs_count} />
        <Metric label="تعارضات صارمة" value={summary?.hard_conflicts_count} danger={summary?.hard_conflicts_count > 0} />
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>جاهزية التنفيذ</h2>
          <div className="check-list">
            {(readiness?.checks ?? []).map((check) => (
              <div key={check.code} className="check-row">
                <span className={check.ready ? "state-dot ready" : "state-dot blocked"} />
                <div>
                  <strong>{check.name_ar}</strong>
                  <p>{check.message_ar}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="surface section-pad">
          <h2>تشغيل الوثيقة</h2>
          <div className="action-stack">
            <button className="btn" onClick={() => runAction("bootstrap", "تم تجهيز الأيام والحصص")}>
              تجهيز الأيام والحصص
            </button>
            <button className="btn btn-secondary" onClick={() => runAction("sync/hr-teachers", (r) => `تمت مزامنة ${r.synced_count} مدرس من HR`)}>
              مزامنة المدرسين من HR
            </button>
            <button className="btn btn-secondary" onClick={runValidation}>فحص الجاهزية والقيود</button>
            <button className="btn btn-secondary" onClick={load}>تحديث البيانات</button>
          </div>
          <p>
            المدرسون مصدرهم برنامج الموظفين، والفصول والقاعات من برنامج المدارس، ولا يتم اعتماد
            أو نشر نسخة بها تعارضات صارمة.
          </p>
        </div>
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>Curriculum Matrix</h2>
          {plans.length === 0 ? (
            <p>لا توجد خطة أسبوعية بعد. أضف خططًا عبر API: /curriculum-plans أو /curriculum-plans/bulk.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>الفصل</th>
                    <th>المادة</th>
                    <th>المدرس</th>
                    <th>القاعة</th>
                    <th>حصص/أسبوع</th>
                  </tr>
                </thead>
                <tbody>
                  {plans.map((plan) => (
                    <tr key={plan.id}>
                      <td>{plan.class_name_ar}</td>
                      <td>{plan.subject_name_ar}</td>
                      <td>{plan.teacher_name_ar || "غير محدد"}</td>
                      <td>{plan.room_name_ar || "غير محدد"}</td>
                      <td>{plan.weekly_lessons}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="surface section-pad">
          <h2>Hard / Soft Constraints</h2>
          {constraints.length === 0 ? (
            <p>القيود الأساسية تعمل من قواعد التحقق، ويمكن إضافة قيود مخصصة عبر /constraints.</p>
          ) : (
            <div className="check-list">
              {constraints.map((item) => (
                <div key={item.id} className="check-row">
                  <span className={item.constraint_type === "hard" ? "state-dot blocked" : "state-dot ready"} />
                  <div>
                    <strong>{item.rule_code}</strong>
                    <p>{item.constraint_type} / {item.target_scope} / وزن {item.weight}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>Generation Center</h2>
          <div className="action-stack">
            <button className="btn" onClick={runGeneration}>توليد جدول من الخطة</button>
            <button className="btn btn-secondary" onClick={runValidation}>تشغيل Validation</button>
            <button className="btn btn-secondary" onClick={exportCsv}>تصدير CSV</button>
          </div>
          {runs.length === 0 ? (
            <p>لا توجد تشغيلات توليد بعد.</p>
          ) : (
            <div className="table-wrap mt-small">
              <table>
                <thead>
                  <tr>
                    <th>النسخة</th>
                    <th>الحالة</th>
                    <th>المجدول</th>
                    <th>التعارض</th>
                    <th>الجودة</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run) => (
                    <tr key={run.id}>
                      <td>{run.timetable_name_ar}</td>
                      <td>{run.status}</td>
                      <td>{run.scheduled_lessons}/{run.total_cards}</td>
                      <td>{run.conflict_count}</td>
                      <td>{run.quality_score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="surface section-pad">
          <h2>Quality Score</h2>
          {quality.length === 0 ? (
            <p>لا توجد نسخة جدول لحساب الجودة بعد.</p>
          ) : (
            <div className="check-list">
              {quality.map((item) => (
                <div key={item.timetable_version_id} className="quality-card">
                  <strong>{item.timetable_name_ar}</strong>
                  <span>{item.quality_score}</span>
                  <p>المجدول {item.scheduled_lessons} / المطلوب {item.required_lessons} / التعارضات {item.hard_conflicts}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>استيراد TimeTable CSV</h2>
          <input className="input mt-small" type="file" accept=".csv,.txt,text/csv" onChange={chooseFile} />
          {file ? <p>الملف: {file}</p> : null}
          <textarea className="input csv-area" value={csv} onChange={(event) => setCsv(event.target.value)} />
          <button className="btn" onClick={importCsv}>استيراد الجدول</button>
        </div>

        <div className="surface section-pad">
          <h2>دورة الاعتماد والنشر</h2>
          {currentVersion ? (
            <div className="version-panel">
              <strong>{currentVersion.name_ar}</strong>
              <p>الحالة: {currentVersion.status} {currentVersion.is_current ? " / النسخة الحالية" : ""}</p>
              <div className="action-stack">
                <button className="btn btn-secondary" onClick={() => runAction(`versions/${currentVersion.id}/approve`, "تم اعتماد نسخة الجدول")}>
                  اعتماد
                </button>
                <button className="btn" onClick={() => runAction(`versions/${currentVersion.id}/publish`, "تم نشر نسخة الجدول")}>
                  نشر
                </button>
                <button className="btn btn-secondary" onClick={() => runAction(`versions/${currentVersion.id}/archive`, "تم أرشفة نسخة الجدول")}>
                  أرشفة
                </button>
              </div>
            </div>
          ) : (
            <p>لا توجد نسخة جدول بعد. شغل تجهيز الأيام والحصص أولًا.</p>
          )}
        </div>
      </section>

      <section className="surface section-pad mt">
        <h2>التعارضات</h2>
        {conflicts.length === 0 ? (
          <p>لا توجد تعارضات صارمة حاليًا.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>النوع</th>
                  <th>الشدة</th>
                  <th>اليوم</th>
                  <th>الحصة</th>
                  <th>العدد</th>
                </tr>
              </thead>
              <tbody>
                {conflicts.map((item, index) => (
                  <tr key={`${item.conflict_type}-${item.entity_id}-${index}`}>
                    <td>{item.conflict_type}</td>
                    <td>{item.severity}</td>
                    <td>{item.day_name_ar}</td>
                    <td>{item.period_name_ar}</td>
                    <td>{item.conflict_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="split mt">
        <div className="surface section-pad">
          <h2>جدول الحصص</h2>
          {grid.length === 0 ? (
            <p>لا توجد دروس بعد. استورد CSV أو أضف حصصًا من API.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>اليوم</th>
                    <th>الحصة</th>
                    <th>الفصل</th>
                    <th>المادة</th>
                    <th>المدرس</th>
                    <th>القاعة</th>
                  </tr>
                </thead>
                <tbody>
                  {grid.map((row) => (
                    <tr key={row.id}>
                      <td>{row.day_name_ar}</td>
                      <td>{row.period_name_ar}</td>
                      <td>{row.class_name_ar}</td>
                      <td><strong>{row.subject_name_ar}</strong></td>
                      <td>{row.teacher_name_ar}</td>
                      <td>{row.room_name_ar}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <aside className="surface section-pad">
          <h2>نصاب المدرسين</h2>
          <div className="teacher-loads">
            {loads.length === 0 ? <p>لا توجد بيانات نصاب.</p> : null}
            {loads.map((teacher) => (
              <div key={teacher.teacher_id ?? teacher.teacher_name_ar} className="teacher-load">
                <strong>{teacher.teacher_name_ar}</strong>
                <span>{teacher.weekly_lessons_count} حصة أسبوعيًا</span>
              </div>
            ))}
          </div>
        </aside>
      </section>
    </SchoolShell>
  );
}

function Metric({ label, value, danger = false }) {
  return (
    <div className={danger ? "metric metric-danger" : "metric"}>
      <span>{label}</span>
      <strong>{value ?? 0}</strong>
    </div>
  );
}
