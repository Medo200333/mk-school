#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$HOME/mk"
OUT_DIR="$ROOT/reports/timetable_audit"
REPORT="$OUT_DIR/TIMETABLE_FINAL_AUDIT_REPORT.md"
TS="$(date '+%Y-%m-%d %H:%M:%S %Z')"

mkdir -p "$OUT_DIR"
cd "$ROOT"

section() {
  echo
  echo "## $1"
  echo
}

cmd_block() {
  local title="$1"
  shift
  echo
  echo "### $title"
  echo
  echo '```text'
  "$@" 2>&1 || true
  echo '```'
}

{
echo "# تقرير مراجعة موديول الجدول المدرسي وربطه بباقي البرنامج"
echo
echo "**Generated at:** $TS"
echo
echo "**Project root:** \`$ROOT\`"
echo

section "1) ملخص تنفيذي أولي"
echo "- هذا التقرير يفحص الموجود فعليًا داخل فولدر المشروع."
echo "- يركز على جزء الجدول المدرسي، الربط مع المدارس، الكنترول، الموظفين، وقاعدة البيانات."
echo "- أي نقص مذكور هنا مبني على فحص الملفات، Routes، APIs، والجداول الحالية."
echo

section "2) حالة Git والملفات المعدلة"
cmd_block "git status" git status --short
cmd_block "آخر commits" git log --oneline -n 12

section "3) حالة Docker والخدمات"
cmd_block "docker compose ps" sudo docker compose ps
cmd_block "backend logs آخر 120 سطر" sudo docker compose logs --tail=120 backend
cmd_block "frontend logs آخر 120 سطر" sudo docker compose logs --tail=120 frontend

section "4) فحص الصحة والروابط الرئيسية"
cmd_block "Backend health" curl -fsS http://localhost:8100/health
cmd_block "Frontend timetable HEAD" curl -I http://localhost:3100/timetable
cmd_block "Frontend home HEAD" curl -I http://localhost:3100/
cmd_block "Education control HEAD" curl -I http://localhost:3100/education-control

section "5) ملفات الجدول المدرسي في الباك إند"
cmd_block "backend timetable files" find backend -type f \( -iname "*timetable*" -o -iname "*school*" \) | sort
if [ -f backend/app/api/v1/school_timetable_operational.py ]; then
  cmd_block "school_timetable_operational.py أول 260 سطر" sed -n '1,260p' backend/app/api/v1/school_timetable_operational.py
else
  echo "- ❌ ملف API الخاص بالجدول غير موجود: \`backend/app/api/v1/school_timetable_operational.py\`"
fi

section "6) ملفات الجدول المدرسي في الفرونت إند"
cmd_block "frontend timetable files" find frontend/src/app -maxdepth 6 -type f \( -path "*timetable*" -o -path "*api/timetable*" \) | sort
if [ -f frontend/src/app/timetable/page.tsx ]; then
  cmd_block "timetable page أول 220 سطر" sed -n '1,220p' frontend/src/app/timetable/page.tsx
else
  echo "- ❌ صفحة الجدول غير موجودة: \`frontend/src/app/timetable/page.tsx\`"
fi
if [ -f frontend/src/app/api/timetable/'[...path]'/route.ts ]; then
  cmd_block "timetable proxy route" sed -n '1,220p' frontend/src/app/api/timetable/'[...path]'/route.ts
else
  echo "- ❌ Proxy route غير موجود: \`frontend/src/app/api/timetable/[...path]/route.ts\`"
fi

section "7) Routes الموجودة في Next.js"
cmd_block "frontend app routes" find frontend/src/app -maxdepth 4 -type f -name 'page.tsx' -printf '%p\n' | sort

section "8) OpenAPI الخاص بالباك إند"
cmd_block "كل school-timetable endpoints من OpenAPI" bash -lc "curl -fsS http://localhost:8100/openapi.json | python3 - <<'PY'
import json, sys
doc=json.load(sys.stdin)
for p in sorted(doc.get('paths',{})):
    if 'school-timetable' in p or 'education-control' in p or 'hr' in p or 'school' in p:
        methods=','.join(sorted(doc['paths'][p].keys()))
        print(f'{methods:20} {p}')
PY"

section "9) اختبار APIs الخاصة بالجدول المدرسي"
cmd_block "summary" curl -fsS http://localhost:8100/api/v1/school-timetable/summary
cmd_block "grid" curl -fsS http://localhost:8100/api/v1/school-timetable/grid
cmd_block "teacher-load" curl -fsS http://localhost:8100/api/v1/school-timetable/teacher-load
cmd_block "teachers" curl -fsS http://localhost:8100/api/v1/school-timetable/teachers
cmd_block "classes" curl -fsS http://localhost:8100/api/v1/school-timetable/classes
cmd_block "classrooms" curl -fsS http://localhost:8100/api/v1/school-timetable/classrooms
cmd_block "periods" curl -fsS http://localhost:8100/api/v1/school-timetable/periods
cmd_block "versions" curl -fsS http://localhost:8100/api/v1/school-timetable/versions

section "10) فحص جداول قاعدة البيانات school"
cmd_block "school schema tables" sudo docker compose exec -T postgres psql -U mk_user -d mk_school -c "
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema='school'
ORDER BY table_name;
"

cmd_block "school table row counts" sudo docker compose exec -T postgres psql -U mk_user -d mk_school -c "
SELECT 'teachers' table_name, count(*) rows FROM school.teachers
UNION ALL SELECT 'school_classes', count(*) FROM school.school_classes
UNION ALL SELECT 'classrooms', count(*) FROM school.classrooms
UNION ALL SELECT 'week_days', count(*) FROM school.week_days
UNION ALL SELECT 'lesson_periods', count(*) FROM school.lesson_periods
UNION ALL SELECT 'timetable_versions', count(*) FROM school.timetable_versions
UNION ALL SELECT 'timetable_slots', count(*) FROM school.timetable_slots
UNION ALL SELECT 'timetable_import_batches', count(*) FROM school.timetable_import_batches
UNION ALL SELECT 'timetable_import_errors', count(*) FROM school.timetable_import_errors;
"

cmd_block "school timetable constraints/indexes" sudo docker compose exec -T postgres psql -U mk_user -d mk_school -c "
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname='school'
ORDER BY tablename, indexname;
"

cmd_block "school columns" sudo docker compose exec -T postgres psql -U mk_user -d mk_school -c "
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema='school'
ORDER BY table_name, ordinal_position;
"

section "11) فحص الربط بين الجدول وباقي البرنامج"
echo "### نتيجة فحص مبدئية"
echo
echo "| منطقة الربط | الحالة الحالية المحتملة | المطلوب للوصول لربط إنتاجي |"
echo "|---|---|---|"
echo "| الجدول ↔ المدارس | يوجد classes/classrooms لكن غالبًا بدون institute_id إجباري | ربط كل فصل وقاعة ومعمل بمدرسة/معهد محدد |"
echo "| الجدول ↔ الموظفين | يوجد teachers داخل school لكن منفصل عن HR | ربط teacher_id بجدول الموظفين/العاملين بدل إنشاء مدرس مستقل فقط |"
echo "| الجدول ↔ الكنترول | يوجد education-control مستقل | ربط الصفوف والفصول والمواد بنتائج الكنترول والطلاب |"
echo "| الجدول ↔ المواد | subject_name_ar نص حر داخل slots | إنشاء جدول subjects رسمي وربطه بالحصص وبالكنترول |"
echo "| الجدول ↔ القاعات | classrooms موجودة | مطلوب نوع القاعة: فصل/معمل/ملعب/نشاط + السعة + صلاحية المادة |"
echo "| الجدول ↔ الاستيراد | CSV import موجود | مطلوب Import Wizard: Browse + Preview + Mapping + Validation قبل الحفظ |"
echo "| منع التعارض | موجود جزئيًا في API slots | مطلوب تعارض مدرس/فصل/قاعة/مجموعة/نصاب/أيام إجازات |"
echo "| التقسيم والمجموعات | غير مكتمل | مطلوب groups/sections/split lessons/lab groups |"
echo "| الواجهة | متذبذبة بسبب لصق ملفات طويلة | مطلوب UI ثابت مقسم Components وليس صفحة ضخمة واحدة |"
echo

section "12) النواقص النهائية في موديول الجدول المدرسي"
echo
echo "### ناقص أساسي"
echo "- إدارة مدرسة/معهد متعددة وربط كل جدول بمدرسة محددة."
echo "- جدول مواد رسمي بدل كتابة اسم المادة كنص داخل الحصة."
echo "- ربط المدرسين ببرنامج الموظفين HR."
echo "- ربط الفصول بطلاب الكنترول والمرحلة والصف."
echo "- إنشاء نسخة جدول لكل مدرسة ولكل عام دراسي وفصل دراسي."
echo "- شاشة بناء جدول يدوي كاملة."
echo "- شاشة استيراد احترافية من TimeTable مع Browse + Preview + Mapping."
echo "- دعم XLSX وليس CSV فقط."
echo "- منع تعارض شامل: مدرس، فصل، قاعة، مجموعة، مادة، نصاب، أيام غياب."
echo "- دعم الحصص المزدوجة والحصة نصفية/1.5."
echo "- دعم تقسيم الفصل لمجموعات: حاسب، علوم، لغات، أنشطة."
echo "- دعم القاعات المتخصصة ومعامل المواد."
echo "- دعم قيود المدرسين: أيام ممنوعة، حصص مفضلة، حد أقصى يومي/أسبوعي."
echo "- دعم طباعة جدول الفصل وجدول المدرس وجدول القاعة."
echo "- Dashboard إحصائي: كثافة الحصص، التعارضات، نصاب المدرسين، الفجوات."
echo "- Audit log لكل تعديل في الجدول."
echo "- صلاحيات: مدير مدرسة، مسؤول جدول، مراجع، مشاهدة فقط."
echo "- Import errors UI بدل الاعتماد على JSON فقط."
echo

echo "### ناقص معماري"
echo "- فصل موديول timetable إلى ملفات: API + Service + Repository + Schemas بدل ملف واحد ضخم."
echo "- إضافة migrations رسمية مرتبة بدل تعديلات مباشرة في DB."
echo "- إضافة tests لمنع التعارضات."
echo "- إضافة seed data رسمية للأيام والحصص."
echo "- إضافة route protection وصلاحيات."
echo "- إضافة validation صارم للمدخلات."
echo "- إضافة frontend components مستقلة بدل page.tsx كبير."
echo

section "13) خطة استكمال مقترحة"
echo
echo "### Phase A - تثبيت الأساس"
echo "1. تثبيت DB migrations لموديول timetable."
echo "2. ربط teachers ببرنامج الموظفين."
echo "3. ربط classes بالمدارس/المعاهد."
echo "4. إنشاء subjects."
echo "5. فصل كود API إلى services."
echo
echo "### Phase B - تشغيل UI حقيقي"
echo "1. صفحة Teachers."
echo "2. صفحة Classes."
echo "3. صفحة Rooms."
echo "4. صفحة Periods."
echo "5. صفحة Manual Timetable Builder."
echo "6. صفحة Import Wizard."
echo
echo "### Phase C - ذكاء الجدولة"
echo "1. Rules Engine."
echo "2. Conflict Detector."
echo "3. Auto-scheduler."
echo "4. Reports/Print."
echo

section "14) مراقبة تحديثات المشروع"
echo "تم إنشاء سكربت مراقبة في: \`scripts/watch_mk_updates.sh\`"
echo

} > "$REPORT"

cat > scripts/watch_mk_updates.sh <<'BASH2'
#!/usr/bin/env bash
set -Eeuo pipefail
cd "$HOME/mk"

echo "Watching project changes. Press Ctrl+C to stop."
echo

while true; do
  clear
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo
  echo "=== git status ==="
  git status --short || true

  echo
  echo "=== docker ps ==="
  sudo docker compose ps || true

  echo
  echo "=== latest changed frontend/backend files ==="
  find backend frontend -type f \
    \( -name "*.py" -o -name "*.tsx" -o -name "*.ts" -o -name "*.sql" -o -name "*.css" \) \
    -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort -r | head -n 30

  echo
  echo "=== timetable route ==="
  curl -fsSI http://localhost:3100/timetable 2>/dev/null | head -n 1 || echo "frontend timetable not reachable"

  echo
  echo "=== backend timetable summary ==="
  curl -fsS http://localhost:8100/api/v1/school-timetable/summary 2>/dev/null || echo "backend timetable not reachable"

  sleep 10
done
BASH2

chmod +x scripts/watch_mk_updates.sh
echo "✅ Report written: $REPORT"
echo
sed -n '1,260p' "$REPORT"
