# PHASE 7E ROZ API Integration Target Inspect

- Date: 2026-05-14T23:50:17+03:00
- Root: /home/pc/mk
- Machine: pc-HP-mt45-Mobile-Thin-Client
- Branch: phase-6-timetable-production-polish
- Database changes: none
- Code mutation: none

## Current Commit
d61dfea (HEAD -> phase-6-timetable-production-polish, tag: phase-7e-roz-evidence-extractor-ok) phase7e add roz evidence extractor
7b1a0bb (tag: phase-6zz-release-bundle-restore-ok) phase6zz verify release bundle restore
25a5875 (tag: phase-6z-release-readiness-local-ok) phase6z verify local release readiness

## Files
- API: `backend/app/api/v1/school_timetable_operational.py`
- Service: `backend/app/services/roz_evidence.py`

## Current ROZ API Functions
```
429:            "slot_import_from_roz": False,
653:class RozInspectPayload(BaseModel):
1554:def parse_asctt_roz_bytes(data: bytes, max_records: int = 800) -> dict[str, Any]:
1617:async def inspect_asctt_roz_file(
1618:    payload: RozInspectPayload,
1623:    parsed = parse_asctt_roz_bytes(data, payload.max_records)
1635:class RozEntityImportPayload(BaseModel):
1879:        "safe_to_import_slots": False,
1907:async def import_asctt_roz_entities(
1908:    payload: RozEntityImportPayload,
1913:    parsed = parse_asctt_roz_bytes(data, payload.max_records)
1944:        "safe_to_import_slots": False,
```

## Service Public Functions
```
298:def analyze_roz_bytes(data: bytes, max_records: int = 300) -> dict[str, Any]:
350:def analyze_roz_file(path: str | Path, max_records: int = 300) -> dict[str, Any]:
363:def summarize_for_cli(result: dict[str, Any]) -> dict[str, Any]:
```

## Decision Needed
- Next patch should import `analyze_roz_file` or `analyze_roz_bytes` from service.
- Existing endpoint response must stay backward-compatible for frontend.
- ROZ slot import must remain blocked.
- Database writes must remain unchanged in this integration step.
