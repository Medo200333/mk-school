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


def _read_pascal_cp1256(data: bytes, offset: int) -> tuple[str, int] | None:
    if offset < 0 or offset >= len(data):
        return None
    length = data[offset]
    if length <= 0:
        return None
    start = offset + 1
    end = start + length
    if end > len(data):
        return None
    raw = data[start:end]
    try:
        return raw.decode("cp1256", errors="ignore"), end
    except Exception:
        return None


def _true_classtt_record_starts(data: bytes) -> list[int]:
    starts: list[int] = []
    marker = b"CLASSTT"
    pos = 0
    while True:
        idx = data.find(marker, pos)
        if idx < 0:
            break
        record_start = idx - 2
        if record_start >= 0 and data[record_start] == 2 and data[record_start + 1] == len(marker):
            starts.append(record_start)
        pos = idx + 1
    return starts


def _decode_classtt_block_labels(data: bytes, start: int) -> list[str]:
    labels: list[str] = []
    first = _read_pascal_cp1256(data, start + 1)
    if not first or first[0] != "CLASSTT":
        return labels

    pos = first[1]
    for _ in range(4):
        parsed = _read_pascal_cp1256(data, pos)
        if not parsed:
            break
        value, pos = parsed
        if "/" in value:
            labels.append(value)
        else:
            break
    return labels


def _read_u32_le(data: bytes, offset: int) -> int | None:
    if offset < 0 or offset + 4 > len(data):
        return None
    return int.from_bytes(data[offset : offset + 4], "little", signed=False)


def _normalize_layout_term(value: str) -> str:
    value = " ".join(value.replace("\x00", " ").split())
    known = ["الفصل بالكامل", "المجموعة 1", "المجموعة 2", "أولاد", "بنات"]
    for term in known:
        if term in value:
            return term
    if "المجموعة" in value and "2" in value:
        return "المجموعة 2"
    return value


def _canonical_layout_text(value: str) -> str:
    return " ".join(value.replace("\x00", " ").split())


def _strict_layout_term(value: str) -> tuple[str, str] | None:
    canonical = _canonical_layout_text(value)
    canonical = canonical.replace("المجموعة  2", "المجموعة 2")
    expected = {
        "الفصل بالكامل",
        "المجموعة 1",
        "المجموعة 2",
        "أولاد",
        "بنات",
    }
    if canonical in expected:
        return canonical, "EXACT"
    return None


def _read_layout_text_record(data: bytes, offset: int) -> tuple[str, int] | None:
    """Read a real ASCTT/ROZ text record: prefix byte 0x02, then one-byte length, then cp1256 text.

    This intentionally rejects noisy substring hits. It is evidence-only and never writes to DB.
    """
    if offset < 0 or offset + 2 > len(data):
        return None
    if data[offset] != 2:
        return None

    length = data[offset + 1]
    if length <= 0 or length > 80:
        return None

    start = offset + 2
    end = start + length
    if end > len(data):
        return None

    raw = data[start:end]
    if b"\x00" in raw:
        return None

    try:
        value = raw.decode("cp1256", errors="strict")
    except UnicodeError:
        return None

    return value, end


def _layout_term_records_before_first_classtt(data: bytes, first_classtt_start: int) -> list[dict[str, object]]:
    scan_start = max(0, first_classtt_start - 12000)
    records: list[dict[str, object]] = []

    for offset in range(scan_start, first_classtt_start):
        parsed = _read_layout_text_record(data, offset)
        if not parsed:
            continue

        raw_text, end = parsed
        strict = _strict_layout_term(raw_text)
        if not strict:
            continue

        term, quality = strict
        records.append(
            {
                "offset": offset,
                "raw_text": raw_text,
                "term": term,
                "quality": quality,
                "end": end,
            }
        )

    return records


def _rank_layout_cycle_candidates(records: list[dict[str, object]]) -> list[dict[str, object]]:
    expected = ["الفصل بالكامل", "المجموعة 1", "المجموعة 2", "أولاد", "بنات"]
    candidates: list[dict[str, object]] = []

    for index, record in enumerate(records):
        if record.get("term") != expected[0]:
            continue

        selected = [record]
        cursor = int(record["offset"])
        ok = True

        for term in expected[1:]:
            matches = [
                candidate
                for candidate in records
                if candidate.get("term") == term and int(candidate["offset"]) > cursor
            ]
            if not matches:
                ok = False
                break
            nearest = min(matches, key=lambda item: int(item["offset"]) - cursor)
            gap = int(nearest["offset"]) - cursor
            if gap > 130:
                ok = False
                break
            selected.append(nearest)
            cursor = int(nearest["offset"])

        if not ok or len(selected) != 5:
            continue

        offsets = [int(item["offset"]) for item in selected]
        exact_count = sum(1 for item in selected if item.get("quality") == "EXACT")
        noise_count = len(selected) - exact_count
        score = exact_count * 100 - noise_count * 10
        candidates.append(
            {
                "offsets": offsets,
                "terms": [str(item["term"]) for item in selected],
                "qualities": [str(item["quality"]) for item in selected],
                "score": score,
                "exact": exact_count,
                "noise": noise_count,
                "span": offsets[-1] - offsets[0],
            }
        )

    candidates.sort(key=lambda item: (int(item["offsets"][0]), -int(item["score"])))
    return candidates


def _select_nonoverlap_layout_cycles(candidates: list[dict[str, object]], limit: int = 12) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    used_offsets: set[int] = set()

    for candidate in candidates:
        offsets = [int(value) for value in candidate["offsets"]]  # type: ignore[index]
        if any(offset in used_offsets for offset in offsets):
            continue
        cycle_no = len(selected) + 1
        item = dict(candidate)
        item["cycle"] = cycle_no
        item["synthetic_ids"] = list(range((cycle_no - 1) * 5, cycle_no * 5))
        selected.append(item)
        used_offsets.update(offsets)
        if len(selected) >= limit:
            break

    return selected


def _extract_classtt_layout_preview(data: bytes) -> dict[str, object]:
    starts = _true_classtt_record_starts(data)
    end_offsets: list[int] = []
    pos = 0
    while True:
        idx = data.find(b"CLASSTT_END", pos)
        if idx < 0:
            break
        end_offsets.append(idx)
        pos = idx + 1

    blocks: list[dict[str, object]] = []
    for block_index, start in enumerate(starts[:12], 1):
        labels = _decode_classtt_block_labels(data, start)
        label = labels[0] if labels else ""

        header_ids: list[int] = []
        for rel in (26, 30, 34, 38, 42):
            value = _read_u32_le(data, start + rel)
            if value is not None:
                header_ids.append(value)

        block_cycles = sorted({(value // 5) + 1 for value in header_ids})
        block_positions = [(value % 5) + 1 for value in header_ids]

        blocks.append(
            {
                "block": block_index,
                "label": label,
                "all_labels": labels,
                "start": start,
                "end_marker": end_offsets[block_index - 1] if block_index - 1 < len(end_offsets) else None,
                "header_ids": header_ids,
                "layout_cycles": block_cycles,
                "positions": block_positions,
            }
        )

    first_start = starts[0] if starts else 0
    term_records = _layout_term_records_before_first_classtt(data, first_start) if starts else []
    candidates = _rank_layout_cycle_candidates(term_records)
    selected_cycles = _select_nonoverlap_layout_cycles(candidates, limit=12)

    by_cycle = {int(item["cycle"]): item for item in selected_cycles}
    object_map: list[dict[str, object]] = []
    expected = ["الفصل بالكامل", "المجموعة 1", "المجموعة 2", "أولاد", "بنات"]

    for object_id in range(60):
        cycle = (object_id // 5) + 1
        position = (object_id % 5) + 1
        cycle_item = by_cycle.get(cycle)
        entry: dict[str, object] = {
            "id": object_id,
            "cycle": cycle,
            "position": position,
            "term_candidate": expected[position - 1],
            "status": "MISSING_LAYOUT_CYCLE",
        }
        if cycle_item:
            offsets = cycle_item.get("offsets", [])
            qualities = cycle_item.get("qualities", [])
            terms = cycle_item.get("terms", [])
            entry.update(
                {
                    "status": "FOUND",
                    "text_offset": offsets[position - 1] if len(offsets) >= position else None,
                    "quality": qualities[position - 1] if len(qualities) >= position else None,
                    "term": terms[position - 1] if len(terms) >= position else None,
                }
            )
        object_map.append(entry)

    all_header_ids = [value for block in blocks for value in block.get("header_ids", [])]  # type: ignore[union-attr]

    return {
        "parser_stage": "classtt_layout_preview_read_only",
        "sample_counts": {
            "raw_CLASSTT": data.count(b"CLASSTT"),
            "true_CLASSTT_records": len(starts),
            "CLASSTT_END": len(end_offsets),
        },
        "true_record_starts": starts[:12],
        "blocks": blocks,
        "layout_cycles": selected_cycles,
        "object_map_preview": object_map,
        "summary": {
            "selected_layout_cycle_count": len(selected_cycles),
            "selected_exactly_12_cycles": len(selected_cycles) == 12,
            "total_header_ids": len(all_header_ids),
            "unique_header_ids": len(set(all_header_ids)),
            "covers_exact_0_to_59": sorted(set(all_header_ids)) == list(range(60)),
            "header_ids_are_layout_object_references": sorted(set(all_header_ids)) == list(range(60)),
            "slot_tuple_proven": False,
            "teacher_subject_period_class_day_tuple_proven": False,
            "safe_to_import_slots": False,
            "safe_to_confirm": False,
        },
        "safety_decision": {
            "safe_to_import_slots": False,
            "safe_to_confirm": False,
            "reason": "CLASSTT layout preview maps binary header ids to layout object cycles only; it does not prove class + day + period + subject + teacher.",
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
            "classtt_layout_preview": _extract_classtt_layout_preview(data),
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
