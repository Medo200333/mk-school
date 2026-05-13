# Phase 6V - Weekly Board Backend API

Date: 2026-05-14T01:13:32+03:00
Branch: phase-6-timetable-production-polish
HEAD before commit: 8c07f85585def3b7229d9f77198fc10da07fec6f

## Implemented

- Added read-only endpoint:
  - GET /api/v1/school-timetable/weekly-board
  - Frontend proxy path:
    - /api/timetable/weekly-board

## Source of Truth

- school.timetable_slots
- Subject contract:
  - timetable_slots.subject_name_ar
- No subject_id is assumed because current timetable_slots schema does not contain subject_id.

## Response Shape

The endpoint returns:

- version
- days
- periods
- classes
- cells
- matrix
- counts
- safe_to_print
- source contract metadata
- Arabic safety notes

## Safety

- No database writes.
- No ROZ slot import.
- ROZ slot mapping remains blocked until CLASSTT mapping is proven.
- Endpoint is ready for Weekly Board UI and print layout.

## Verification

- Direct backend weekly-board contract passed.
- Frontend proxy weekly-board contract passed.
- Imported TimeTable draft version check passed when available.
- Existing frontend routes and timetable APIs returned 200.
- Runtime logs showed no current build/runtime errors.
