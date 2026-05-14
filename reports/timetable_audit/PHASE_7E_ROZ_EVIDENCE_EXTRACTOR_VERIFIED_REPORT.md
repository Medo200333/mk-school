# PHASE 7E ROZ Evidence Extractor Verified

- Date: 2026-05-14T23:41:06+03:00
- Root: /home/pc/mk
- Machine: pc-HP-mt45-Mobile-Thin-Client
- Branch: phase-6-timetable-production-polish
- Database changes: none
- API changes: none
- Timetable slot import from ROZ: still blocked
- Service file: `backend/app/services/roz_evidence.py`
- Test file: `backend/tests/test_roz_evidence.py`
- Sample file: `import_samples/mmmmmmmmmmm2-2.roz`

## Verification Result

- Direct Python test passed without pytest.
- Test was executed with `PYTHONDONTWRITEBYTECODE=1`.
- No database connection was opened.
- No Docker service was required.
- The extractor identified the sample as ASCTT/ROZ binary evidence.
- The extractor found ASCTT and CLASSTT markers.
- The extractor produced Arabic evidence records, period labels, class labels, and subject candidates.
- Entity import evidence is allowed for review only.
- Slot import remains blocked until CLASSTT is proven against days, periods, classes, teachers, and subjects.

## Extracted Summary

```json
{
  "file": {
    "path": "import_samples/mmmmmmmmmmm2-2.roz",
    "name": "mmmmmmmmmmm2-2.roz",
    "size": 246418,
    "sha256": "5df0ee9085c4972ee5d7377bc66db0cab80d13389f297db6e0d2730a7d292f5a"
  },
  "parser_stage": "asctt_binary_roz_evidence_only",
  "format": {
    "family": "ASCTT/ROZ",
    "flags": {
      "is_zip": false,
      "is_sqlite": false,
      "has_asctt": true,
      "has_classtt": true
    },
    "first_64_hex": "be 02 00 00 05 41 53 43 54 54 00 00 00 00 0a 00 00 80 0f d4 44 65 00 00 00 00 bb d0 4b 00 0a 00 00 80 6b cb 90 69 00 00 00 00 01 00 00 00 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 ff ff ff",
    "counts": {
      "ASCTT": 2,
      "CLASSTT": 24,
      "CARD_ascii": 0,
      "LESSON_ascii": 0,
      "ascii_runs": 334,
      "arabic_cp1256_records": 137
    }
  },
  "confidence": {
    "score": 0.9667,
    "percent": 96.67,
    "breakdown": {
      "asctt_signature": 0.25,
      "classtt_markers": 0.25,
      "arabic_cp1256_records": 0.15,
      "period_and_class_labels": 0.1667,
      "safe_binary_size": 0.1,
      "subject_candidates": 0.05
    },
    "thresholds": {
      "entity_preview_min": 0.6,
      "slot_import_min": 0.9
    }
  },
  "detected_counts": {
    "academic_years": 0,
    "period_labels": 5,
    "class_labels": 20,
    "subject_candidates": 12,
    "ASCTT_windows": 2,
    "CLASSTT_windows": 24,
    "arabic_records": 137
  },
  "detected_preview": {
    "academic_years": [],
    "period_labels": [
      "الحصة الاولي",
      "الحصة الثالثة",
      "الحصة الثانية",
      "الحصة الخامسة",
      "الحصة الرابعة"
    ],
    "class_labels": [
      "الصف الدراسي 1",
      "الصف الدراسي 10",
      "الصف الدراسي 11",
      "الصف الدراسي 12",
      "الصف الدراسي 13",
      "الصف الدراسي 14",
      "الصف الدراسي 15",
      "الصف الدراسي 16",
      "الصف الدراسي 17",
      "الصف الدراسي 18",
      "الصف الدراسي 19",
      "الصف الدراسي 2",
      "الصف الدراسي 20",
      "الصف الدراسي 3",
      "الصف الدراسي 4",
      "الصف الدراسي 5",
      "الصف الدراسي 6",
      "الصف الدراسي 7",
      "الصف الدراسي 8",
      "الصف الدراسي 9"
    ],
    "subject_candidates": [
      "قران كريم",
      "تربية دينية اسلامية",
      "تربية دينية",
      "لغة عربية",
      "رياضيات",
      "لغة انجليزية",
      "التربية الرياضية",
      "تربية الرياضية",
      "دراسات",
      "علوم",
      "تربية فنية مهارات مهنية",
      "حنان قران"
    ]
  },
  "safety": {
    "safe_to_import_entities": true,
    "safe_to_import_slots": false,
    "safe_to_confirm": false,
    "notes_ar": [
      "هذه طبقة Evidence فقط ولا تكتب في قاعدة البيانات.",
      "استيراد الحصص يظل ممنوعًا حتى يتم إثبات ربط CLASSTT بالأيام والحصص والمدرسين.",
      "لا يوجد اعتماد على قاعدة البيانات في هذا التحليل."
    ]
  }
}
```

## Safety Decision

- `safe_to_import_entities`: evidence-only readiness.
- `safe_to_import_slots`: false.
- `safe_to_confirm`: false.
- This phase adds a parser/evidence service and tests only.
