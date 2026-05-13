# Phase 6O ROZ/ASCTT Canonical Entities Preview Report

Date: 2026-05-13T17:44:20+03:00
Machine: pc-HP-mt45-Mobile-Thin-Client
Branch: phase-6-timetable-production-polish
Head before commit: dbbf7e67c6ed86f4971105353b92204986286b6c

## Objective
Clean ROZ structured entity extraction into canonical preview entities.

## Scope
- Backend parser only.
- No DB import.
- No frontend UI changes.
- No binary file tracking.

## Added
- Canonical teacher cleanup.
- Proven ROZ teacher-name preview map for names discovered in Phase 6M/6N.
- Reversed/partial/noisy name filtering.
- Structural/school phrase exclusion.
- Canonical subject cleanup.
- canonical_entities under semantic_preview.structured_entities.

## Verified
- محمد كمال is present.
- Known noisy names are excluded.
- Direct backend inspect endpoint passes.
- Frontend proxy inspect endpoint passes.
- Existing timetable APIs pass.
- Existing frontend routes pass.
- No runtime errors.

## Safety
canonical_entities.safe_to_import remains false.
canonical_entities.parser_stage is canonical_preview_only.
