# Phase 6S - ROZ Guarded Entity Import UI Panel

## الهدف
إضافة لوحة واجهة أمامية داخل صفحة الجدول المدرسي تسمح بتشغيل Dry-Run لاستيراد كيانات ROZ، ثم تنفيذ محروس للكيانات فقط عند كتابة تأكيد صريح.

## الملفات المعدلة
- `frontend/src/app/timetable/page.tsx`
- `frontend/src/app/globals.css`

## ما تم إضافته
- Types لنتيجة استيراد كيانات ROZ.
- State لنتيجة خطة الاستيراد وعبارة التأكيد.
- زر Dry Run للكيانات.
- زر تنفيذ محروس لا يعمل إلا عند كتابة:
  `IMPORT_ROZ_ENTITIES_ONLY`
- جدول معاينة للمدرسين.
- جدول معاينة للمواد.
- جدول معاينة للفصول.
- CSS للوحة ROZ entity import.

## قيود الأمان
- لا يوجد Auto Execute.
- التنفيذ الفعلي مغلق من الواجهة حتى يكتب المستخدم عبارة التأكيد.
- Backend ما زال يمنع التنفيذ بدون `execute_confirm=IMPORT_ROZ_ENTITIES_ONLY`.
- استيراد الحصص/الخانات ما زال ممنوعًا: `safe_to_import_slots=false`.

## إثبات التشغيل
- /timetable رجع 200.
- لوحة `استيراد كيانات ROZ الآمن` ظهرت في HTML.
- Dry-run عبر frontend proxy رجع 200.
- unsafe execute بدون confirm رجع 409.
- routes/APIs الأساسية رجعت 200.
- لا توجد runtime/build errors حالية.

## نتيجة Dry-Run
```json
{"file_name":"mmmmmmmmmmm2-2.roz","file_size":246418,"sha256":"5df0ee9085c4972ee5d7377bc66db0cab80d13389f297db6e0d2730a7d292f5a","dry_run":true,"safe_to_import_slots":false,"mode":"dry_run","teachers":[{"teacher_name_ar":"سماح ابراهيم","action":"would_create","teacher_code":"ROZ-T-001-E34BC6FD"},{"teacher_name_ar":"هدي محمد","action":"would_create","teacher_code":"ROZ-T-002-2BFBF1D8"},{"teacher_name_ar":"فاطمة اسماعيل","action":"would_create","teacher_code":"ROZ-T-003-C70208C0"},{"teacher_name_ar":"صفية صابر","action":"would_create","teacher_code":"ROZ-T-004-453C2B50"},{"teacher_name_ar":"محمد كمال","action":"would_create","teacher_code":"ROZ-T-005-6623B8A4"},{"teacher_name_ar":"جيرمين حسين","action":"would_create","teacher_code":"ROZ-T-006-CB657995"},{"teacher_name_ar":"حنان عبد المحي","action":"would_create","teacher_code":"ROZ-T-007-3B30251F"},{"teacher_name_ar":"رضا السيد","action":"would_create","teacher_code":"ROZ-T-008-29EC28E4"},{"teacher_name_ar":"منال عبد الحميد","action":"would_create","teacher_code":"ROZ-T-009-DD20F5F0"},{"teacher_name_ar":"رشا عبد الحافظ","action":"would_create","teacher_code":"ROZ-T-010-21868D72"},{"teacher_name_ar":"عفاف حامد","action":"would_create","teacher_code":"ROZ-T-011-A5603BD5"},{"teacher_name_ar":"ايمان حسن","action":"would_create","teacher_code":"ROZ-T-012-1E11CBA1"},{"teacher_name_ar":"سيد عبد الهادي","action":"would_create","teacher_code":"ROZ-T-013-39B04BB8"},{"teacher_name_ar":"رانيا ابراهيم","action":"would_create","teacher_code":"ROZ-T-014-F9EB8A8E"},{"teacher_name_ar":"امل محمد","action":"would_create","teacher_code":"ROZ-T-015-414EE666"}],"subjects":[{"subject_name_ar":"قران كريم","action":"would_create","subject_code":"ROZ-S-001-F6BBF123"},{"subject_name_ar":"تربية دينية اسلامية","action":"would_create","subject_code":"ROZ-S-002-1C40545D"},{"subject_name_ar":"لغة عربية","action":"would_create","subject_code":"ROZ-S-003-A9C6C791"},{"subject_name_ar":"رياضيات","action":"would_create","subject_code":"ROZ-S-004-8DD76B09"},{"subject_name_ar":"لغة انجليزية","action":"would_create","subject_code":"ROZ-S-005-77874EE7"},{"subject_name_ar":"متعدد","action":"would_create","subject_code":"ROZ-S-006-5496D34F"},{"subject_name_ar":"التربية الرياضية","action":"would_create","subject_code":"ROZ-S-007-23E77538"},{"subject_name_ar":"دراسات","action":"would_create","subject_code":"ROZ-S-008-44FE0AC9"},{"subject_name_ar":"علوم","action":"would_create","subject_code":"ROZ-S-009-63AF5F21"},{"subject_name_ar":"تربية فنية مهارات مهنية","action":"would_create","subject_code":"ROZ-S-010-8D8DBEB5"},{"subject_name_ar":"العاب ودين","action":"would_create","subject_code":"ROZ-S-011-36C60DE6"},{"subject_name_ar":"تكنولجيا","action":"would_create","subject_code":"ROZ-S-012-17C5C567"},{"subject_name_ar":"توكاتسو","action":"would_create","subject_code":"ROZ-S-013-E7AAF232"}],"classes":[{"class_name_ar":"الصف الدراسي 1","action":"would_create","class_code":"ROZ-CLASS-01"},{"class_name_ar":"الصف الدراسي 2","action":"would_create","class_code":"ROZ-CLASS-02"},{"class_name_ar":"الصف الدراسي 3","action":"would_create","class_code":"ROZ-CLASS-03"},{"class_name_ar":"الصف الدراسي 4","action":"would_create","class_code":"ROZ-CLASS-04"},{"class_name_ar":"الصف الدراسي 5","action":"would_create","class_code":"ROZ-CLASS-05"},{"class_name_ar":"الصف الدراسي 6","action":"would_create","class_code":"ROZ-CLASS-06"},{"class_name_ar":"الصف الدراسي 7","action":"would_create","class_code":"ROZ-CLASS-07"},{"class_name_ar":"الصف الدراسي 8","action":"would_create","class_code":"ROZ-CLASS-08"},{"class_name_ar":"الصف الدراسي 9","action":"would_create","class_code":"ROZ-CLASS-09"},{"class_name_ar":"الصف الدراسي 10","action":"would_create","class_code":"ROZ-CLASS-10"},{"class_name_ar":"الصف الدراسي 11","action":"would_create","class_code":"ROZ-CLASS-11"},{"class_name_ar":"الصف الدراسي 12","action":"would_create","class_code":"ROZ-CLASS-12"},{"class_name_ar":"الصف الدراسي 13","action":"would_create","class_code":"ROZ-CLASS-13"},{"class_name_ar":"الصف الدراسي 14","action":"would_create","class_code":"ROZ-CLASS-14"},{"class_name_ar":"الصف الدراسي 15","action":"would_create","class_code":"ROZ-CLASS-15"},{"class_name_ar":"الصف الدراسي 16","action":"would_create","class_code":"ROZ-CLASS-16"},{"class_name_ar":"الصف الدراسي 17","action":"would_create","class_code":"ROZ-CLASS-17"},{"class_name_ar":"الصف الدراسي 18","action":"would_create","class_code":"ROZ-CLASS-18"},{"class_name_ar":"الصف الدراسي 19","action":"would_create","class_code":"ROZ-CLASS-19"},{"class_name_ar":"الصف الدراسي 20","action":"would_create","class_code":"ROZ-CLASS-20"}],"counts":{"teachers_total":15,"subjects_total":13,"classes_total":20,"teachers_created":0,"subjects_created":0,"classes_created":0,"teachers_would_create":15,"subjects_would_create":13,"classes_would_create":20,"teachers_existing":0,"subjects_existing":0,"classes_existing":0},"notes_ar":["هذا endpoint يستورد الكيانات فقط: مدرسين ومواد وفصول.","استيراد خانات الجدول timetable_slots ممنوع في هذه المرحلة.","الوضع الافتراضي dry_run ولا يحدث أي كتابة في قاعدة البيانات.","التنفيذ الفعلي يتطلب dry_run=false و execute_confirm=IMPORT_ROZ_ENTITIES_ONLY."]}
```
