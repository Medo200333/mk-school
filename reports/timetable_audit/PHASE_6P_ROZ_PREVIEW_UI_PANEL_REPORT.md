# Phase 6P — ROZ Canonical Preview UI Panel

## Scope

Added a safe frontend preview panel for ASCTT/ROZ timetable files inside the timetable studio page.

This phase does not import ROZ content into the database.

## Changed files

- `frontend/src/app/timetable/page.tsx`
- `frontend/src/app/globals.css`

## UI behavior

The timetable page now includes:

- ROZ / ASCTT preview section
- editable ROZ file path field
- safe preview action calling `/api/timetable/import/asctt-roz/inspect`
- canonical metrics:
  - academic year
  - periods
  - classes
  - CLASSTT blocks
  - teachers
  - subjects
- teacher chips
- subject chips
- quality notes
- SHA256 display
- existing CSV import retained under “استيراد CSV التقليدي”

## Verified ROZ preview contract

- `safe_to_import = false`
- `canonical_teachers_count = 15`
- `canonical_subjects_count = 13`
- `محمد كمال` exists in canonical teacher preview

## Existing route/API verification

Frontend routes verified HTTP 200:

- `/`
- `/timetable`
- `/school`
- `/education-control`
- `/platform`
- `/hr`
- `/operations`
- `/access-mirror`

Timetable APIs verified HTTP 200:

- summary
- readiness
- grid
- teacher-load
- quality
- conflicts
- versions
- runs
- teachers
- subjects
- classes
- classrooms
- curriculum-plans
- constraints

## Safety

- No database import.
- No mutation endpoint added.
- ROZ preview remains inspect-only.
- No runtime/build errors detected after fresh route/API checks.
