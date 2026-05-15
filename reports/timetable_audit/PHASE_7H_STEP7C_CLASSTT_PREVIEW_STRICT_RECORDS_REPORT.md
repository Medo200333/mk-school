# PHASE 7H STEP 7C - CLASSTT Read-Only Preview Strict Record Fix

## Scope

Changed only:

- `backend/app/services/roz_evidence.py`

## Purpose

Added a read-only CLASSTT layout preview decoder and fixed its layout text extraction to accept only real ASCTT/ROZ text records:

- prefix byte `0x02`
- one-byte length
- cp1256 text payload
- exact normalized layout term match only

This rejects noisy substring hits that previously caused wrong cycle selection.

## Confirmed output

The service-only smoke confirmed:

- raw `CLASSTT`: 24
- true `CLASSTT` records: 12
- `CLASSTT_END`: 12
- selected layout cycles: 12
- selected exactly 12 cycles: true
- total header ids: 60
- unique header ids: 60
- covers exact `0..59`: true
- object map missing count: 0

## Safety

This remains evidence-only.

Still false:

- `safe_to_import_slots`
- `safe_to_confirm`
- `slot_tuple_proven`
- `teacher_subject_period_class_day_tuple_proven`

## Database impact

None.

No database command was run.

No insert/update/delete was added.

## Forbidden capabilities still absent

No route or confirm token was added for slot import:

- no `/import/asctt-roz/slots`
- no `/import/asctt-roz/timetable`
- no `IMPORT_ROZ_SLOTS`
- no `IMPORT_ROZ_TIMETABLE`

## Important conclusion

This proves CLASSTT binary header ids map to layout object cycles only.

It still does not prove deterministic timetable slot tuples:

- class
- day
- period
- subject
- teacher

Therefore actual ROZ slot import remains blocked.
