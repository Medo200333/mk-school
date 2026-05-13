# Phase 6B Smoke Data Cleanup Dry-Run API Report

## Branch
phase-6-timetable-production-polish

## Endpoint
POST /api/v1/school-timetable/admin/cleanup-smoke-data

## Fix
Resolved ambiguous joined cleanup-count queries by qualifying timetable version columns through `tv.name_ar` and `tv.status`.

## Safety Contract
- Requires confirm=DELETE_SMOKE_DATA.
- dry_run=true returns counts only.
- dry_run=false is blocked with HTTP 409.
- Wrong confirmation is blocked with HTTP 400.
- No records are deleted in Phase 6B.

## Verified
- Direct backend dry-run works.
- Frontend proxy dry-run works.
- Wrong confirmation is rejected.
- Actual deletion is rejected.
- Core timetable APIs remain healthy.
- No recent runtime errors after the fix.
