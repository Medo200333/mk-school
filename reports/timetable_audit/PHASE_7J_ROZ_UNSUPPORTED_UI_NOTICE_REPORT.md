# PHASE 7J — ROZ Unsupported Slot Import UI Notice Report

## Scope
This phase adds a frontend-only notice to the timetable ROZ / ASCTT panel.

## Changed Files
- `frontend/src/app/timetable/page.tsx`
- `frontend/src/app/globals.css`
- `reports/timetable_audit/PHASE_7J_ROZ_UNSUPPORTED_UI_NOTICE_REPORT.md`

## UI Decision
The timetable page now explicitly states that ROZ slot import is unsupported for the current sample.

Displayed policy:
- `safe_to_import_slots=false`
- `safe_to_confirm=false`
- ROZ Evidence is allowed for read-only preview.
- ROZ entity import remains limited to teachers, subjects, and classes.
- ROZ timetable slot import remains blocked.

## Database Impact
No database migration was created.
No database write was performed.
No timetable slot import was implemented.

## Backend Impact
No backend source code changed.
No API route changed.
No slot import route was added.

## Safety
This UI update does not enable:
- `/import/asctt-roz/slots`
- `/import/asctt-roz/timetable`
- `IMPORT_ASCTT_ROZ_SLOTS`
- `IMPORT_ASCTT_ROZ_TIMETABLE`

## Final Decision
Phase 7J makes the unsupported ROZ slot-import status visible in the UI while preserving the Phase 7I decision: layout/entities only, no timetable slots.
