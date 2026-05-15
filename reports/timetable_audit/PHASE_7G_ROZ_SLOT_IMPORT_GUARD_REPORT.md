# PHASE 7G ROZ Slot Import Guard

## الهدف

تثبيت Guard دائم يمنع استيراد خانات الجدول من ملفات ROZ قبل إثبات ربط CLASSTT بالأيام والحصص والمدرسين والفصول والمواد.

## الملفات

- `backend/tests/test_roz_slot_import_guard.py`
- `backend/app/api/v1/school_timetable_operational.py`
- `backend/app/services/roz_evidence.py`

## ما يثبته الاختبار

- Endpoint استيراد كيانات ROZ لا يكتب داخل `school.timetable_slots`.
- لا يوجد route لاستيراد ROZ slots مثل `/import/asctt-roz/slots`.
- لا توجد عبارة تأكيد خطيرة مثل `IMPORT_ROZ_SLOTS` أو `IMPORT_ROZ_TIMETABLE`.
- Evidence service يجبر:
  - `safe_to_import_slots = False`
  - `safe_to_confirm = False`
- كتابات `school.timetable_slots` الحالية تظل محصورة في المسارات غير ROZ:
  - CSV التقليدي
  - إنشاء حصة يدويًا
  - التوليد الآلي من Curriculum Matrix

## قاعدة البيانات

لا يوجد أي تغيير في قاعدة البيانات.  
الاختبار Static فقط ويقرأ ملفات Python كنص.

## قرار الأمان

ROZ slot import يظل ممنوعًا حتى يتم إثبات tuple كامل deterministic:

- subject
- teacher
- class/group
- day
- period


## Verification

- Date: 2026-05-15T20:22:40+03:00
- Root: /home/pc/mk
- Machine: pc-HP-mt45-Mobile-Thin-Client
- Branch: phase-6-timetable-production-polish
- Static test: passed
- Database changes: none
- Docker required: no
