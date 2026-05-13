# Phase 6F Cleanup Delete Plan Discovery Report

## Branch
phase-6-timetable-production-polish

## Base
phase-6e-cleanup-preview-ui-ok

## Timestamp
2026-05-13T12:34:44.954307+00:00

## Scope
- Inspect-only discovery for safe smoke/test data cleanup.
- No backend changes.
- No frontend changes.
- No proxy changes.
- No database DELETE/UPDATE/INSERT executed.

## Cleanup Preview Contract
- dry_run: True
- deleted: False
- count_total: 61
- preview_total: 61

## Candidate Counts
- classes: 3
- classrooms: 4
- constraints: 5
- export_jobs_by_version: 4
- generation_runs_by_version: 2
- slots_by_content: 11
- slots_by_version: 11
- subjects: 6
- teachers: 3
- versions: 12

## Preview Keys
- classes: 3
- classrooms: 4
- constraints: 5
- export_jobs_by_version: 4
- generation_runs_by_version: 2
- slots_by_content: 11
- slots_by_version: 11
- subjects: 6
- teachers: 3
- versions: 12

## Foreign Key Decision
Deletion must remove dependent rows before parent rows because cleanup parent entities are referenced by timetable slots and curriculum plans.

Relevant FK behavior discovered:
- timetable_slots -> timetable_versions: CASCADE
- timetable_generation_runs -> timetable_versions: SET NULL
- timetable_export_jobs -> timetable_versions: SET NULL
- curriculum_plans -> school_classes: CASCADE
- curriculum_plans -> subjects: NO ACTION
- curriculum_plans -> teachers: NO ACTION
- curriculum_plans -> classrooms: NO ACTION
- timetable_slots -> teachers/classes/classrooms: NO ACTION

## Proposed Safe Delete Order For Later Phase 6G
1. school.timetable_export_jobs where timetable_version_id is smoke-like.
2. school.timetable_generation_runs where timetable_version_id is smoke-like.
3. school.timetable_slots where version, content, teacher, class, or classroom is smoke-like.
4. school.curriculum_plans where teacher, subject, class, or classroom is smoke-like.
5. school.timetable_constraints where rule fields are smoke-like.
6. school.timetable_versions where version fields are smoke-like.
7. school.subjects where subject fields are smoke-like.
8. school.teachers where teacher fields are smoke-like.
9. school.school_classes where class fields are smoke-like.
10. school.classrooms where classroom fields are smoke-like.

## Safety Requirements Before Actual Delete
- Actual cleanup must remain behind explicit confirm.
- Actual cleanup must run inside one database transaction.
- Actual cleanup must return deleted_counts.
- Actual cleanup must keep dry_run=true behavior unchanged.
- Actual cleanup must be verified against preview counts before deletion.

## Phase 6F Result
Phase 6F is an inspect-only, report-only phase. It defines the safe deletion strategy but does not perform deletion.
