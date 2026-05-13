# Phase 6J ROZ/ASCTT Inspect Backend API Report

## Branch
phase-6-timetable-production-polish

## Base
phase-6g-cleanup-execute-guard-ok

## Scope
- Added read-only backend endpoint for ASCTT/ROZ file inspection.
- Endpoint: POST /api/v1/school-timetable/import/asctt-roz/inspect
- Added read-only Docker mount: ./import_samples:/app/import_samples:ro
- Reads .roz files only from import_samples.
- Extracts CP1256/ASCII textual records from binary ROZ file.
- Detects ASCTT/CLASSTT markers, period labels, class labels, academic year markers.
- Does not import into database.
- Does not mutate timetable data.
- Does not change frontend UI.
- Does not change proxy.

## Verified
- Backend container can see /app/import_samples/mmmmmmmmmmm2-2.roz.
- Direct backend ROZ inspect endpoint returns HTTP 200.
- Frontend proxy passes JSON request to ROZ inspect endpoint.
- Unsafe path traversal is blocked.
- Main frontend routes return HTTP 200.
- Core timetable APIs remain OK.
- No recent runtime errors after verification.

## Current ROZ Input
- import_samples/mmmmmmmmmmm2-2.roz
- Inspect-only parser stage.

## Next Phase Recommendation
Phase 6K should add frontend preview UI for ROZ inspection, then Phase 6L can map extracted ROZ records into normalized timetable import rows after validating actual teacher/class/grid semantics.
