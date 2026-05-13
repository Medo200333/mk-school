# Phase 6D Smoke Cleanup Preview API Report

## Branch
phase-6-timetable-production-polish

## Base
phase-6c-cleanup-dry-run-ui-ok

## Scope
Backend only.

## Modified Files
- backend/app/api/v1/school_timetable_operational.py
- reports/timetable_audit/PHASE_6D_SMOKE_CLEANUP_PREVIEW_API_REPORT.md

## Exact Backend Target
- Function: cleanup_smoke_data
- Inserted preview generation after cleanup counts.
- Return payload now includes:
  - dry_run
  - deleted
  - counts
  - preview
  - markers

## Safety
- No delete operation added.
- dry_run=false still returns 409.
- wrong confirm still returns 400.
- Frontend proxy verified.
- Core timetable APIs verified.

## Verification
- Direct backend cleanup preview verified.
- Frontend proxy cleanup preview verified.
- Runtime logs clean.
