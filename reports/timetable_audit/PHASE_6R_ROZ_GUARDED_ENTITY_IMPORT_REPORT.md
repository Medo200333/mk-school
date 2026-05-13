# Phase 6R ROZ Guarded Entity Import Backend

## Base
- Branch: phase-6-timetable-production-polish
- Base tag: phase-6p-roz-preview-ui-panel-ok
- Commit before Phase 6R: 8ba215f69ff40422bcd0dc4a27553d431f63bfb2

## Added Endpoint
`POST /api/v1/school-timetable/import/asctt-roz/entities`

## Scope
Guarded entity-only import from ASCTT/ROZ preview:
- Teachers
- Subjects
- Classes

## Explicitly Blocked
- No timetable_slots import
- No CLASSTT slot mapping import
- No automatic schedule insertion

## Safety Contract
- Default: `dry_run=true`
- Dry-run performs no DB writes
- Execute requires:
  - `dry_run=false`
  - `execute_confirm=IMPORT_ROZ_ENTITIES_ONLY`
- Execute without confirmation returns HTTP 409

## Dry-run Result
- Teachers total: 15
- Subjects total: 13
- Classes total: 20
- Teachers would create: 15
- Subjects would create: 13
- Classes would create: 20
- Created in dry-run: 0

## Verification
- Direct backend dry-run: OK
- Frontend proxy dry-run: OK
- Unsafe execute guard: OK
- Existing frontend routes: OK
- Existing timetable APIs: OK
- Runtime/build logs: clean

## Next Phase
Phase 6S may add a frontend dry-run/execute panel for entity import.
Slot import remains blocked until CLASSTT/day/period/teacher mapping is proven.
