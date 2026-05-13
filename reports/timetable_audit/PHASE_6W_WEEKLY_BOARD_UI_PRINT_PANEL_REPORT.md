# Phase 6W Weekly Board UI + Print Panel Report

## Context
- Machine: pc-HP-mt45-Mobile-Thin-Client
- Path: /home/pc/mk
- Branch: phase-6-timetable-production-polish
- Base Head: ffd8515fc83bc42278009c2c86f6fbd85cd7613f
- Head before commit: ffd8515fc83bc42278009c2c86f6fbd85cd7613f

## Implemented
- Added Weekly Board frontend types.
- Added Weekly Board frontend state.
- Added loadWeeklyBoard() using GET /api/timetable/weekly-board.
- Added printable Weekly Board UI panel.
- Added explicit "طباعة اللوحة" button.
- Added print CSS for weekly board output.
- Kept ROZ slot import blocked.
- Kept DB mutation out of Phase 6W.

## Verified
- /timetable renders Weekly Board UI markers.
- /api/timetable/weekly-board returns valid counts.
- total_cells = classes * days * periods.
- source.read_only = true.
- source.slot_import_from_roz = false.
- Existing routes and timetable APIs return 200.
- No current runtime/build errors.

## Safety
- Read-only UI.
- No ROZ timetable_slots import.
- No database mutation.
