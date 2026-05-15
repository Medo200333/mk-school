# PHASE 7F ROZ Evidence UI Report

- Date: 2026-05-15T08:44:30+03:00
- File changed: `frontend/src/app/timetable/page.tsx`
- Database changes: none
- Docker changes: none
- Commit: not performed in this step

## UI Change

The ROZ preview panel now displays the backend Evidence fields returned by:

`POST /api/v1/school-timetable/import/asctt-roz/inspect`

Added visible fields:
- Evidence family
- Evidence confidence percent
- Entity import safety
- Slot import safety
- Parser stage
- ASCTT marker count
- CLASSTT marker count
- Arabic evidence record count
- Evidence safety notes

## Safety

- This is frontend-only.
- It does not write to the database.
- It does not enable ROZ timetable slot import.
- `safe_to_import_slots` remains a displayed guard and must stay false until CLASSTT slot mapping is proven.

## Verification Before Commit

- Verification date: 2026-05-15T08:47:07+03:00
- TypeScript check: passed with `./node_modules/.bin/tsc --noEmit`
- Diff whitespace check: passed with `git diff --check`
- Confirmed no real bad token exists for:
  - `evidence_safet?`
  - `rozPreviewevidence_summary`
- Frontend file only displays Evidence metadata.
- Database changes: none.
- ROZ slot import remains blocked.
