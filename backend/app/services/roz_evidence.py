from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
ACADEMIC_YEAR_RE = re.compile(r"20\d{2}/20\d{2}")
PERIOD_RE = re.compile(r"الحصة\s+[^\s]+")
CLASS_RE = re.compile(r"الصف\s+الدراسي\s+\d+")

SUBJECT_HINTS = (
    "قران",
    "قرآن",
    "كريم",
    "تربية",
    "دينية",
    "اسلامية",
    "إسلامية",
    "لغة",
    "عربية",
    "انجليزية",
    "إنجليزية",
    "رياضيات",
    "علوم",
    "دراسات",
    "اجتماعية",
    "حاسب",
    "كمبيوتر",
    "نشاط",
    "فنية",
    "موسيقية",
    "رياضية",
)

NOISE_TOKENS = (
    "ےےے",
    "€",
    "ƒ",
    "†",
    "‰",
    "œ",
    "®",
    "؛؛",
)


def _clean_text(value: str) -> str:
    value = value.replace("\x00", " ")
    value = value.replace("\ufeff", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _arabic_ratio(value: str) -> float:
    if not value:
        return 0.0
    arabic = len(ARABIC_RE.findall(value))
    return round(arabic / max(len(value), 1), 4)


def _is_interesting_arabic(value: str) -> bool:
    value = _clean_text(value)
    if len(value) < 4 or len(value) > 220:
        return False
    if not ARABIC_RE.search(value):
        return False
    if any(token in value for token in NOISE_TOKENS):
        return False

    ratio = _arabic_ratio(value)
    if ratio >= 0.45:
        return True

    known_signal = (
        "الحصة" in value
        or "الصف الدراسي" in value
        or any(hint in value for hint in SUBJECT_HINTS)
        or ACADEMIC_YEAR_RE.search(value) is not None
    )
    return bool(known_signal and ratio >= 0.20)


def _decode_cp1256(chunk: bytes) -> str:
    return _clean_text(chunk.decode("cp1256", errors="ignore"))


def _ascii_printable_runs(data: bytes, minimum: int = 4) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    start: int | None = None
    current = bytearray()

    def flush(end_offset: int) -> None:
        nonlocal start, current
        if start is not None and len(current) >= minimum:
            text = current.decode("ascii", errors="ignore")
            text = _clean_text(text)
            if text:
                records.append(
                    {
                        "offset": start,
                        "length": end_offset - start,
                        "encoding": "ascii",
                        "text": text,
                    }
                )
        start = None
        current = bytearray()

    for offset, byte in enumerate(data):
        if 32 <= byte <= 126:
            if start is None:
                start = offset
            current.append(byte)
        else:
            flush(offset)

    flush(len(data))
    return records


def _cp1256_candidate_runs(data: bytes, minimum: int = 4) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    start: int | None = None
    current = bytearray()

    def allowed(byte: int) -> bool:
        return byte in (9, 10, 13) or 32 <= byte <= 126 or 0x80 <= byte <= 0xFF

    def flush(end_offset: int) -> None:
        nonlocal start, current
        if start is not None and len(current) >= minimum:
            text = _decode_cp1256(bytes(current))
            if _is_interesting_arabic(text):
                records.append(
                    {
                        "offset": start,
                        "length": end_offset - start,
                        "encoding": "cp1256",
                        "text": text,
                        "arabic_ratio": _arabic_ratio(text),
                        "tags": _tags_for_text(text),
                    }
                )
        start = None
        current = bytearray()

    for offset, byte in enumerate(data):
        if allowed(byte):
            if start is None:
                start = offset
            current.append(byte)
        else:
            flush(offset)

    flush(len(data))
    return records


def _tags_for_text(value: str) -> list[str]:
    tags: list[str] = []
    if PERIOD_RE.search(value):
        tags.append("period_label")
    if CLASS_RE.search(value):
        tags.append("class_label")
    if ACADEMIC_YEAR_RE.search(value):
        tags.append("academic_year")
    if any(hint in value for hint in SUBJECT_HINTS):
        tags.append("subject_candidate")
    return tags


def _dedup_records(records: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []

    for record in sorted(records, key=lambda item: (item.get("offset", 0), item.get("text", ""))):
        text = str(record.get("text") or "")
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(record)
        if len(output) >= limit:
            break

    return output


def _marker_offsets(data: bytes, marker: bytes, limit: int = 80) -> list[int]:
    offsets: list[int] = []
    start = 0
    while len(offsets) < limit:
        found = data.find(marker, start)
        if found < 0:
            break
        offsets.append(found)
        start = found + 1
    return offsets


def _marker_windows(data: bytes, marker: bytes, radius: int = 160, limit: int = 24) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for offset in _marker_offsets(data, marker, limit=limit):
        left = max(0, offset - radius)
        right = min(len(data), offset + len(marker) + radius)
        raw = data[left:right]
        windows.append(
            {
                "marker": marker.decode("ascii", errors="ignore"),
                "offset": offset,
                "window_start": left,
                "window_end": right,
                "raw_hex_prefix": raw[:80].hex(" "),
                "text_cp1256": _decode_cp1256(raw)[:260],
            }
        )
    return windows


def _collect_labels(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    text_blob = "\n".join(str(record.get("text") or "") for record in records)

    period_labels = sorted(set(PERIOD_RE.findall(text_blob)))
    class_labels = sorted(set(CLASS_RE.findall(text_blob)))
    academic_years = sorted(set(ACADEMIC_YEAR_RE.findall(text_blob)))

    subjects: list[str] = []
    seen_subjects: set[str] = set()
    for record in records:
        text = str(record.get("text") or "")
        if "period_label" in record.get("tags", []) or "class_label" in record.get("tags", []):
            continue
        if "subject_candidate" not in record.get("tags", []):
            continue
        normalized = _normalize_subject_candidate(text)
        if normalized and normalized not in seen_subjects:
            seen_subjects.add(normalized)
            subjects.append(normalized)

    return {
        "academic_years": academic_years[:20],
        "period_labels": period_labels[:30],
        "class_labels": class_labels[:80],
        "subject_candidates": subjects[:80],
    }


def _normalize_subject_candidate(value: str) -> str:
    value = _clean_text(value)
    parts = re.findall(r"[\u0600-\u06FF]+", value)
    if not parts:
        return ""

    phrase = " ".join(parts)
    phrase = re.sub(r"\b(.+?)\s+\1\b", r"\1", phrase)
    phrase = _clean_text(phrase)

    if len(phrase) < 4 or len(phrase) > 80:
        return ""
    if "الحصة" in phrase or "الصف الدراسي" in phrase:
        return ""

    return phrase


def _confidence(data: bytes, records: list[dict[str, Any]], labels: dict[str, list[str]]) -> dict[str, Any]:
    asctt_count = data.count(b"ASCTT")
    classtt_count = data.count(b"CLASSTT")

    breakdown = {
        "asctt_signature": 0.25 if b"ASCTT" in data[:64] else (0.18 if asctt_count else 0.0),
        "classtt_markers": min(0.25, classtt_count / 24 * 0.25),
        "arabic_cp1256_records": min(0.15, len(records) / 40 * 0.15),
        "period_and_class_labels": min(
            0.20,
            (len(labels["period_labels"]) + len(labels["class_labels"])) / 30 * 0.20,
        ),
        "safe_binary_size": 0.10 if 1024 <= len(data) <= 10 * 1024 * 1024 else 0.0,
        "subject_candidates": min(0.05, len(labels["subject_candidates"]) / 10 * 0.05),
    }

    total = round(sum(breakdown.values()), 4)
    return {
        "score": total,
        "percent": round(total * 100, 2),
        "breakdown": {key: round(value, 4) for key, value in breakdown.items()},
        "thresholds": {
            "entity_preview_min": 0.60,
            "slot_import_min": 0.90,
        },
    }


def analyze_roz_bytes(data: bytes, max_records: int = 300) -> dict[str, Any]:
    ascii_records = _ascii_printable_runs(data)
    arabic_records = _dedup_records(_cp1256_candidate_runs(data), limit=max_records)
    labels = _collect_labels(arabic_records)
    confidence = _confidence(data, arabic_records, labels)

    format_flags = {
        "is_zip": data.startswith(b"PK\x03\x04"),
        "is_sqlite": data.startswith(b"SQLite format 3\x00"),
        "has_asctt": b"ASCTT" in data,
        "has_classtt": b"CLASSTT" in data,
    }

    parser_stage = "asctt_binary_roz_evidence_only" if format_flags["has_asctt"] else "unknown"

    return {
        "parser_stage": parser_stage,
        "format": {
            "family": "ASCTT/ROZ" if format_flags["has_asctt"] else "unknown",
            "flags": format_flags,
            "first_64_hex": data[:64].hex(" "),
            "counts": {
                "ASCTT": data.count(b"ASCTT"),
                "CLASSTT": data.count(b"CLASSTT"),
                "CARD_ascii": data.upper().count(b"CARD"),
                "LESSON_ascii": data.upper().count(b"LESSON"),
                "ascii_runs": len(ascii_records),
                "arabic_cp1256_records": len(arabic_records),
            },
        },
        "detected": labels,
        "confidence": confidence,
        "evidence": {
            "markers": {
                "ASCTT": _marker_windows(data, b"ASCTT", radius=160, limit=12),
                "CLASSTT": _marker_windows(data, b"CLASSTT", radius=220, limit=24),
            },
            "arabic_records": arabic_records,
        },
        "safety": {
            "safe_to_import_entities": confidence["score"] >= 0.60,
            "safe_to_import_slots": False,
            "safe_to_confirm": False,
            "notes_ar": [
                "هذه طبقة Evidence فقط ولا تكتب في قاعدة البيانات.",
                "استيراد الحصص يظل ممنوعًا حتى يتم إثبات ربط CLASSTT بالأيام والحصص والمدرسين.",
                "لا يوجد اعتماد على قاعدة البيانات في هذا التحليل.",
            ],
        },
    }


def analyze_roz_file(path: str | Path, max_records: int = 300) -> dict[str, Any]:
    file_path = Path(path)
    data = file_path.read_bytes()
    result = analyze_roz_bytes(data, max_records=max_records)
    result["file"] = {
        "path": str(file_path),
        "name": file_path.name,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    return result


def summarize_for_cli(result: dict[str, Any]) -> dict[str, Any]:
    detected = result.get("detected", {})
    evidence = result.get("evidence", {})
    markers = evidence.get("markers", {})

    return {
        "file": result.get("file"),
        "parser_stage": result.get("parser_stage"),
        "format": result.get("format"),
        "confidence": result.get("confidence"),
        "detected_counts": {
            "academic_years": len(detected.get("academic_years", [])),
            "period_labels": len(detected.get("period_labels", [])),
            "class_labels": len(detected.get("class_labels", [])),
            "subject_candidates": len(detected.get("subject_candidates", [])),
            "ASCTT_windows": len(markers.get("ASCTT", [])),
            "CLASSTT_windows": len(markers.get("CLASSTT", [])),
            "arabic_records": len(evidence.get("arabic_records", [])),
        },
        "detected_preview": {
            "academic_years": detected.get("academic_years", [])[:10],
            "period_labels": detected.get("period_labels", [])[:10],
            "class_labels": detected.get("class_labels", [])[:20],
            "subject_candidates": detected.get("subject_candidates", [])[:20],
        },
        "safety": result.get("safety"),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect ASCTT/ROZ evidence without DB writes.")
    parser.add_argument("path", help="ROZ file path")
    parser.add_argument("--max-records", type=int, default=300)
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()

    analysis = analyze_roz_file(args.path, max_records=args.max_records)
    output = analysis if args.full else summarize_for_cli(analysis)
    print(json.dumps(output, ensure_ascii=False, indent=2))
