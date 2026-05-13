# Phase 6N ROZ/ASCTT Structured Entities Preview Report

Date: 2026-05-13T17:34:40+03:00
Machine: pc-HP-mt45-Mobile-Thin-Client
Branch: phase-6-timetable-production-polish
Head before commit: f05ad1338751a8985c94ecad3127cffb1252f1d6

## Objective
Add a read-only structured preview layer for ASCTT/ROZ files.

## Scope
- Backend parser only.
- No DB import.
- No frontend UI patch.
- No proxy patch.
- No binary sample tracking.

## Added
- Teacher candidate extraction.
- Subject candidate extraction.
- structured_entities inside semantic_preview.
- Confidence scoring and source offsets.

## Verified
- Direct backend endpoint:
  POST /api/v1/school-timetable/import/asctt-roz/inspect
- Frontend proxy endpoint:
  POST /api/timetable/import/asctt-roz/inspect
- Existing timetable APIs.
- Existing frontend routes.
- No runtime errors.

## Safety
safe_to_import remains false.
parser_stage remains structured_preview_only for structured entities.
