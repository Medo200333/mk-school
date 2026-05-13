# Phase 6K ROZ/ASCTT Semantic Preview Report

## Branch
phase-6-timetable-production-polish

## Base
phase-6j-roz-asctt-inspect-backend-ok

## Scope
- Improved ASCTT/ROZ inspect parser with semantic preview.
- Added class timetable block extraction using CLASSTT / CLASSTT_END.
- Added marker windows around teacher_row/class_row/report_header/Master.
- Added filtered meaningful Arabic records to reduce binary noise.
- Added detected period labels, class labels, and academic year metadata.
- Added import_samples/ to .gitignore so uploaded binary samples remain local input and are not committed.

## Safety
- No DB import.
- No DB writes.
- No frontend changes.
- No proxy changes.
- Endpoint remains inspect-only and safe_to_import=false.

## Verified
- Direct backend semantic inspect endpoint returns HTTP 200.
- Frontend proxy passes semantic inspect response.
- Existing timetable APIs remain OK.
- Main frontend routes return HTTP 200.
- No recent runtime errors.

## Next Phase
Phase 6L should add a frontend ROZ preview panel.
Phase 6M should start mapping confirmed ROZ blocks into normalized timetable import rows only after visual review.
