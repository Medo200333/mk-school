from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
API_FILE = PROJECT_ROOT / "backend" / "app" / "api" / "v1" / "school_timetable_operational.py"
EVIDENCE_FILE = PROJECT_ROOT / "backend" / "app" / "services" / "roz_evidence.py"


def _read(path: Path) -> str:
    assert path.exists(), f"Missing expected file: {path}"
    return path.read_text(encoding="utf-8")


def _function_body(source: str, function_name: str) -> str:
    marker = f"async def {function_name}("
    start = source.find(marker)
    if start == -1:
        marker = f"def {function_name}("
        start = source.find(marker)

    assert start != -1, f"Missing function: {function_name}"

    next_defs = [
        index
        for index in (
            source.find("\nasync def ", start + 1),
            source.find("\ndef ", start + 1),
            source.find("\n@router.", start + 1),
        )
        if index != -1
    ]
    end = min(next_defs) if next_defs else len(source)
    return source[start:end]


def test_roz_entity_import_never_writes_timetable_slots() -> None:
    api = _read(API_FILE)
    body = _function_body(api, "import_asctt_roz_entities")

    assert "IMPORT_ROZ_ENTITIES_ONLY" in body
    assert '"safe_to_import_slots": False' in body
    assert "school.timetable_slots" not in body
    assert "INSERT INTO school.timetable_slots" not in body
    assert "DELETE FROM school.timetable_slots" not in body
    assert "UPDATE school.timetable_slots" not in body


def test_no_roz_slot_import_route_or_confirm_phrase_exists() -> None:
    api = _read(API_FILE)

    forbidden_fragments = [
        "/import/asctt-roz/slots",
        "/import/asctt-roz/timetable",
        "/import/roz/slots",
        "/import/roz/timetable",
        "IMPORT_ROZ_SLOTS",
        "IMPORT_ROZ_TIMETABLE",
        "IMPORT_ASCTT_ROZ_SLOTS",
        "IMPORT_ASCTT_ROZ_TIMETABLE",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in api, f"Forbidden ROZ slot import fragment exists: {fragment}"


def test_roz_evidence_forces_slots_and_confirmation_off() -> None:
    evidence = _read(EVIDENCE_FILE)

    assert '"safe_to_import_slots": False' in evidence
    assert '"safe_to_confirm": False' in evidence
    assert "استيراد الحصص يظل ممنوعًا" in evidence


def test_existing_slot_writers_are_non_roz_paths_only() -> None:
    api = _read(API_FILE)

    slot_insert_count = len(re.findall(r"INSERT\s+INTO\s+school\.timetable_slots", api, flags=re.IGNORECASE))
    assert slot_insert_count >= 1

    entity_body = _function_body(api, "import_asctt_roz_entities")
    assert not re.search(r"INSERT\s+INTO\s+school\.timetable_slots", entity_body, flags=re.IGNORECASE)

    # Known non-ROZ slot writers must remain clearly separated from ROZ entity import.
    assert '@router.post("/import/time-table-csv")' in api
    assert '@router.post("/slots")' in api
    assert '@router.post("/runs")' in api


if __name__ == "__main__":
    test_roz_entity_import_never_writes_timetable_slots()
    test_no_roz_slot_import_route_or_confirm_phrase_exists()
    test_roz_evidence_forces_slots_and_confirmation_off()
    test_existing_slot_writers_are_non_roz_paths_only()
    print("✅ ROZ slot import guard static tests passed")
