# PHASE 7E ROZ Runtime Smoke Verified

- Date: 2026-05-15T08:10:18+03:00
- Root: /home/pc/mk
- Machine: pc-HP-mt45-Mobile-Thin-Client
- Branch: phase-6-timetable-production-polish
- HEAD: eb8bdda
- Database changes: none
- Migration changes: none
- Application code changes in this step: none
- Report only: yes

## Runtime Services
- Backend container was running on host port 8100.
- Frontend container was running on host port 3100.
- PostgreSQL container was running on host port 55433.
- Redis container was running on host port 56379.

## Verified HTTP Results
- Backend /health returned HTTP 200.
- Frontend /timetable returned HTTP 200.
- Backend POST /api/v1/school-timetable/import/asctt-roz/inspect returned HTTP 200.
- Frontend proxy POST /api/timetable/import/asctt-roz/inspect returned HTTP 200.

## Verified ROZ Evidence
- File: import_samples/mmmmmmmmmmm2-2.roz
- Legacy parser format: ASCTT/ROZ
- Evidence parser family: ASCTT/ROZ
- Evidence confidence percent: 96.67
- Entity evidence review: allowed
- Slot import from ROZ: still blocked
- Final confirmation/import: still blocked

## Safety Decision
- safe_to_import_entities: true
- safe_to_import_slots: false
- safe_to_confirm: false
- No database write was performed by the smoke test.
- No timetable_slots rows were imported from ROZ.

## Logs Evidence
- Backend logs showed POST /api/v1/school-timetable/import/asctt-roz/inspect HTTP 200.
- Frontend logs showed POST /api/timetable/import/asctt-roz/inspect HTTP 200.
- Frontend logs showed /timetable HTTP 200.

## Related Commit
eb8bdda (HEAD -> phase-6-timetable-production-polish, tag: phase-7e-roz-api-evidence-integration-ok) phase7e integrate roz evidence into inspect api
