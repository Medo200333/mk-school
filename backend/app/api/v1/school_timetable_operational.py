from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime, time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.roz_evidence import analyze_roz_file, summarize_for_cli
from pathlib import Path

router = APIRouter(prefix="/api/v1/school-timetable", tags=["school-timetable"])


class TimetableCsvImport(BaseModel):
    batch_name: str = "استيراد TimeTable"
    csv_text: str


def rows(result) -> list[dict[str, Any]]:
    return [dict(row._mapping) for row in result]



def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [json_safe(v) for v in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


async def audit_event(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    exists = await db.execute(text("SELECT to_regclass('audit.events')"))
    if exists.scalar_one() is None:
        return

    await db.execute(
        text("""
            INSERT INTO audit.events(actor, action, entity_type, entity_id, payload)
            VALUES ('school-timetable-api', :action, :entity_type, :entity_id, CAST(:payload AS jsonb))
        """),
        {
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "payload": json.dumps(json_safe(payload or {}), ensure_ascii=False),
        },
    )


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(text("""
        SELECT
          (SELECT count(*) FROM school.teachers) AS teachers_count,
          (SELECT count(*) FROM school.teachers WHERE employee_id IS NOT NULL) AS hr_linked_teachers_count,
          (SELECT count(*) FROM school.school_classes) AS classes_count,
          (SELECT count(*) FROM school.subjects) AS subjects_count,
          (SELECT COALESCE(sum(weekly_lessons), 0) FROM school.curriculum_plans WHERE is_active = true) AS planned_weekly_lessons_count,
          (SELECT count(*) FROM school.timetable_constraints WHERE is_active = true AND constraint_type = 'hard') AS hard_constraints_count,
          (SELECT count(*) FROM school.timetable_constraints WHERE is_active = true AND constraint_type = 'soft') AS soft_constraints_count,
          (SELECT count(*) FROM school.classrooms) AS classrooms_count,
          (SELECT count(*) FROM school.lesson_periods) AS periods_count,
          (SELECT count(*) FROM school.timetable_versions) AS versions_count,
          (SELECT count(*) FROM school.timetable_slots) AS slots_count,
          (SELECT count(*) FROM school.timetable_generation_runs) AS generation_runs_count,
          (SELECT count(*) FROM school.timetable_import_batches) AS imports_count,
          (SELECT count(*) FROM school.vw_school_timetable_conflicts) AS hard_conflicts_count
    """))
    return dict(result.one()._mapping)


@router.get("/readiness")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    data = await summary(db)
    checks = [
        {
            "code": "academic_time",
            "name_ar": "الأيام والحصص",
            "ready": data["periods_count"] > 0,
            "message_ar": "تم إعداد حصص اليوم الدراسي" if data["periods_count"] > 0 else "شغل تجهيز الأيام والحصص أولًا",
        },
        {
            "code": "school_resources",
            "name_ar": "موارد المدرسة",
            "ready": data["classes_count"] > 0 and data["subjects_count"] > 0 and data["classrooms_count"] > 0,
            "message_ar": "الفصول والمواد والقاعات جاهزة" if data["classes_count"] > 0 and data["subjects_count"] > 0 and data["classrooms_count"] > 0 else "أضف فصولًا ومواد وقاعات قبل الاعتماد",
        },
        {
            "code": "curriculum_matrix",
            "name_ar": "الخطة الأسبوعية",
            "ready": data["planned_weekly_lessons_count"] > 0,
            "message_ar": "تم إدخال Curriculum Matrix" if data["planned_weekly_lessons_count"] > 0 else "أدخل الخطة الأسبوعية قبل التوليد",
        },
        {
            "code": "hr_teacher_link",
            "name_ar": "ربط HR بالمدرسين",
            "ready": data["hr_linked_teachers_count"] > 0 or data["teachers_count"] == 0,
            "message_ar": "يوجد مدرسون مرتبطون ببرنامج الموظفين" if data["hr_linked_teachers_count"] > 0 else "زامن المدرسين من برنامج الموظفين",
        },
        {
            "code": "hard_conflicts",
            "name_ar": "التعارضات الصارمة",
            "ready": data["hard_conflicts_count"] == 0,
            "message_ar": "لا توجد تعارضات صارمة" if data["hard_conflicts_count"] == 0 else "لا تنشر جدولًا به تعارضات",
        },
        {
            "code": "published_data",
            "name_ar": "دروس الجدول",
            "ready": data["slots_count"] > 0,
            "message_ar": "يوجد جدول قابل للمراجعة" if data["slots_count"] > 0 else "استورد أو أضف دروس الجدول",
        },
    ]

    return {
        "ready": all(item["ready"] for item in checks),
        "checks": checks,
        "summary": data,
    }


@router.post("/bootstrap")
async def bootstrap(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    await db.execute(text("""
        INSERT INTO school.week_days(day_code, name_ar, sort_order)
        VALUES
        ('saturday', 'السبت', 1),
        ('sunday', 'الأحد', 2),
        ('monday', 'الإثنين', 3),
        ('tuesday', 'الثلاثاء', 4),
        ('wednesday', 'الأربعاء', 5),
        ('thursday', 'الخميس', 6)
        ON CONFLICT (day_code)
        DO UPDATE SET name_ar = EXCLUDED.name_ar, sort_order = EXCLUDED.sort_order
    """))

    await db.execute(text("""
        INSERT INTO school.lesson_periods(period_no, name_ar, starts_at, ends_at)
        VALUES
        (1, 'الحصة 1', TIME '08:00', TIME '08:45'),
        (2, 'الحصة 2', TIME '08:50', TIME '09:35'),
        (3, 'الحصة 3', TIME '09:40', TIME '10:25'),
        (4, 'الحصة 4', TIME '10:45', TIME '11:30'),
        (5, 'الحصة 5', TIME '11:35', TIME '12:20'),
        (6, 'الحصة 6', TIME '12:25', TIME '13:10'),
        (7, 'الحصة 7', TIME '13:15', TIME '14:00')
        ON CONFLICT (period_no)
        DO UPDATE SET
          name_ar = EXCLUDED.name_ar,
          starts_at = EXCLUDED.starts_at,
          ends_at = EXCLUDED.ends_at
    """))

    exists = await db.execute(text("""
        SELECT id
        FROM school.timetable_versions
        WHERE is_current = true
        ORDER BY created_at DESC
        LIMIT 1
    """))

    if exists.first() is None:
        await db.execute(text("""
            INSERT INTO school.timetable_versions(name_ar, status, is_current)
            VALUES ('جدول المدرسة الأساسي', 'draft', true)
        """))

    await audit_event(db, "bootstrap", "school_timetable", payload={"source": "document_requirements"})
    await db.commit()
    return await summary(db)


@router.get("/week-days")
async def week_days(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("SELECT * FROM school.week_days ORDER BY sort_order"))
    return rows(result)


@router.get("/periods")
async def periods(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("SELECT * FROM school.lesson_periods ORDER BY period_no"))
    return rows(result)


@router.get("/grid")
async def grid(
    version_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    if version_id:
        result = await db.execute(text("""
            SELECT *
            FROM school.vw_school_timetable_grid
            WHERE timetable_version_id = CAST(:version_id AS uuid)
            ORDER BY day_order, period_no, class_code
            LIMIT 2000
        """), {"version_id": version_id})
    else:
        result = await db.execute(text("""
            SELECT *
            FROM school.vw_school_timetable_grid
            ORDER BY day_order, period_no, class_code
            LIMIT 2000
        """))

    return rows(result)


def _weekly_board_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _weekly_board_json_row(row: Any) -> dict[str, Any]:
    mapping = row._mapping if hasattr(row, "_mapping") else row
    return {str(key): _weekly_board_json_value(value) for key, value in dict(mapping).items()}


@router.get("/weekly-board")
async def weekly_board(
    version_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if version_id:
        version_result = await db.execute(
            text("""
                SELECT id, name_ar, status, is_current, effective_from, effective_to, created_at
                FROM school.timetable_versions
                WHERE id = CAST(:version_id AS uuid)
                LIMIT 1
            """),
            {"version_id": version_id},
        )
    else:
        version_result = await db.execute(text("""
            SELECT id, name_ar, status, is_current, effective_from, effective_to, created_at
            FROM school.timetable_versions
            WHERE is_current = true
            ORDER BY created_at DESC
            LIMIT 1
        """))

    version_row = version_result.first()
    if version_row is None:
        raise HTTPException(status_code=404, detail="نسخة الجدول غير موجودة")

    version = _weekly_board_json_row(version_row)
    selected_version_id = str(version["id"])

    days_result = await db.execute(text("""
        SELECT id, day_code, name_ar, sort_order
        FROM school.week_days
        ORDER BY sort_order
    """))

    periods_result = await db.execute(text("""
        SELECT id, period_no, name_ar, starts_at, ends_at, is_break, is_active
        FROM school.lesson_periods
        WHERE is_active = true
        ORDER BY period_no
    """))

    classes_result = await db.execute(text("""
        SELECT id, class_code, class_name_ar, stage_name_ar, grade_name_ar, capacity
        FROM school.school_classes
        WHERE is_active = true
        ORDER BY class_code
    """))

    slots_result = await db.execute(
        text("""
            SELECT
              ts.id AS slot_id,
              ts.timetable_version_id,
              ts.school_class_id,
              ts.week_day_id,
              ts.period_id,
              ts.subject_name_ar,
              COALESCE(sub.color_code, '#8b5a2b') AS subject_color,
              ts.teacher_id,
              tea.teacher_code,
              tea.teacher_name_ar,
              ts.classroom_id,
              COALESCE(room.room_name_ar, room.name_ar) AS room_name_ar,
              ts.slot_type,
              ts.notes
            FROM school.timetable_slots ts
            LEFT JOIN school.subjects sub ON sub.subject_name_ar = ts.subject_name_ar
            LEFT JOIN school.teachers tea ON tea.id = ts.teacher_id
            LEFT JOIN school.classrooms room ON room.id = ts.classroom_id
            WHERE ts.timetable_version_id = CAST(:version_id AS uuid)
            ORDER BY ts.week_day_id, ts.period_id, ts.school_class_id
        """),
        {"version_id": selected_version_id},
    )

    days = [_weekly_board_json_row(row) for row in days_result]
    periods = [_weekly_board_json_row(row) for row in periods_result]
    classes = [_weekly_board_json_row(row) for row in classes_result]
    slots = [_weekly_board_json_row(row) for row in slots_result]

    slot_by_key: dict[tuple[str, int, str], dict[str, Any]] = {}
    for slot in slots:
        key = (
            str(slot["school_class_id"]),
            int(slot["week_day_id"]),
            str(slot["period_id"]),
        )
        slot_by_key[key] = slot

    cells: list[dict[str, Any]] = []
    matrix: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}

    for class_row in classes:
        class_id = str(class_row["id"])
        matrix[class_id] = {}

        for day in days:
            day_id = int(day["id"])
            day_key = str(day_id)
            matrix[class_id][day_key] = {}

            for period in periods:
                period_id = str(period["id"])
                slot = slot_by_key.get((class_id, day_id, period_id))

                cell = {
                    "school_class_id": class_id,
                    "class_code": class_row.get("class_code"),
                    "class_name_ar": class_row.get("class_name_ar"),
                    "stage_name_ar": class_row.get("stage_name_ar"),
                    "grade_name_ar": class_row.get("grade_name_ar"),
                    "week_day_id": day_id,
                    "day_code": day.get("day_code"),
                    "day_name_ar": day.get("name_ar"),
                    "day_order": day.get("sort_order"),
                    "period_id": period_id,
                    "period_no": period.get("period_no"),
                    "period_name_ar": period.get("name_ar"),
                    "starts_at": period.get("starts_at"),
                    "ends_at": period.get("ends_at"),
                    "is_break": period.get("is_break"),
                    "slot_id": None,
                    "subject_name_ar": None,
                    "subject_color": None,
                    "teacher_id": None,
                    "teacher_code": None,
                    "teacher_name_ar": None,
                    "classroom_id": None,
                    "room_name_ar": None,
                    "slot_type": "free",
                    "notes": None,
                    "is_empty": True,
                }

                if slot:
                    cell.update(
                        {
                            "slot_id": slot.get("slot_id"),
                            "subject_name_ar": slot.get("subject_name_ar"),
                            "subject_color": slot.get("subject_color"),
                            "teacher_id": slot.get("teacher_id"),
                            "teacher_code": slot.get("teacher_code"),
                            "teacher_name_ar": slot.get("teacher_name_ar"),
                            "classroom_id": slot.get("classroom_id"),
                            "room_name_ar": slot.get("room_name_ar"),
                            "slot_type": slot.get("slot_type") or "lesson",
                            "notes": slot.get("notes"),
                            "is_empty": False,
                        }
                    )

                cells.append(cell)
                matrix[class_id][day_key][period_id] = cell

    total_cells = len(cells)
    filled_cells = sum(1 for cell in cells if not cell["is_empty"])
    empty_cells = total_cells - filled_cells

    return {
        "version": version,
        "days": days,
        "periods": periods,
        "classes": classes,
        "cells": cells,
        "matrix": matrix,
        "counts": {
            "classes": len(classes),
            "days": len(days),
            "periods": len(periods),
            "slots": filled_cells,
            "empty_cells": empty_cells,
            "total_cells": total_cells,
        },
        "safe_to_print": bool(classes and days and periods),
        "source": {
            "table": "school.timetable_slots",
            "subject_contract": "subject_name_ar",
            "read_only": True,
            "slot_import_from_roz": False,
        },
        "notes_ar": [
            "هذا endpoint قراءة فقط ولا يغير قاعدة البيانات.",
            "مصدر الحقيقة هو school.timetable_slots.",
            "جدول الحصص الحالي يعتمد على subject_name_ar لأن timetable_slots لا يحتوي subject_id.",
            "استيراد خانات ROZ ما زال ممنوعًا حتى يثبت ربط CLASSTT بالأيام والحصص والمدرسين.",
        ],
    }


@router.get("/teacher-load")
async def teacher_load(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT *
        FROM school.vw_school_teacher_load
        ORDER BY weekly_lessons_count DESC, teacher_name_ar
    """))
    return rows(result)


@router.get("/quality")
async def quality(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT *
        FROM school.vw_school_timetable_quality
        ORDER BY quality_score DESC, timetable_name_ar
    """))
    return rows(result)


@router.get("/conflicts")
async def conflicts(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT
          c.conflict_type,
          c.severity,
          tv.name_ar AS timetable_name_ar,
          wd.name_ar AS day_name_ar,
          lp.name_ar AS period_name_ar,
          c.entity_id,
          c.conflict_count
        FROM school.vw_school_timetable_conflicts c
        JOIN school.timetable_versions tv ON tv.id = c.timetable_version_id
        JOIN school.week_days wd ON wd.id = c.week_day_id
        JOIN school.lesson_periods lp ON lp.id = c.period_id
        ORDER BY wd.sort_order, lp.period_no, c.conflict_type
    """))
    return rows(result)


@router.post("/validation/run")
async def validation_run(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    readiness_result = await readiness(db)
    conflicts_result = await conflicts(db)
    quality_result = await quality(db)
    await audit_event(
        db,
        "validation_run",
        "school_timetable",
        payload={
            "ready": readiness_result["ready"],
            "hard_conflicts": len(conflicts_result),
            "quality_items": len(quality_result),
        },
    )
    await db.commit()
    return {
        "readiness": readiness_result,
        "conflicts": conflicts_result,
        "quality": quality_result,
    }


@router.get("/reports/teachers")
async def report_teachers(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    return await teacher_load(db)


@router.get("/reports/classes")
async def report_classes(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT
          class_code,
          class_name_ar,
          count(id) AS scheduled_lessons
        FROM school.vw_school_timetable_grid
        GROUP BY class_code, class_name_ar
        ORDER BY class_code
    """))
    return rows(result)


@router.get("/reports/rooms")
async def report_rooms(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT
          COALESCE(room_name_ar, 'بدون قاعة') AS room_name_ar,
          count(id) AS scheduled_lessons
        FROM school.vw_school_timetable_grid
        GROUP BY room_name_ar
        ORDER BY scheduled_lessons DESC, room_name_ar
    """))
    return rows(result)


@router.get("/reports/quality")
async def report_quality(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    return await quality(db)


@router.post("/sync/hr-teachers")
async def sync_hr_teachers(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    exists = await db.execute(text("SELECT to_regclass('hr.teacher_profiles')"))
    if exists.scalar_one() is None:
        raise HTTPException(status_code=409, detail="برنامج الموظفين غير مثبت في قاعدة البيانات")

    result = await db.execute(text("""
        WITH source_teachers AS (
            SELECT
                e.id AS employee_id,
                COALESCE(e.employee_no, e.id::text) AS teacher_code,
                e.full_name_ar AS teacher_name_ar,
                tp.specialization
            FROM hr.teacher_profiles tp
            JOIN hr.employees e ON e.id = tp.employee_id
            WHERE e.status = 'active'
        ),
        upserted AS (
            INSERT INTO school.teachers(employee_id, teacher_code, teacher_name_ar, specialization)
            SELECT employee_id, teacher_code, teacher_name_ar, specialization
            FROM source_teachers
            ON CONFLICT (employee_id) WHERE employee_id IS NOT NULL
            DO UPDATE SET
              teacher_code = EXCLUDED.teacher_code,
              teacher_name_ar = EXCLUDED.teacher_name_ar,
              specialization = EXCLUDED.specialization,
              is_active = true
            RETURNING id
        )
        SELECT count(*) AS synced_count FROM upserted
    """))
    synced_count = int(result.scalar_one())
    await audit_event(
        db,
        "sync_hr_teachers",
        "school_timetable",
        payload={"synced_count": synced_count},
    )
    await db.commit()
    return {"synced_count": synced_count}


async def get_or_create_class(db: AsyncSession, class_code: str) -> Any:
    found = await db.execute(
        text("SELECT id FROM school.school_classes WHERE class_code = :code LIMIT 1"),
        {"code": class_code},
    )
    row = found.first()
    if row:
        return row._mapping["id"]

    created = await db.execute(
        text("""
            INSERT INTO school.school_classes(class_code, class_name_ar)
            VALUES (:code, :name)
            RETURNING id
        """),
        {"code": class_code, "name": class_code},
    )
    return created.one()._mapping["id"]


async def get_or_create_teacher(db: AsyncSession, teacher_name: str) -> Any:
    found = await db.execute(
        text("""
            SELECT id
            FROM school.teachers
            WHERE teacher_code = :code OR teacher_name_ar = :name
            LIMIT 1
        """),
        {"code": teacher_name, "name": teacher_name},
    )
    row = found.first()
    if row:
        return row._mapping["id"]

    created = await db.execute(
        text("""
            INSERT INTO school.teachers(teacher_code, teacher_name_ar)
            VALUES (:code, :name)
            RETURNING id
        """),
        {"code": teacher_name, "name": teacher_name},
    )
    return created.one()._mapping["id"]


async def get_or_create_room(db: AsyncSession, room_name: str) -> Any:
    found = await db.execute(
        text("""
            SELECT id
            FROM school.classrooms
            WHERE room_code = :code OR room_name_ar = :name
            LIMIT 1
        """),
        {"code": room_name, "name": room_name},
    )
    row = found.first()
    if row:
        return row._mapping["id"]

    created = await db.execute(
        text("""
            INSERT INTO school.classrooms(room_code, room_name_ar, name_ar)
            VALUES (:code, :name, :name)
            RETURNING id
        """),
        {"code": room_name, "name": room_name},
    )
    return created.one()._mapping["id"]



class RozInspectPayload(BaseModel):
    file_path: str = "import_samples/mmmmmmmmmmm2-2.roz"
    max_records: int = 800


def _safe_import_sample_path(raw_path: str) -> Path:
    root = Path.cwd().resolve()
    import_root = (root / "import_samples").resolve()
    requested = Path(raw_path)

    if not requested.is_absolute():
        requested = root / requested

    resolved = requested.resolve()

    if import_root not in resolved.parents and resolved != import_root:
        raise HTTPException(
            status_code=400,
            detail="مسموح بقراءة ملفات ROZ فقط من مجلد import_samples داخل المشروع",
        )

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail=f"ملف ROZ غير موجود: {raw_path}")

    if resolved.suffix.lower() != ".roz":
        raise HTTPException(status_code=400, detail="الملف المطلوب ليس بصيغة .roz")

    return resolved


def _decode_cp1256_chunk(chunk: bytes) -> str:
    return chunk.decode("cp1256", errors="ignore").replace("\x00", "").strip()


def _clean_roz_text(value: str) -> str:
    value = value.replace("\r", "\n")
    value = re.sub(r"[ے]{3,}", "", value)
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+", " ", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n+", "\n", value)
    return value.strip()


def _interesting_roz_text(value: str) -> bool:
    if not value:
        return False
    if len(value) < 2:
        return False

    markers = (
        "ASCTT",
        "CLASSTT",
        "CLASSTT_END",
        "teacher_row",
        "class_row",
        "report_header",
        "Master",
        "الحصة",
        "الصف",
        "الدراسي",
        "2024/2025",
    )
    if any(marker in value for marker in markers):
        return True

    arabic_chars = sum(1 for ch in value if "\u0600" <= ch <= "\u06ff")
    return arabic_chars >= 3


def _extract_ascii_runs(data: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    pattern = re.compile(rb"[\x20-\x7e]{3,}")
    for match in pattern.finditer(data):
        raw = match.group(0)
        text_value = raw.decode("ascii", errors="ignore").strip()
        if _interesting_roz_text(text_value):
            records.append(
                {
                    "offset": match.start(),
                    "kind": "ascii_run",
                    "encoding": "ascii",
                    "length": len(raw),
                    "text": text_value,
                }
            )
    return records


def _extract_cp1256_runs(data: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current = bytearray()
    start = 0

    def flush(end: int) -> None:
        nonlocal current, start
        if len(current) >= 3:
            decoded = _clean_roz_text(_decode_cp1256_chunk(bytes(current)))
            if _interesting_roz_text(decoded):
                records.append(
                    {
                        "offset": start,
                        "kind": "cp1256_run",
                        "encoding": "cp1256",
                        "length": len(current),
                        "text": decoded,
                    }
                )
        current = bytearray()

    for index, byte in enumerate(data):
        is_textish = (
            byte in (9, 10, 13)
            or 32 <= byte <= 126
            or 0xC1 <= byte <= 0xFF
            or byte in (0x80, 0x81, 0x8A, 0x8C, 0x8D, 0x8E, 0x90, 0x98, 0x9A, 0x9C, 0x9D, 0x9E)
        )
        if is_textish:
            if not current:
                start = index
            current.append(byte)
        else:
            flush(index)

    flush(len(data))
    return records


def _extract_pascal_strings(data: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    size = len(data)

    for offset, length in enumerate(data):
        if length < 3 or length > 120:
            continue

        end = offset + 1 + length
        if end > size:
            continue

        chunk = data[offset + 1:end]
        decoded = _clean_roz_text(_decode_cp1256_chunk(chunk))

        if _interesting_roz_text(decoded):
            records.append(
                {
                    "offset": offset,
                    "kind": "pascal_u8",
                    "encoding": "cp1256",
                    "length": length,
                    "text": decoded,
                }
            )

    return records



def _roz_window_text(data: bytes, marker: bytes, radius: int = 420) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    start = 0

    while True:
        pos = data.find(marker, start)
        if pos < 0:
            break

        left = max(0, pos - radius)
        right = min(len(data), pos + len(marker) + radius)
        decoded = _clean_roz_text(_decode_cp1256_chunk(data[left:right]))

        windows.append(
            {
                "marker": marker.decode("ascii", errors="ignore"),
                "offset": pos,
                "text": decoded[:1800],
            }
        )
        start = pos + len(marker)

    return windows


def _meaningful_arabic_records(records: list[dict[str, Any]], limit: int = 160) -> list[dict[str, Any]]:
    useful: list[dict[str, Any]] = []
    seen: set[str] = set()

    noise_tokens = ("ےے", "ززز", "€", "†", "™", "گپ", "ذK", "ثگ", "cp1256")
    keep_tokens = (
        "الحصة",
        "الصف الدراسي",
        "CLASSTT",
        "CLASSTT_END",
        "teacher_row",
        "class_row",
        "report_header",
        "Master",
        "2024/2025",
    )

    for row in records:
        value = _clean_roz_text(str(row.get("text") or ""))
        if not value:
            continue

        has_keep = any(token in value for token in keep_tokens)
        arabic_count = sum(1 for ch in value if "\u0600" <= ch <= "\u06ff")
        too_noisy = any(token in value for token in noise_tokens) and not has_keep

        if too_noisy:
            continue

        if not has_keep and arabic_count < 5:
            continue

        compact = re.sub(r"\s+", " ", value).strip()
        if compact in seen:
            continue
        seen.add(compact)

        useful.append(
            {
                "offset": row.get("offset"),
                "kind": row.get("kind"),
                "encoding": row.get("encoding"),
                "length": row.get("length"),
                "text": value,
            }
        )

        if len(useful) >= limit:
            break

    return useful


def _extract_classtt_blocks(data: bytes, limit: int = 40) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    marker = b"CLASSTT"
    end_marker = b"CLASSTT_END"
    start = 0

    while len(blocks) < limit:
        pos = data.find(marker, start)
        if pos < 0:
            break

        end = data.find(end_marker, pos)
        if end < 0:
            block_end = min(len(data), pos + 1500)
            closed = False
        else:
            block_end = min(len(data), end + len(end_marker) + 260)
            closed = True

        raw = data[pos:block_end]
        decoded = _clean_roz_text(_decode_cp1256_chunk(raw))
        class_refs = sorted(set(re.findall(r"CLASSTT\d+/\d+", decoded)))
        numeric_refs = sorted(set(re.findall(r"\b\d{1,2}/\d{1,2}\b", decoded)))

        blocks.append(
            {
                "offset": pos,
                "closed": closed,
                "byte_length": len(raw),
                "class_refs": class_refs,
                "numeric_refs": numeric_refs,
                "text_preview": decoded[:1400],
            }
        )
        start = pos + len(marker)

    return blocks


def _arabic_phrase_parts(value: str) -> list[str]:
    cleaned = _clean_roz_text(value)
    cleaned = re.sub(r"[A-Za-z0-9#@_\-\\/|{}\[\]().,;:!?\"'`~+=*&%^$<>]+", " ", cleaned)
    cleaned = re.sub(r"[^\u0600-\u06ff\s]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return re.findall(r"[\u0600-\u06ff]{2,}(?:\s+[\u0600-\u06ff]{2,}){0,4}", cleaned)


def _compact_arabic_phrase(value: str) -> str:
    words = [w for w in value.split() if len(w) >= 2]
    if not words:
        return ""

    if len(words) >= 4 and len(words) % 2 == 0:
        half = len(words) // 2
        if words[:half] == words[half:]:
            words = words[:half]

    if len(words) >= 3 and words[-1] == words[0]:
        words = words[:-1]

    if len(words) >= 3 and words[-1] == words[1]:
        words = words[:2]

    return " ".join(words).strip()


def _dedup_entity_rows(rows: list[dict[str, Any]], key_name: str, limit: int = 80) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []

    for row in rows:
        key = str(row.get(key_name, "")).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(row)
        if len(output) >= limit:
            break

    return output


def _extract_roz_teacher_candidates(records: list[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    subject_words = {
        "قران",
        "كريم",
        "تربية",
        "دينية",
        "اسلامية",
        "لغة",
        "عربية",
        "رياضيات",
        "انجليزية",
        "متعدد",
        "التربية",
        "الرياضية",
        "دراسات",
        "علوم",
        "فنية",
        "مهارات",
        "مهنية",
        "العاب",
        "ودين",
        "توكاتسو",
        "تكنولجيا",
        "تكنولوجيا",
        "عربي",
        "رياضة",
    }
    structural_words = {
        "الصف",
        "الدراسي",
        "الحصة",
        "الاولي",
        "الثانية",
        "الثالثة",
        "الرابعة",
        "الخامسة",
        "الفصل",
        "بالكامل",
        "بنات",
        "أولاد",
        "اولاد",
        "المجموعة",
        "المعلمون",
        "المواد",
        "الغرف",
        "الدراسية",
        "الطلاب",
        "الكل",
    }

    candidates: list[dict[str, Any]] = []

    for record in sorted(records, key=lambda row: int(row.get("offset", 0))):
        offset = int(record.get("offset", 0))
        text_value = str(record.get("text", ""))

        # In this ASCTT sample, the clean teacher-name band starts after the subject band.
        # Keep this as confidence scoring, not a hard parser contract.
        offset_score = 2 if 106000 <= offset <= 132200 else 0

        for phrase in _arabic_phrase_parts(text_value):
            compact = _compact_arabic_phrase(phrase)
            words = compact.split()

            if len(words) < 2 or len(words) > 4:
                continue

            word_set = set(words)
            if word_set & subject_words:
                continue
            if word_set & structural_words:
                continue

            if len(compact) < 7 or len(compact) > 45:
                continue

            arabic_chars = sum(1 for ch in compact if "\u0600" <= ch <= "\u06ff")
            if arabic_chars < 6:
                continue

            confidence = 50 + offset_score * 20
            if len(words) in {2, 3}:
                confidence += 10
            if any(token in compact for token in ("عبد", "محمد", "ابراهيم", "حسن", "حسين", "السيد")):
                confidence += 10

            candidates.append(
                {
                    "teacher_name_ar": compact,
                    "offset": offset,
                    "source_kind": record.get("kind"),
                    "source_length": record.get("length"),
                    "confidence": min(confidence, 99),
                    "source_text": text_value[:120],
                }
            )

    return _dedup_entity_rows(
        sorted(candidates, key=lambda row: (-int(row["confidence"]), int(row["offset"]), row["teacher_name_ar"])),
        "teacher_name_ar",
        limit=limit,
    )


def _extract_roz_subject_candidates(records: list[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    known_subject_patterns = [
        "قران كريم",
        "تربية دينية اسلامية",
        "تربية دينية",
        "لغة عربية",
        "رياضيات",
        "لغة انجليزية",
        "متعدد",
        "التربية الرياضية",
        "تربية الرياضية",
        "دراسات",
        "علوم",
        "تربية فنية مهارات مهنية",
        "تربية فنية",
        "مهارات مهنية",
        "العاب ودين",
        "توكاتسو",
        "تكنولوجيا",
        "تكنولجيا",
    ]

    candidates: list[dict[str, Any]] = []

    for record in sorted(records, key=lambda row: int(row.get("offset", 0))):
        offset = int(record.get("offset", 0))
        text_value = _clean_roz_text(str(record.get("text", "")))

        for subject in known_subject_patterns:
            if subject in text_value:
                confidence = 95 if 103000 <= offset <= 106000 else 75
                candidates.append(
                    {
                        "subject_name_ar": subject,
                        "offset": offset,
                        "source_kind": record.get("kind"),
                        "confidence": confidence,
                        "source_text": text_value[:120],
                    }
                )

    return _dedup_entity_rows(
        sorted(candidates, key=lambda row: (-int(row["confidence"]), int(row["offset"]), row["subject_name_ar"])),
        "subject_name_ar",
        limit=limit,
    )


def _canonicalize_roz_teacher_name(raw_name: str) -> str:
    value = _clean_roz_text(raw_name)
    value = re.sub(r"[^\u0600-\u06ff\s]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    noise_words = {
        "ءد",
        "ء",
        "د",
        "ج",
        "ف",
        "لٹ",
        "رث",
        "ےجے",
        "ےے",
        "استاذ",
        "م،",
        "م",
    }

    words = [w for w in value.split() if len(w) >= 2 and w not in noise_words]

    if len(words) >= 4 and len(words) % 2 == 0:
        half = len(words) // 2
        if words[:half] == words[half:]:
            words = words[:half]

    if len(words) >= 3 and words[-1] == words[0]:
        words = words[:-1]

    if len(words) >= 3 and words[-1] == words[1]:
        words = words[:2]

    return " ".join(words).strip()


def _is_probably_partial_teacher_name(name: str) -> bool:
    partial_tails = {
        "اسما",
        "ابرا",
        "ابراه",
        "حسي",
        "عبد ال",
        "عبد ا",
        "فے",
        "جے",
        "جےے",
        "ےج",
        "ےےج",
        "ےے",
        "ال",
    }
    return any(name.endswith(tail) for tail in partial_tails)


def _is_roz_structural_or_school_phrase(name: str) -> bool:
    bad_terms = {
        "جداولهم",
        "المخطط",
        "العام",
        "الحصص",
        "عقبة",
        "نافع",
        "الابتدائى",
        "خيارات",
        "الطلا",
        "الطلاب",
        "الانتهاء",
        "الغرف",
        "الدراسية",
        "المعلمون",
        "المواد",
        "الفصل",
        "بالكامل",
        "بنات",
        "أولاد",
        "اولاد",
        "المجموعة",
    }
    return bool(set(name.split()) & bad_terms)


def _looks_like_complete_teacher_name(name: str) -> bool:
    words = name.split()
    if len(words) < 2 or len(words) > 4:
        return False
    if len(name) < 7 or len(name) > 40:
        return False
    if _is_probably_partial_teacher_name(name):
        return False
    if _is_roz_structural_or_school_phrase(name):
        return False
    return True


def _known_teacher_name_hits(text_value: str) -> list[str]:
    # Deterministic names proven from the same ROZ binary discovery windows.
    known = [
        "سماح ابراهيم",
        "هدي محمد",
        "فاطمة اسماعيل",
        "صفية صابر",
        "محمد كمال",
        "جيرمين حسين",
        "حنان عبد المحي",
        "رضا السيد",
        "منال عبد الحميد",
        "رشا عبد الحافظ",
        "عفاف حامد",
        "ايمان حسن",
        "سيد عبد الهادي",
        "رانيا ابراهيم",
        "امل محمد",
        "مصطفي",
        "عبدالله",
    ]
    return [name for name in known if name in text_value]


def _teacher_name_quality_score(name: str, confidence: int, offset: int) -> int:
    score = confidence
    words = name.split()

    if 106000 <= offset <= 132200:
        score += 20

    if len(words) in {2, 3}:
        score += 8

    if any(token in name for token in ("عبد", "محمد", "ابراهيم", "حسن", "حسين", "السيد", "كمال")):
        score += 6

    if len(words) == 1:
        score -= 30

    if _is_roz_structural_or_school_phrase(name):
        score -= 100

    if _is_probably_partial_teacher_name(name):
        score -= 80

    return min(score, 100)


def _extract_roz_canonical_teachers(raw_teachers: list[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    cleaned_rows: list[dict[str, Any]] = []

    for row in raw_teachers:
        offset = int(row.get("offset") or 0)
        source_text = str(row.get("source_text") or row.get("teacher_name_ar") or "")
        confidence = int(row.get("confidence") or 0)

        names_to_try = [str(row.get("teacher_name_ar") or "")]
        names_to_try.extend(_known_teacher_name_hits(source_text))

        for candidate in names_to_try:
            canonical = _canonicalize_roz_teacher_name(candidate)

            if not _looks_like_complete_teacher_name(canonical):
                continue

            cleaned_rows.append(
                {
                    "teacher_name_ar": canonical,
                    "source_teacher_name_ar": row.get("teacher_name_ar"),
                    "offset": offset,
                    "confidence": _teacher_name_quality_score(canonical, confidence, offset),
                    "source_kind": row.get("source_kind"),
                }
            )

    # Deduplicate exact names first.
    best_by_name: dict[str, dict[str, Any]] = {}
    for row in cleaned_rows:
        name = str(row["teacher_name_ar"])
        existing = best_by_name.get(name)
        if existing is None:
            best_by_name[name] = row
            continue

        current_key = (int(row.get("confidence") or 0), -int(row.get("offset") or 0))
        existing_key = (int(existing.get("confidence") or 0), -int(existing.get("offset") or 0))
        if current_key > existing_key:
            best_by_name[name] = row

    # Remove reversed duplicates only when the same token set exists.
    best_by_token_set: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in sorted(best_by_name.values(), key=lambda r: (-int(r.get("confidence") or 0), int(r.get("offset") or 0))):
        name = str(row["teacher_name_ar"])
        token_set = tuple(sorted(name.split()))
        existing = best_by_token_set.get(token_set)

        if existing is None:
            best_by_token_set[token_set] = row
            continue

        current_key = (
            int(row.get("confidence") or 0),
            len(name.split()),
            -int(row.get("offset") or 0),
        )
        existing_name = str(existing["teacher_name_ar"])
        existing_key = (
            int(existing.get("confidence") or 0),
            len(existing_name.split()),
            -int(existing.get("offset") or 0),
        )

        if current_key > existing_key:
            best_by_token_set[token_set] = row

    rows = sorted(best_by_token_set.values(), key=lambda r: int(r.get("offset") or 0))

    # Proven teacher names discovered from the same ROZ binary in Phase 6M/6N.
    # This is still preview-only and remains safe_to_import=false.
    proven_offsets = {
        "سماح ابراهيم": 106873,
        "هدي محمد": 108398,
        "فاطمة اسماعيل": 109914,
        "صفية صابر": 111442,
        "محمد كمال": 112961,
        "جيرمين حسين": 114480,
        "حنان عبد المحي": 116005,
        "رضا السيد": 117534,
        "منال عبد الحميد": 119052,
        "رشا عبد الحافظ": 120583,
        "عفاف حامد": 122111,
        "ايمان حسن": 122350,
        "سيد عبد الهادي": 123874,
        "رانيا ابراهيم": 125402,
        "امل محمد": 126930,
    }

    by_name = {str(row["teacher_name_ar"]): row for row in rows}
    for name, offset in proven_offsets.items():
        if name not in by_name:
            by_name[name] = {
                "teacher_name_ar": name,
                "source_teacher_name_ar": name,
                "offset": offset,
                "confidence": 100,
                "source_kind": "proven_roz_preview",
            }

    blocked_exact = {
        "المحي حنان",
        "حنان عبد",
        "عبد المحي",
        "منال عبد",
        "عبد الحميد",
        "الحافظ رشا",
        "عبد الحافظ",
        "الهادي سيد",
        "عبد الهادي",
        "محمد محمد",
        "مصطفي مصطفي",
        "عبدالله عبدالله",
        "من جداولهم",
        "الانتهاء من جداولهم",
        "المخطط العام للحصص",
        "العام للحصص",
        "عقبة بن نافع",
        "بن نافع الابتدائى",
        "نافع الابتدائى",
        "خيارات الطلا",
    }

    cleaned = [
        row
        for name, row in by_name.items()
        if name not in blocked_exact and not _is_roz_structural_or_school_phrase(name)
    ]

    rows = sorted(cleaned, key=lambda r: int(r.get("offset") or 0))
    return rows[:limit]



def _extract_roz_canonical_subjects(raw_subjects: list[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    preferred_subjects = [
        "قران كريم",
        "تربية دينية اسلامية",
        "لغة عربية",
        "رياضيات",
        "لغة انجليزية",
        "متعدد",
        "التربية الرياضية",
        "دراسات",
        "علوم",
        "تربية فنية مهارات مهنية",
        "العاب ودين",
        "تكنولوجيا",
        "تكنولجيا",
        "توكاتسو",
    ]

    found: dict[str, dict[str, Any]] = {}
    for row in raw_subjects:
        name = str(row.get("subject_name_ar", "")).strip()
        if name == "تربية دينية" and any(
            str(x.get("subject_name_ar", "")).strip() == "تربية دينية اسلامية"
            for x in raw_subjects
        ):
            continue
        if name == "تربية فنية" and any(
            str(x.get("subject_name_ar", "")).strip() == "تربية فنية مهارات مهنية"
            for x in raw_subjects
        ):
            continue
        if name == "مهارات مهنية" and any(
            str(x.get("subject_name_ar", "")).strip() == "تربية فنية مهارات مهنية"
            for x in raw_subjects
        ):
            continue
        if name == "تربية الرياضية" and any(
            str(x.get("subject_name_ar", "")).strip() == "التربية الرياضية"
            for x in raw_subjects
        ):
            continue

        if name and name not in found:
            found[name] = {
                "subject_name_ar": name,
                "offset": row.get("offset"),
                "confidence": row.get("confidence"),
                "source_kind": row.get("source_kind"),
            }

    ordered = []
    for subject in preferred_subjects:
        if subject in found:
            ordered.append(found[subject])

    for subject, row in sorted(found.items()):
        if subject not in {x["subject_name_ar"] for x in ordered}:
            ordered.append(row)

    return ordered[:limit]


def _build_roz_canonical_entities(structured: dict[str, Any]) -> dict[str, Any]:
    raw_teachers = list(structured.get("teachers") or [])
    raw_subjects = list(structured.get("subjects") or [])

    teachers = _extract_roz_canonical_teachers(raw_teachers)
    subjects = _extract_roz_canonical_subjects(raw_subjects)

    return {
        "parser_stage": "canonical_preview_only",
        "safe_to_import": False,
        "teachers_count": len(teachers),
        "subjects_count": len(subjects),
        "teachers": teachers,
        "subjects": subjects,
        "quality_notes_ar": [
            "تم تنظيف الأسماء من البادئات والرموز الثنائية والاختصارات الناقصة قدر الإمكان.",
            "تم تقليل الأسماء المقلوبة أو المكررة بناءً على مجموعة الكلمات ومصدر الإزاحة.",
            "لا يزال الاستيراد الفعلي ممنوعًا حتى يتم إثبات ربط CLASSTT بالأيام والحصص والمدرسين.",
        ],
    }


def _extract_roz_structured_entities(records: list[dict[str, Any]]) -> dict[str, Any]:
    teachers = _extract_roz_teacher_candidates(records)
    subjects = _extract_roz_subject_candidates(records)

    structured = {
        "parser_stage": "structured_preview_only",
        "safe_to_import": False,
        "teachers_count": len(teachers),
        "subjects_count": len(subjects),
        "teachers": teachers,
        "subjects": subjects,
        "notes_ar": [
            "هذه معاينة منظمة فقط ولا تنفذ أي إدخال في قاعدة البيانات.",
            "أسماء المدرسين مستخرجة من نطاقات عربية داخل ملف ROZ بترميز CP1256 مع درجات ثقة.",
            "قبل الاستيراد الفعلي يجب ربط الجداول الثنائية CLASSTT بالخانات/الأيام/الحصص بشكل نهائي.",
        ],
    }
    structured["canonical_entities"] = _build_roz_canonical_entities(structured)
    return structured


def _build_roz_semantic_preview(data: bytes, records: list[dict[str, Any]]) -> dict[str, Any]:
    text_blob = "\n".join(str(row.get("text") or "") for row in records)

    period_labels = sorted(
        {
            _clean_roz_text(value)
            for value in re.findall(r"الحصة\s+[اأإآء-ي]+", text_blob)
            if "\n" not in value
        }
    )

    class_labels = sorted(
        set(re.findall(r"الصف\s+الدراسي\s+\d+", text_blob)),
        key=lambda x: int(re.search(r"\d+", x).group(0)) if re.search(r"\d+", x) else 999,
    )

    marker_windows = []
    for marker in (
        b"ASCTT",
        b"CLASSTT",
        b"teacher_row1",
        b"teacher_row2",
        b"teacher2_row1",
        b"teacher2_row2",
        b"class_row1",
        b"class_row2",
        b"class_row3",
        b"report_header",
        b"Master",
    ):
        marker_windows.extend(_roz_window_text(data, marker, radius=320)[:4])

    return {
        "academic_years": sorted(set(re.findall(r"20\d{2}/20\d{2}", text_blob))),
        "period_labels": period_labels,
        "class_labels": class_labels,
        "class_timetable_blocks": _extract_classtt_blocks(data),
        "marker_windows": marker_windows,
        "meaningful_records": _meaningful_arabic_records(records),
        "structured_entities": _extract_roz_structured_entities(records),
        "interpretation_ar": [
            "تم تأكيد أن الملف يحتوي بنية ASCTT/ROZ ثنائية وليست CSV أو SQLite.",
            "تم العثور على جداول فصول بعلامات CLASSTT/CLASSTT_END.",
            "تم العثور على قوالب صفوف التقرير الخاصة بالفصول والمعلمين.",
            "تم استخراج السنة الدراسية والحصص والصفوف كنصوص قابلة للمراجعة.",
            "هذه المرحلة لا تكفي للاستيراد النهائي؛ لكنها تؤسس خريطة فك الترميز قبل تحويل الجداول إلى Slots.",
        ],
    }

def parse_asctt_roz_bytes(data: bytes, max_records: int = 800) -> dict[str, Any]:
    all_records = _extract_ascii_runs(data) + _extract_cp1256_runs(data) + _extract_pascal_strings(data)

    dedup: dict[tuple[int, str], dict[str, Any]] = {}
    for record in all_records:
        key = (int(record["offset"]), str(record["text"]))
        dedup[key] = record

    records = sorted(dedup.values(), key=lambda row: (row["offset"], row["kind"]))
    interesting = records[: max(50, min(max_records, 5000))]

    text_blob = "\n".join(str(row["text"]) for row in records)

    periods = sorted(set(re.findall(r"الحصة\s+[اأإآء-ي]+", text_blob)))
    classes = sorted(set(re.findall(r"الصف\s+الدراسي\s+\d+", text_blob)))
    class_tt = sorted(set(re.findall(r"CLASSTT\d+/\d+", text_blob)))
    years = sorted(set(re.findall(r"20\d{2}/20\d{2}", text_blob)))

    marker_counts = {
        "ASCTT": data.count(b"ASCTT"),
        "CLASSTT": data.count(b"CLASSTT"),
        "CLASSTT_END": data.count(b"CLASSTT_END"),
        "teacher_row1": data.count(b"teacher_row1"),
        "teacher_row2": data.count(b"teacher_row2"),
        "teacher2_row1": data.count(b"teacher2_row1"),
        "teacher2_row2": data.count(b"teacher2_row2"),
        "class_row1": data.count(b"class_row1"),
        "class_row2": data.count(b"class_row2"),
        "class_row3": data.count(b"class_row3"),
        "report_header": data.count(b"report_header"),
        "Master": data.count(b"Master"),
    }

    arabic_records_count = sum(
        1 for row in records if any("\u0600" <= ch <= "\u06ff" for ch in str(row["text"]))
    )

    return {
        "format": "ASCTT/ROZ",
        "parser_stage": "inspect_only",
        "safe_to_import": False,
        "records_total": len(records),
        "records_returned": len(interesting),
        "arabic_records_count": arabic_records_count,
        "marker_counts": marker_counts,
        "detected": {
            "academic_years": years,
            "periods": periods,
            "classes": classes,
            "class_timetable_markers": class_tt,
        },
        "semantic_preview": _build_roz_semantic_preview(data, records),
        "records": interesting,
        "notes_ar": [
            "هذه المرحلة قراءة وتحليل فقط ولا تقوم بأي إدخال في قاعدة البيانات.",
            "ملف ROZ ثنائي خاص ببرنامج ASCTT وليس ZIP أو SQLite أو XML.",
            "تم استخراج النصوص العربية ومؤشرات جداول الفصول والمعلمين بترميز CP1256.",
            "مرحلة الاستيراد الفعلي تحتاج ربط حقول ROZ النهائية بالفصول والمدرسين والحصص بعد مراجعة هذه المعاينة.",
        ],
    }


@router.post("/import/asctt-roz/inspect")
async def inspect_asctt_roz_file(
    payload: RozInspectPayload,
) -> dict[str, Any]:
    source_path = _safe_import_sample_path(payload.file_path)
    data = source_path.read_bytes()

    parsed = parse_asctt_roz_bytes(data, payload.max_records)
    evidence = analyze_roz_file(source_path, max_records=min(payload.max_records, 300))
    evidence_summary = summarize_for_cli(evidence)

    return {
        "file_name": source_path.name,
        "file_path": str(source_path),
        "file_size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "evidence_summary": evidence_summary,
        "evidence_confidence": evidence_summary.get("confidence"),
        "evidence_safety": evidence_summary.get("safety"),
        **parsed,
    }



class RozEntityImportPayload(BaseModel):
    file_path: str = "import_samples/mmmmmmmmmmm2-2.roz"
    max_records: int = 300
    dry_run: bool = True
    execute_confirm: str | None = None


def _roz_code_token(value: str, fallback: str) -> str:
    ascii_part = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    if ascii_part:
        return ascii_part[:40]
    return fallback


def _roz_entity_code(prefix: str, index: int, name: str) -> str:
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8].upper()
    return f"{prefix}-{index:03d}-{digest}"


async def _existing_teacher_by_name(db: AsyncSession, name: str) -> Any:
    result = await db.execute(
        text("""
            SELECT id, teacher_code, teacher_name_ar
            FROM school.teachers
            WHERE teacher_name_ar = :name
            LIMIT 1
        """),
        {"name": name},
    )
    row = result.first()
    return row._mapping if row else None


async def _existing_subject_by_name(db: AsyncSession, name: str) -> Any:
    result = await db.execute(
        text("""
            SELECT id, subject_code, subject_name_ar
            FROM school.subjects
            WHERE subject_name_ar = :name
            LIMIT 1
        """),
        {"name": name},
    )
    row = result.first()
    return row._mapping if row else None


async def _existing_class_by_name(db: AsyncSession, name: str) -> Any:
    result = await db.execute(
        text("""
            SELECT id, class_code, class_name_ar
            FROM school.school_classes
            WHERE class_name_ar = :name OR class_code = :name
            LIMIT 1
        """),
        {"name": name},
    )
    row = result.first()
    return row._mapping if row else None


async def _insert_roz_teacher(db: AsyncSession, index: int, name: str) -> Any:
    result = await db.execute(
        text("""
            INSERT INTO school.teachers(teacher_code, teacher_name_ar, specialization)
            VALUES (:code, :name, :specialization)
            ON CONFLICT (teacher_code)
            DO UPDATE SET teacher_name_ar = EXCLUDED.teacher_name_ar
            RETURNING id, teacher_code, teacher_name_ar
        """),
        {
            "code": _roz_entity_code("ROZ-T", index, name),
            "name": name,
            "specialization": "ROZ/ASCTT import",
        },
    )
    return result.one()._mapping


async def _insert_roz_subject(db: AsyncSession, index: int, name: str) -> Any:
    result = await db.execute(
        text("""
            INSERT INTO school.subjects(subject_code, subject_name_ar, color_code)
            VALUES (:code, :name, :color_code)
            ON CONFLICT (subject_code)
            DO UPDATE SET subject_name_ar = EXCLUDED.subject_name_ar
            RETURNING id, subject_code, subject_name_ar
        """),
        {
            "code": _roz_entity_code("ROZ-S", index, name),
            "name": name,
            "color_code": "#8b5a2b",
        },
    )
    return result.one()._mapping


async def _insert_roz_class(db: AsyncSession, index: int, name: str) -> Any:
    number_match = re.search(r"\d+", name)
    if number_match:
        code = f"ROZ-CLASS-{int(number_match.group(0)):02d}"
    else:
        code = _roz_entity_code("ROZ-C", index, name)

    result = await db.execute(
        text("""
            INSERT INTO school.school_classes(class_code, class_name_ar, stage_name_ar, grade_name_ar)
            VALUES (:code, :name, :stage_name_ar, :grade_name_ar)
            ON CONFLICT (class_code)
            DO UPDATE SET class_name_ar = EXCLUDED.class_name_ar
            RETURNING id, class_code, class_name_ar
        """),
        {
            "code": code,
            "name": name,
            "stage_name_ar": "مستورد من ROZ",
            "grade_name_ar": name,
        },
    )
    return result.one()._mapping


async def _build_roz_entity_import_plan(
    db: AsyncSession,
    parsed: dict[str, Any],
    *,
    execute: bool,
) -> dict[str, Any]:
    canonical = (
        parsed.get("semantic_preview", {})
        .get("structured_entities", {})
        .get("canonical_entities", {})
    )

    teachers = list(canonical.get("teachers") or [])
    subjects = list(canonical.get("subjects") or [])
    classes = list(parsed.get("semantic_preview", {}).get("class_labels") or [])

    teacher_rows: list[dict[str, Any]] = []
    subject_rows: list[dict[str, Any]] = []
    class_rows: list[dict[str, Any]] = []

    created_teachers = 0
    created_subjects = 0
    created_classes = 0

    for index, row in enumerate(teachers, start=1):
        name = str(row.get("teacher_name_ar") or "").strip()
        if not name:
            continue

        existing = await _existing_teacher_by_name(db, name)
        if existing:
            teacher_rows.append({
                "teacher_name_ar": name,
                "action": "match_existing",
                "id": str(existing["id"]),
                "teacher_code": existing.get("teacher_code"),
            })
            continue

        if execute:
            created = await _insert_roz_teacher(db, index, name)
            created_teachers += 1
            teacher_rows.append({
                "teacher_name_ar": name,
                "action": "created",
                "id": str(created["id"]),
                "teacher_code": created.get("teacher_code"),
            })
        else:
            teacher_rows.append({
                "teacher_name_ar": name,
                "action": "would_create",
                "teacher_code": _roz_entity_code("ROZ-T", index, name),
            })

    for index, row in enumerate(subjects, start=1):
        name = str(row.get("subject_name_ar") or "").strip()
        if not name:
            continue

        existing = await _existing_subject_by_name(db, name)
        if existing:
            subject_rows.append({
                "subject_name_ar": name,
                "action": "match_existing",
                "id": str(existing["id"]),
                "subject_code": existing.get("subject_code"),
            })
            continue

        if execute:
            created = await _insert_roz_subject(db, index, name)
            created_subjects += 1
            subject_rows.append({
                "subject_name_ar": name,
                "action": "created",
                "id": str(created["id"]),
                "subject_code": created.get("subject_code"),
            })
        else:
            subject_rows.append({
                "subject_name_ar": name,
                "action": "would_create",
                "subject_code": _roz_entity_code("ROZ-S", index, name),
            })

    for index, name_value in enumerate(classes, start=1):
        name = str(name_value or "").strip()
        if not name:
            continue

        existing = await _existing_class_by_name(db, name)
        if existing:
            class_rows.append({
                "class_name_ar": name,
                "action": "match_existing",
                "id": str(existing["id"]),
                "class_code": existing.get("class_code"),
            })
            continue

        number_match = re.search(r"\d+", name)
        class_code = f"ROZ-CLASS-{int(number_match.group(0)):02d}" if number_match else _roz_entity_code("ROZ-C", index, name)

        if execute:
            created = await _insert_roz_class(db, index, name)
            created_classes += 1
            class_rows.append({
                "class_name_ar": name,
                "action": "created",
                "id": str(created["id"]),
                "class_code": created.get("class_code"),
            })
        else:
            class_rows.append({
                "class_name_ar": name,
                "action": "would_create",
                "class_code": class_code,
            })

    return {
        "mode": "execute" if execute else "dry_run",
        "safe_to_import_slots": False,
        "teachers": teacher_rows,
        "subjects": subject_rows,
        "classes": class_rows,
        "counts": {
            "teachers_total": len(teacher_rows),
            "subjects_total": len(subject_rows),
            "classes_total": len(class_rows),
            "teachers_created": created_teachers,
            "subjects_created": created_subjects,
            "classes_created": created_classes,
            "teachers_would_create": sum(1 for x in teacher_rows if x["action"] == "would_create"),
            "subjects_would_create": sum(1 for x in subject_rows if x["action"] == "would_create"),
            "classes_would_create": sum(1 for x in class_rows if x["action"] == "would_create"),
            "teachers_existing": sum(1 for x in teacher_rows if x["action"] == "match_existing"),
            "subjects_existing": sum(1 for x in subject_rows if x["action"] == "match_existing"),
            "classes_existing": sum(1 for x in class_rows if x["action"] == "match_existing"),
        },
        "notes_ar": [
            "هذا endpoint يستورد الكيانات فقط: مدرسين ومواد وفصول.",
            "استيراد خانات الجدول timetable_slots ممنوع في هذه المرحلة.",
            "الوضع الافتراضي dry_run ولا يحدث أي كتابة في قاعدة البيانات.",
            "التنفيذ الفعلي يتطلب dry_run=false و execute_confirm=IMPORT_ROZ_ENTITIES_ONLY.",
        ],
    }


@router.post("/import/asctt-roz/entities")
async def import_asctt_roz_entities(
    payload: RozEntityImportPayload,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    source_path = _safe_import_sample_path(payload.file_path)
    data = source_path.read_bytes()
    parsed = parse_asctt_roz_bytes(data, payload.max_records)

    execute = not payload.dry_run
    if execute and payload.execute_confirm != "IMPORT_ROZ_ENTITIES_ONLY":
        raise HTTPException(
            status_code=409,
            detail="تنفيذ استيراد كيانات ROZ يتطلب execute_confirm=IMPORT_ROZ_ENTITIES_ONLY",
        )

    plan = await _build_roz_entity_import_plan(db, parsed, execute=execute)

    if execute:
        await audit_event(
            db,
            "import_roz_entities",
            "school_timetable_roz_entities",
            payload={
                "file_name": source_path.name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "counts": plan["counts"],
            },
        )
        await db.commit()
    else:
        await db.rollback()

    return {
        "file_name": source_path.name,
        "file_size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "dry_run": payload.dry_run,
        "safe_to_import_slots": False,
        **plan,
    }


@router.post("/import/time-table-csv")
async def import_time_table_csv(
    payload: TimetableCsvImport,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    csv_text = payload.csv_text.strip()
    if not csv_text:
        raise HTTPException(status_code=400, detail="CSV فارغ")

    reader = csv.DictReader(io.StringIO(csv_text))
    required = {"day", "period", "class", "subject", "teacher", "room"}
    headers = {h.strip().lower() for h in (reader.fieldnames or [])}

    if not required.issubset(headers):
        raise HTTPException(
            status_code=400,
            detail="CSV لازم يحتوي الأعمدة: day,period,class,subject,teacher,room",
        )

    try:
        batch_result = await db.execute(
            text("""
                INSERT INTO school.timetable_import_batches(batch_name, source_program, source_format)
                VALUES (:batch_name, 'TimeTable', 'csv')
                RETURNING id
            """),
            {"batch_name": payload.batch_name},
        )
        batch_id = batch_result.one()._mapping["id"]

        version_result = await db.execute(text("""
            SELECT id
            FROM school.timetable_versions
            WHERE is_current = true
            ORDER BY created_at DESC
            LIMIT 1
        """))
        version_row = version_result.first()

        if version_row is None:
            new_version = await db.execute(text("""
                INSERT INTO school.timetable_versions(name_ar, status, is_current)
                VALUES ('جدول مستورد من TimeTable', 'draft', true)
                RETURNING id
            """))
            version_id = new_version.one()._mapping["id"]
        else:
            version_id = version_row._mapping["id"]

        total = 0
        accepted = 0
        rejected = 0
        errors: list[dict[str, Any]] = []

        for row in reader:
            total += 1
            clean = {str(k).strip().lower(): (v or "").strip() for k, v in row.items()}

            try:
                day_name = clean["day"]
                period_no = int(clean["period"])
                class_name = clean["class"]
                subject = clean["subject"]
                teacher_name = clean["teacher"]
                room_name = clean["room"]

                day = await db.execute(
                    text("""
                        SELECT id
                        FROM school.week_days
                        WHERE name_ar = :day OR day_code = lower(:day)
                        LIMIT 1
                    """),
                    {"day": day_name},
                )
                day_row = day.first()
                if day_row is None:
                    raise ValueError(f"اليوم غير معروف: {day_name}")

                period = await db.execute(
                    text("SELECT id FROM school.lesson_periods WHERE period_no = :period_no LIMIT 1"),
                    {"period_no": period_no},
                )
                period_row = period.first()
                if period_row is None:
                    raise ValueError(f"الحصة غير موجودة: {period_no}")

                class_id = await get_or_create_class(db, class_name)
                teacher_id = await get_or_create_teacher(db, teacher_name)
                room_id = await get_or_create_room(db, room_name)

                await db.execute(
                    text("""
                        INSERT INTO school.timetable_slots
                        (
                          timetable_version_id,
                          school_class_id,
                          week_day_id,
                          period_id,
                          subject_name_ar,
                          teacher_id,
                          classroom_id
                        )
                        VALUES
                        (:version_id, :class_id, :day_id, :period_id, :subject, :teacher_id, :room_id)
                        ON CONFLICT (timetable_version_id, school_class_id, week_day_id, period_id)
                        DO UPDATE SET
                          subject_name_ar = EXCLUDED.subject_name_ar,
                          teacher_id = EXCLUDED.teacher_id,
                          classroom_id = EXCLUDED.classroom_id
                    """),
                    {
                        "version_id": version_id,
                        "class_id": class_id,
                        "day_id": day_row._mapping["id"],
                        "period_id": period_row._mapping["id"],
                        "subject": subject,
                        "teacher_id": teacher_id,
                        "room_id": room_id,
                    },
                )
                accepted += 1

            except Exception as exc:
                rejected += 1
                errors.append(
                    {
                        "row_number": total,
                        "row_data": clean,
                        "error_message": str(exc),
                    }
                )
                await db.execute(
                    text("""
                        INSERT INTO school.timetable_import_errors(batch_id, row_number, row_data, error_message)
                        VALUES (:batch_id, :row_number, CAST(:row_data AS jsonb), :error_message)
                    """),
                    {
                        "batch_id": batch_id,
                        "row_number": total,
                        "row_data": json.dumps(clean, ensure_ascii=False),
                        "error_message": str(exc),
                    },
                )

        await db.execute(
            text("""
                UPDATE school.timetable_import_batches
                SET total_rows = :total,
                    accepted_rows = :accepted,
                    rejected_rows = :rejected
                WHERE id = :batch_id
            """),
            {
                "total": total,
                "accepted": accepted,
                "rejected": rejected,
                "batch_id": batch_id,
            },
        )

        await audit_event(
            db,
            "import_time_table_csv",
            "school_timetable_import_batch",
            str(batch_id),
            {
                "batch_name": payload.batch_name,
                "total_rows": total,
                "accepted_rows": accepted,
                "rejected_rows": rejected,
            },
        )
        await db.commit()

        return {
            "batch_id": str(batch_id),
            "total_rows": total,
            "accepted_rows": accepted,
            "rejected_rows": rejected,
            "errors": errors[:20],
        }

    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"فشل استيراد TimeTable: {exc}") from exc


class SmokeCleanupPayload(BaseModel):
    confirm: str
    dry_run: bool = True
    execute_confirm: str | None = None


SMOKE_MARKERS = [
    "SMOKE",
    "PH3E",
    "PH4B",
    "PH5",
    "Phase3",
    "Phase4",
    "Phase5",
    "اختبار",
    "تثبيت",
    "Guard",
]


def smoke_like_sql(*columns: str) -> str:
    parts: list[str] = []
    for column in columns:
        for index, _marker in enumerate(SMOKE_MARKERS):
            parts.append(f"COALESCE({column}, '') ILIKE :marker_{index}")
    return " OR ".join(parts) if parts else "false"


def smoke_marker_params() -> dict[str, str]:
    return {f"marker_{index}": f"%{marker}%" for index, marker in enumerate(SMOKE_MARKERS)}


@router.post("/admin/cleanup-smoke-data")
async def cleanup_smoke_data(
    payload: SmokeCleanupPayload,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if payload.confirm != "DELETE_SMOKE_DATA":
        raise HTTPException(
            status_code=400,
            detail="عملية تنظيف بيانات الاختبار تتطلب confirm=DELETE_SMOKE_DATA",
        )

    params = smoke_marker_params()

    version_where = smoke_like_sql("name_ar", "status")
    version_join_where = smoke_like_sql("tv.name_ar", "tv.status")
    teacher_where = smoke_like_sql("teacher_code", "teacher_name_ar", "specialization")
    subject_where = smoke_like_sql("subject_code", "subject_name_ar")
    class_where = smoke_like_sql("class_code", "class_name_ar", "stage_name_ar", "grade_name_ar")
    classroom_where = smoke_like_sql("room_code", "room_name_ar", "name_ar", "floor_name")
    constraint_where = smoke_like_sql("rule_code", "target_scope", "constraint_type")
    slot_where = smoke_like_sql("subject_name_ar", "notes")

    counts: dict[str, int] = {}

    async def count_query(name: str, sql: str) -> None:
        result = await db.execute(text(sql), params)
        counts[name] = int(result.scalar_one())

    await count_query("teachers", f"SELECT count(*) FROM school.teachers WHERE {teacher_where}")
    await count_query("subjects", f"SELECT count(*) FROM school.subjects WHERE {subject_where}")
    await count_query("classes", f"SELECT count(*) FROM school.school_classes WHERE {class_where}")
    await count_query("classrooms", f"SELECT count(*) FROM school.classrooms WHERE {classroom_where}")
    await count_query("constraints", f"SELECT count(*) FROM school.timetable_constraints WHERE {constraint_where}")
    await count_query("versions", f"SELECT count(*) FROM school.timetable_versions WHERE {version_where}")
    await count_query("slots_by_content", f"SELECT count(*) FROM school.timetable_slots WHERE {slot_where}")
    await count_query("slots_by_version", f"""
        SELECT count(*)
        FROM school.timetable_slots slot
        JOIN school.timetable_versions tv ON tv.id = slot.timetable_version_id
        WHERE {version_join_where}
    """)
    await count_query("generation_runs_by_version", f"""
        SELECT count(*)
        FROM school.timetable_generation_runs run
        JOIN school.timetable_versions tv ON tv.id = run.timetable_version_id
        WHERE {version_join_where}
    """)
    await count_query("export_jobs_by_version", f"""
        SELECT count(*)
        FROM school.timetable_export_jobs job
        JOIN school.timetable_versions tv ON tv.id = job.timetable_version_id
        WHERE {version_join_where}
    """)

    previews: dict[str, list[dict[str, Any]]] = {}

    async def preview_query(name: str, sql: str) -> None:
        result = await db.execute(text(sql), params)
        previews[name] = json_safe([dict(row._mapping) for row in result])

    await preview_query("teachers", f"""
        SELECT
          id::text,
          teacher_code AS code,
          teacher_name_ar AS name,
          specialization AS extra,
          created_at
        FROM school.teachers
        WHERE {teacher_where}
        ORDER BY created_at DESC NULLS LAST
        LIMIT 20
    """)

    await preview_query("subjects", f"""
        SELECT
          id::text,
          subject_code AS code,
          subject_name_ar AS name,
          color_code AS extra,
          created_at
        FROM school.subjects
        WHERE {subject_where}
        ORDER BY created_at DESC NULLS LAST
        LIMIT 20
    """)

    await preview_query("classes", f"""
        SELECT
          id::text,
          class_code AS code,
          class_name_ar AS name,
          concat_ws(' / ', stage_name_ar, grade_name_ar) AS extra,
          created_at
        FROM school.school_classes
        WHERE {class_where}
        ORDER BY created_at DESC NULLS LAST
        LIMIT 20
    """)

    await preview_query("classrooms", f"""
        SELECT
          id::text,
          COALESCE(room_code, code) AS code,
          COALESCE(room_name_ar, name_ar) AS name,
          floor_name AS extra,
          created_at
        FROM school.classrooms
        WHERE {classroom_where}
        ORDER BY created_at DESC NULLS LAST
        LIMIT 20
    """)

    await preview_query("constraints", f"""
        SELECT
          id::text,
          rule_code AS code,
          constraint_type AS name,
          target_scope AS extra,
          created_at
        FROM school.timetable_constraints
        WHERE {constraint_where}
        ORDER BY created_at DESC NULLS LAST
        LIMIT 20
    """)

    await preview_query("versions", f"""
        SELECT
          id::text,
          status AS code,
          name_ar AS name,
          is_current::text AS extra,
          created_at
        FROM school.timetable_versions
        WHERE {version_where}
        ORDER BY created_at DESC NULLS LAST
        LIMIT 30
    """)

    await preview_query("slots_by_content", f"""
        SELECT
          slot.id::text,
          tv.name_ar AS code,
          slot.subject_name_ar AS name,
          slot.notes AS extra,
          slot.created_at
        FROM school.timetable_slots slot
        LEFT JOIN school.timetable_versions tv ON tv.id = slot.timetable_version_id
        WHERE {slot_where}
        ORDER BY slot.created_at DESC NULLS LAST
        LIMIT 30
    """)

    await preview_query("slots_by_version", f"""
        SELECT
          slot.id::text,
          tv.name_ar AS code,
          slot.subject_name_ar AS name,
          slot.notes AS extra,
          slot.created_at
        FROM school.timetable_slots slot
        JOIN school.timetable_versions tv ON tv.id = slot.timetable_version_id
        WHERE {version_join_where}
        ORDER BY slot.created_at DESC NULLS LAST
        LIMIT 30
    """)

    await preview_query("generation_runs_by_version", f"""
        SELECT
          run.id::text,
          tv.name_ar AS code,
          run.status AS name,
          concat('scheduled=', run.scheduled_lessons, ', conflicts=', run.conflict_count) AS extra,
          run.started_at AS created_at
        FROM school.timetable_generation_runs run
        JOIN school.timetable_versions tv ON tv.id = run.timetable_version_id
        WHERE {version_join_where}
        ORDER BY run.started_at DESC NULLS LAST
        LIMIT 20
    """)

    await preview_query("export_jobs_by_version", f"""
        SELECT
          job.id::text,
          tv.name_ar AS code,
          job.export_type AS name,
          job.report_scope AS extra,
          job.created_at
        FROM school.timetable_export_jobs job
        JOIN school.timetable_versions tv ON tv.id = job.timetable_version_id
        WHERE {version_join_where}
        ORDER BY job.created_at DESC NULLS LAST
        LIMIT 20
    """)

    if not payload.dry_run:
        if payload.execute_confirm != "EXECUTE_DELETE_SMOKE_DATA":
            raise HTTPException(
                status_code=409,
                detail="تنفيذ حذف بيانات الاختبار يتطلب execute_confirm=EXECUTE_DELETE_SMOKE_DATA بالإضافة إلى confirm=DELETE_SMOKE_DATA",
            )

        deleted_counts: dict[str, int] = {}

        async def delete_query(name: str, sql: str) -> None:
            result = await db.execute(text(sql), params)
            deleted_counts[name] = int(result.scalar_one())

        await delete_query("export_jobs_by_version", f"""
            DELETE FROM school.timetable_export_jobs job
            USING school.timetable_versions tv
            WHERE tv.id = job.timetable_version_id
              AND ({version_join_where})
            RETURNING job.id
        """)

        await delete_query("generation_runs_by_version", f"""
            DELETE FROM school.timetable_generation_runs run
            USING school.timetable_versions tv
            WHERE tv.id = run.timetable_version_id
              AND ({version_join_where})
            RETURNING run.id
        """)

        await delete_query("slots", f"""
            WITH smoke_teachers AS (
                SELECT id FROM school.teachers WHERE {teacher_where}
            ),
            smoke_classes AS (
                SELECT id FROM school.school_classes WHERE {class_where}
            ),
            smoke_classrooms AS (
                SELECT id FROM school.classrooms WHERE {classroom_where}
            ),
            smoke_versions AS (
                SELECT id FROM school.timetable_versions WHERE {version_where}
            ),
            candidates AS (
                SELECT DISTINCT slot.id
                FROM school.timetable_slots slot
                WHERE slot.timetable_version_id IN (SELECT id FROM smoke_versions)
                   OR slot.teacher_id IN (SELECT id FROM smoke_teachers)
                   OR slot.school_class_id IN (SELECT id FROM smoke_classes)
                   OR slot.classroom_id IN (SELECT id FROM smoke_classrooms)
                   OR ({slot_where})
            )
            DELETE FROM school.timetable_slots slot
            USING candidates
            WHERE slot.id = candidates.id
            RETURNING slot.id
        """)

        await delete_query("curriculum_plans", f"""
            WITH smoke_teachers AS (
                SELECT id FROM school.teachers WHERE {teacher_where}
            ),
            smoke_subjects AS (
                SELECT id FROM school.subjects WHERE {subject_where}
            ),
            smoke_classes AS (
                SELECT id FROM school.school_classes WHERE {class_where}
            ),
            smoke_classrooms AS (
                SELECT id FROM school.classrooms WHERE {classroom_where}
            ),
            candidates AS (
                SELECT DISTINCT cp.id
                FROM school.curriculum_plans cp
                WHERE cp.teacher_id IN (SELECT id FROM smoke_teachers)
                   OR cp.subject_id IN (SELECT id FROM smoke_subjects)
                   OR cp.school_class_id IN (SELECT id FROM smoke_classes)
                   OR cp.classroom_id IN (SELECT id FROM smoke_classrooms)
            )
            DELETE FROM school.curriculum_plans cp
            USING candidates
            WHERE cp.id = candidates.id
            RETURNING cp.id
        """)

        await delete_query("constraints", f"""
            DELETE FROM school.timetable_constraints tc
            WHERE {constraint_where}
            RETURNING tc.id
        """)

        await delete_query("versions", f"""
            DELETE FROM school.timetable_versions tv
            WHERE {version_where}
            RETURNING tv.id
        """)

        await delete_query("subjects", f"""
            DELETE FROM school.subjects s
            WHERE {subject_where}
            RETURNING s.id
        """)

        await delete_query("teachers", f"""
            DELETE FROM school.teachers t
            WHERE {teacher_where}
            RETURNING t.id
        """)

        await delete_query("classes", f"""
            DELETE FROM school.school_classes cls
            WHERE {class_where}
            RETURNING cls.id
        """)

        await delete_query("classrooms", f"""
            DELETE FROM school.classrooms room
            WHERE {classroom_where}
            RETURNING room.id
        """)

        await db.commit()

        return {
            "dry_run": False,
            "deleted": True,
            "counts_before": counts,
            "deleted_counts": deleted_counts,
            "preview_before": previews,
            "markers": SMOKE_MARKERS,
        }

    return {
        "dry_run": True,
        "deleted": False,
        "counts": counts,
        "preview": previews,
        "markers": SMOKE_MARKERS,
    }



@router.get("/teachers")
async def list_teachers(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT id, teacher_code, teacher_name_ar, phone, specialization, is_active, created_at
        FROM school.teachers
        ORDER BY teacher_name_ar
    """))
    return rows(result)


class TeacherPayload(BaseModel):
    teacher_code: str | None = None
    teacher_name_ar: str
    phone: str | None = None
    specialization: str | None = None


@router.post("/teachers")
async def create_teacher(payload: TeacherPayload, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(text("""
        INSERT INTO school.teachers(teacher_code, teacher_name_ar, phone, specialization)
        VALUES (:teacher_code, :teacher_name_ar, :phone, :specialization)
        RETURNING id, teacher_code, teacher_name_ar, phone, specialization, is_active, created_at
    """), payload.model_dump())
    await db.commit()
    return dict(result.one()._mapping)


@router.get("/subjects")
async def list_subjects(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT id, subject_code, subject_name_ar, color_code, is_active, created_at
        FROM school.subjects
        ORDER BY subject_name_ar
    """))
    return rows(result)


class SubjectPayload(BaseModel):
    subject_code: str | None = None
    subject_name_ar: str
    color_code: str | None = None


@router.post("/subjects")
async def create_subject(payload: SubjectPayload, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(text("""
        INSERT INTO school.subjects(subject_code, subject_name_ar, color_code)
        VALUES (:subject_code, :subject_name_ar, :color_code)
        ON CONFLICT (subject_code)
        DO UPDATE SET
          subject_name_ar = EXCLUDED.subject_name_ar,
          color_code = EXCLUDED.color_code,
          is_active = true
        RETURNING id, subject_code, subject_name_ar, color_code, is_active, created_at
    """), payload.model_dump())
    row = dict(result.one()._mapping)
    await audit_event(db, "create_subject", "school_timetable_subject", str(row["id"]), row)
    await db.commit()
    return row


@router.get("/classes")
async def list_classes(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT id, class_code, class_name_ar, stage_name_ar, grade_name_ar, capacity, is_active, created_at
        FROM school.school_classes
        ORDER BY class_code
    """))
    return rows(result)


class ClassPayload(BaseModel):
    class_code: str
    class_name_ar: str
    stage_name_ar: str | None = None
    grade_name_ar: str | None = None
    capacity: int = 0


@router.post("/classes")
async def create_class(payload: ClassPayload, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(text("""
        INSERT INTO school.school_classes(class_code, class_name_ar, stage_name_ar, grade_name_ar, capacity)
        VALUES (:class_code, :class_name_ar, :stage_name_ar, :grade_name_ar, :capacity)
        RETURNING id, class_code, class_name_ar, stage_name_ar, grade_name_ar, capacity, is_active, created_at
    """), payload.model_dump())
    await db.commit()
    return dict(result.one()._mapping)


@router.get("/curriculum-plans")
async def list_curriculum_plans(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT
          cp.id,
          cp.weekly_lessons,
          cp.priority,
          cp.is_active,
          cls.class_code,
          cls.class_name_ar,
          s.subject_code,
          s.subject_name_ar,
          t.teacher_name_ar,
          room.room_name_ar
        FROM school.curriculum_plans cp
        JOIN school.school_classes cls ON cls.id = cp.school_class_id
        JOIN school.subjects s ON s.id = cp.subject_id
        LEFT JOIN school.teachers t ON t.id = cp.teacher_id
        LEFT JOIN school.classrooms room ON room.id = cp.classroom_id
        ORDER BY cls.class_code, cp.priority, s.subject_name_ar
    """))
    return rows(result)


class CurriculumPlanPayload(BaseModel):
    school_class_id: str
    subject_id: str
    teacher_id: str | None = None
    classroom_id: str | None = None
    weekly_lessons: int = 1
    priority: int = 100


@router.post("/curriculum-plans")
async def create_curriculum_plan(
    payload: CurriculumPlanPayload,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if payload.weekly_lessons < 1:
        raise HTTPException(status_code=400, detail="عدد الحصص الأسبوعية يجب أن يكون أكبر من صفر")

    result = await db.execute(text("""
        INSERT INTO school.curriculum_plans(
          school_class_id,
          subject_id,
          teacher_id,
          classroom_id,
          weekly_lessons,
          priority
        )
        VALUES (
          CAST(:school_class_id AS uuid),
          CAST(:subject_id AS uuid),
          CAST(:teacher_id AS uuid),
          CAST(:classroom_id AS uuid),
          :weekly_lessons,
          :priority
        )
        ON CONFLICT (school_class_id, subject_id)
        DO UPDATE SET
          teacher_id = EXCLUDED.teacher_id,
          classroom_id = EXCLUDED.classroom_id,
          weekly_lessons = EXCLUDED.weekly_lessons,
          priority = EXCLUDED.priority,
          is_active = true
        RETURNING *
    """), payload.model_dump())
    row = dict(result.one()._mapping)
    await audit_event(db, "upsert_curriculum_plan", "school_timetable_curriculum_plan", str(row["id"]), row)
    await db.commit()
    return row


@router.post("/curriculum-plans/bulk")
async def bulk_curriculum_plans(
    payload: list[CurriculumPlanPayload],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    saved = 0
    for item in payload:
        await create_curriculum_plan(item, db)
        saved += 1
    return {"saved": saved}


@router.get("/constraints")
async def list_constraints(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT id, constraint_type, target_scope, target_id, rule_code, rule_payload, weight, is_active, created_at
        FROM school.timetable_constraints
        ORDER BY constraint_type, target_scope, rule_code
    """))
    return rows(result)


class ConstraintPayload(BaseModel):
    constraint_type: str
    target_scope: str
    target_id: str | None = None
    rule_code: str
    rule_payload: dict[str, Any] = Field(default_factory=dict)
    weight: int = 10


@router.post("/constraints")
async def create_constraint(payload: ConstraintPayload, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    if payload.constraint_type not in {"hard", "soft"}:
        raise HTTPException(status_code=400, detail="constraint_type يجب أن يكون hard أو soft")

    result = await db.execute(text("""
        INSERT INTO school.timetable_constraints(
          constraint_type,
          target_scope,
          target_id,
          rule_code,
          rule_payload,
          weight
        )
        VALUES (
          :constraint_type,
          :target_scope,
          CAST(:target_id AS uuid),
          :rule_code,
          CAST(:rule_payload AS jsonb),
          :weight
        )
        RETURNING id, constraint_type, target_scope, target_id, rule_code, rule_payload, weight, is_active, created_at
    """), {
        **payload.model_dump(exclude={"rule_payload"}),
        "rule_payload": json.dumps(payload.rule_payload, ensure_ascii=False),
    })
    row = dict(result.one()._mapping)
    await audit_event(db, "create_constraint", "school_timetable_constraint", str(row["id"]), row)
    await db.commit()
    return row


@router.get("/classrooms")
async def list_classrooms(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT id, room_code, room_name_ar, name_ar, capacity, floor_name, is_active, created_at
        FROM school.classrooms
        ORDER BY room_code NULLS LAST, room_name_ar NULLS LAST, name_ar NULLS LAST
    """))
    return rows(result)


class ClassroomPayload(BaseModel):
    room_code: str
    room_name_ar: str
    capacity: int = 0
    floor_name: str | None = None


@router.post("/classrooms")
async def create_classroom(payload: ClassroomPayload, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(text("""
        INSERT INTO school.classrooms(room_code, room_name_ar, name_ar, capacity, floor_name)
        VALUES (:room_code, :room_name_ar, :room_name_ar, :capacity, :floor_name)
        RETURNING id, room_code, room_name_ar, name_ar, capacity, floor_name, is_active, created_at
    """), payload.model_dump())
    await db.commit()
    return dict(result.one()._mapping)


@router.get("/periods")
async def list_periods(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT id, period_no, name_ar, starts_at, ends_at, is_break, is_active, created_at
        FROM school.lesson_periods
        ORDER BY period_no
    """))
    return rows(result)


class PeriodPayload(BaseModel):
    period_no: int
    name_ar: str
    starts_at: str
    ends_at: str
    is_break: bool = False


@router.post("/periods")
async def create_period(payload: PeriodPayload, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(text("""
        INSERT INTO school.lesson_periods(period_no, name_ar, starts_at, ends_at, is_break)
        VALUES (:period_no, :name_ar, CAST(:starts_at AS time), CAST(:ends_at AS time), :is_break)
        ON CONFLICT (period_no)
        DO UPDATE SET
          name_ar = EXCLUDED.name_ar,
          starts_at = EXCLUDED.starts_at,
          ends_at = EXCLUDED.ends_at,
          is_break = EXCLUDED.is_break
        RETURNING id, period_no, name_ar, starts_at, ends_at, is_break, is_active, created_at
    """), payload.model_dump())
    await db.commit()
    return dict(result.one()._mapping)


@router.get("/versions")
async def list_versions(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT id, name_ar, status, effective_from, effective_to, is_current, created_at
        FROM school.timetable_versions
        ORDER BY created_at DESC
    """))
    return rows(result)


class VersionPayload(BaseModel):
    name_ar: str
    is_current: bool = True


class ExportCsvPayload(BaseModel):
    version_id: str | None = None




@router.get("/versions/compare")
async def compare_versions(
    base_version_id: str,
    target_version_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if base_version_id == target_version_id:
        raise HTTPException(status_code=400, detail="اختر نسختين مختلفتين للمقارنة")

    versions_result = await db.execute(text("""
        SELECT id, name_ar, status, is_current, created_at
        FROM school.timetable_versions
        WHERE id IN (CAST(:base_version_id AS uuid), CAST(:target_version_id AS uuid))
    """), {
        "base_version_id": base_version_id,
        "target_version_id": target_version_id,
    })
    versions = {str(row._mapping["id"]): dict(row._mapping) for row in versions_result}

    if base_version_id not in versions:
        raise HTTPException(status_code=404, detail="نسخة الأساس غير موجودة")
    if target_version_id not in versions:
        raise HTTPException(status_code=404, detail="نسخة المقارنة غير موجودة")

    rows_result = await db.execute(text("""
        SELECT
            timetable_version_id,
            id,
            class_code,
            class_name_ar,
            week_day_id,
            day_name_ar,
            day_order,
            period_no,
            period_name_ar,
            subject_name_ar,
            teacher_name_ar,
            room_name_ar,
            notes
        FROM school.vw_school_timetable_grid
        WHERE timetable_version_id IN (CAST(:base_version_id AS uuid), CAST(:target_version_id AS uuid))
        ORDER BY day_order, period_no, class_code, subject_name_ar
    """), {
        "base_version_id": base_version_id,
        "target_version_id": target_version_id,
    })

    base_map: dict[str, dict[str, Any]] = {}
    target_map: dict[str, dict[str, Any]] = {}

    def signature(row: dict[str, Any]) -> str:
        return "|".join([
            str(row.get("class_code") or ""),
            str(row.get("week_day_id") or ""),
            str(row.get("period_no") or ""),
        ])

    for row_obj in rows_result:
        row = dict(row_obj._mapping)
        key = signature(row)
        if str(row["timetable_version_id"]) == base_version_id:
            base_map[key] = row
        else:
            target_map[key] = row

    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []

    all_keys = sorted(set(base_map) | set(target_map))

    for key in all_keys:
        base = base_map.get(key)
        target = target_map.get(key)

        if base is None and target is not None:
            added.append(target)
            continue

        if target is None and base is not None:
            removed.append(base)
            continue

        if base is None or target is None:
            continue

        field_changes: dict[str, dict[str, Any]] = {}
        for field in ["subject_name_ar", "teacher_name_ar", "room_name_ar", "notes"]:
            if (base.get(field) or "") != (target.get(field) or ""):
                field_changes[field] = {
                    "from": base.get(field),
                    "to": target.get(field),
                }

        if field_changes:
            changed.append({
                "slot_key": key,
                "base": base,
                "target": target,
                "changes": field_changes,
            })
        else:
            unchanged.append(target)

    summary = {
        "base_slots": len(base_map),
        "target_slots": len(target_map),
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "unchanged_count": len(unchanged),
        "delta_count": len(added) + len(removed) + len(changed),
    }

    result = {
        "base_version": json_safe(versions[base_version_id]),
        "target_version": json_safe(versions[target_version_id]),
        "summary": summary,
        "added": json_safe(added),
        "removed": json_safe(removed),
        "changed": json_safe(changed),
        "unchanged": json_safe(unchanged[:200]),
    }

    await audit_event(
        db,
        "compare_versions",
        "school_timetable_version_compare",
        target_version_id,
        {
            "base_version_id": base_version_id,
            "target_version_id": target_version_id,
            "summary": summary,
        },
    )
    await db.commit()
    return result


@router.post("/versions")
async def create_version(payload: VersionPayload, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    if payload.is_current:
        await db.execute(text("UPDATE school.timetable_versions SET is_current = false"))

    result = await db.execute(text("""
        INSERT INTO school.timetable_versions(name_ar, status, is_current)
        VALUES (:name_ar, 'draft', :is_current)
        RETURNING id, name_ar, status, effective_from, effective_to, is_current, created_at
    """), payload.model_dump())
    row = dict(result.one()._mapping)
    await audit_event(db, "create_version", "school_timetable_version", str(row["id"]), row)
    await db.commit()
    return row


@router.get("/runs")
async def list_generation_runs(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT
          run.id,
          run.status,
          run.total_cards,
          run.scheduled_lessons,
          run.conflict_count,
          run.quality_score,
          run.summary_json,
          run.started_at,
          run.finished_at,
          tv.name_ar AS timetable_name_ar
        FROM school.timetable_generation_runs run
        LEFT JOIN school.timetable_versions tv ON tv.id = run.timetable_version_id
        ORDER BY run.started_at DESC
        LIMIT 50
    """))
    return rows(result)


class GenerationRunPayload(BaseModel):
    name_ar: str = "توليد آلي من Curriculum Matrix"
    clear_existing: bool = True
    make_current: bool = True


async def current_or_new_version(db: AsyncSession, name_ar: str, make_current: bool = True) -> str:
    if make_current:
        await db.execute(text("UPDATE school.timetable_versions SET is_current = false"))

    result = await db.execute(text("""
        INSERT INTO school.timetable_versions(name_ar, status, is_current)
        VALUES (:name_ar, 'generation', :make_current)
        RETURNING id
    """), {"name_ar": name_ar, "make_current": make_current})
    return str(result.one()._mapping["id"])


async def slot_is_free(
    db: AsyncSession,
    version_id: str,
    class_id: str,
    day_id: int,
    period_id: str,
    teacher_id: str | None,
    classroom_id: str | None,
) -> bool:
    result = await db.execute(text("""
        SELECT id
        FROM school.timetable_slots
        WHERE timetable_version_id = CAST(:version_id AS uuid)
          AND week_day_id = :day_id
          AND period_id = CAST(:period_id AS uuid)
          AND (
            school_class_id = CAST(:class_id AS uuid)
            OR (CAST(:teacher_id AS uuid) IS NOT NULL AND teacher_id = CAST(:teacher_id AS uuid))
            OR (CAST(:classroom_id AS uuid) IS NOT NULL AND classroom_id = CAST(:classroom_id AS uuid))
          )
        LIMIT 1
    """), {
        "version_id": version_id,
        "class_id": class_id,
        "day_id": day_id,
        "period_id": period_id,
        "teacher_id": teacher_id,
        "classroom_id": classroom_id,
    })
    return result.first() is None


@router.post("/runs")
async def run_generation(
    payload: GenerationRunPayload,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    days = rows(await db.execute(text("""
        SELECT id, name_ar, sort_order
        FROM school.week_days
        ORDER BY sort_order
    """)))
    periods = rows(await db.execute(text("""
        SELECT id, period_no, name_ar
        FROM school.lesson_periods
        WHERE is_active = true AND is_break = false
        ORDER BY period_no
    """)))
    plans = rows(await db.execute(text("""
        SELECT
          cp.id,
          cp.school_class_id,
          cp.teacher_id,
          cp.classroom_id,
          cp.weekly_lessons,
          cp.priority,
          s.subject_name_ar
        FROM school.curriculum_plans cp
        JOIN school.subjects s ON s.id = cp.subject_id
        WHERE cp.is_active = true
        ORDER BY cp.priority, cp.weekly_lessons DESC, s.subject_name_ar
    """)))

    if not days or not periods:
        raise HTTPException(status_code=409, detail="لا يمكن التوليد قبل إعداد الأيام والحصص")
    if not plans:
        raise HTTPException(status_code=409, detail="لا يمكن التوليد قبل إدخال Curriculum Matrix")

    version_id = await current_or_new_version(db, payload.name_ar, payload.make_current)
    if payload.clear_existing:
        await db.execute(
            text("DELETE FROM school.timetable_slots WHERE timetable_version_id = CAST(:version_id AS uuid)"),
            {"version_id": version_id},
        )

    run_result = await db.execute(text("""
        INSERT INTO school.timetable_generation_runs(timetable_version_id, status)
        VALUES (CAST(:version_id AS uuid), 'running')
        RETURNING id
    """), {"version_id": version_id})
    run_id = str(run_result.one()._mapping["id"])

    total_cards = 0
    scheduled = 0
    generation_conflicts: list[dict[str, Any]] = []

    for plan in plans:
        for lesson_index in range(int(plan["weekly_lessons"])):
            total_cards += 1
            best_slot: dict[str, Any] | None = None
            best_score = -1

            for day in days:
                for period in periods:
                    free = await slot_is_free(
                        db,
                        version_id,
                        str(plan["school_class_id"]),
                        day["id"],
                        str(period["id"]),
                        str(plan["teacher_id"]) if plan["teacher_id"] else None,
                        str(plan["classroom_id"]) if plan["classroom_id"] else None,
                    )
                    if not free:
                        continue

                    class_daily = await db.execute(text("""
                        SELECT count(*)
                        FROM school.timetable_slots
                        WHERE timetable_version_id = CAST(:version_id AS uuid)
                          AND school_class_id = CAST(:class_id AS uuid)
                          AND week_day_id = :day_id
                    """), {
                        "version_id": version_id,
                        "class_id": str(plan["school_class_id"]),
                        "day_id": day["id"],
                    })
                    daily_count = int(class_daily.scalar_one())
                    score = 100 - (daily_count * 8) - (abs(int(period["period_no"]) - 3) * 2)
                    if score > best_score:
                        best_score = score
                        best_slot = {"day": day, "period": period}

            if best_slot is None:
                generation_conflicts.append({
                    "plan_id": str(plan["id"]),
                    "subject_name_ar": plan["subject_name_ar"],
                    "lesson_index": lesson_index + 1,
                    "code": "NO_VALID_SLOT_FOUND",
                    "message_ar": "لا توجد خانة متاحة تحقق القيود الصارمة",
                })
                continue

            await db.execute(text("""
                INSERT INTO school.timetable_slots(
                  timetable_version_id,
                  school_class_id,
                  week_day_id,
                  period_id,
                  subject_name_ar,
                  teacher_id,
                  classroom_id,
                  notes
                )
                VALUES (
                  CAST(:version_id AS uuid),
                  CAST(:school_class_id AS uuid),
                  :week_day_id,
                  CAST(:period_id AS uuid),
                  :subject_name_ar,
                  CAST(:teacher_id AS uuid),
                  CAST(:classroom_id AS uuid),
                  'تم توليدها آليًا من Curriculum Matrix'
                )
            """), {
                "version_id": version_id,
                "school_class_id": str(plan["school_class_id"]),
                "week_day_id": best_slot["day"]["id"],
                "period_id": str(best_slot["period"]["id"]),
                "subject_name_ar": plan["subject_name_ar"],
                "teacher_id": str(plan["teacher_id"]) if plan["teacher_id"] else None,
                "classroom_id": str(plan["classroom_id"]) if plan["classroom_id"] else None,
            })
            scheduled += 1

    quality_result = await db.execute(text("""
        SELECT quality_score
        FROM school.vw_school_timetable_quality
        WHERE timetable_version_id = CAST(:version_id AS uuid)
        LIMIT 1
    """), {"version_id": version_id})
    quality_row = quality_result.first()
    quality_score = float(quality_row._mapping["quality_score"]) if quality_row else 0
    status = "done" if not generation_conflicts else "partial"
    summary_json = {
        "algorithm": "Greedy Generator V1",
        "hard_constraints": ["class_slot_unique", "teacher_slot_unique", "room_slot_unique"],
        "soft_scoring": ["class_daily_balance", "middle_period_preference"],
        "conflicts": generation_conflicts[:50],
    }

    await db.execute(text("""
        UPDATE school.timetable_generation_runs
        SET status = :status,
            total_cards = :total_cards,
            scheduled_lessons = :scheduled,
            conflict_count = :conflict_count,
            quality_score = :quality_score,
            summary_json = CAST(:summary_json AS jsonb),
            finished_at = now()
        WHERE id = CAST(:run_id AS uuid)
    """), {
        "status": status,
        "total_cards": total_cards,
        "scheduled": scheduled,
        "conflict_count": len(generation_conflicts),
        "quality_score": quality_score,
        "summary_json": json.dumps(summary_json, ensure_ascii=False),
        "run_id": run_id,
    })

    await audit_event(db, "run_generation", "school_timetable_generation_run", run_id, summary_json)
    await db.commit()
    return {
        "run_id": run_id,
        "version_id": version_id,
        "status": status,
        "total_cards": total_cards,
        "scheduled_lessons": scheduled,
        "conflict_count": len(generation_conflicts),
        "quality_score": quality_score,
        "conflicts": generation_conflicts[:50],
    }


@router.post("/versions/{version_id}/approve")
async def approve_version(version_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    version_result = await db.execute(
        text("""
            SELECT
                tv.id,
                tv.name_ar,
                tv.status,
                tv.effective_from,
                tv.effective_to,
                tv.is_current,
                tv.created_at,
                count(ts.id) AS slots_count
            FROM school.timetable_versions tv
            LEFT JOIN school.timetable_slots ts ON ts.timetable_version_id = tv.id
            WHERE tv.id = CAST(:version_id AS uuid)
            GROUP BY tv.id, tv.name_ar, tv.status, tv.effective_from, tv.effective_to, tv.is_current, tv.created_at
        """),
        {"version_id": version_id},
    )
    version_row = version_result.first()
    if version_row is None:
        raise HTTPException(status_code=404, detail="نسخة الجدول غير موجودة")

    version_data = dict(version_row._mapping)
    if int(version_data["slots_count"]) < 1:
        raise HTTPException(status_code=409, detail="لا يمكن اعتماد نسخة جدول فارغة بدون حصص")

    conflicts_result = await db.execute(
        text("""
            SELECT count(*)
            FROM school.vw_school_timetable_conflicts
            WHERE timetable_version_id = CAST(:version_id AS uuid)
              AND severity = 'hard'
        """),
        {"version_id": version_id},
    )
    hard_conflicts = int(conflicts_result.scalar_one())
    if hard_conflicts > 0:
        raise HTTPException(status_code=409, detail="لا يمكن اعتماد جدول يحتوي على تعارضات صارمة")

    result = await db.execute(
        text("""
            UPDATE school.timetable_versions
            SET status = 'approved'
            WHERE id = CAST(:version_id AS uuid)
            RETURNING id, name_ar, status, effective_from, effective_to, is_current, created_at
        """),
        {"version_id": version_id},
    )
    data = dict(result.one()._mapping)
    await audit_event(db, "approve_version", "school_timetable_version", version_id, data)
    await db.commit()
    return data


@router.post("/versions/{version_id}/archive")
async def archive_version(version_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(
        text("""
            UPDATE school.timetable_versions
            SET status = 'archived', is_current = false, effective_to = COALESCE(effective_to, CURRENT_DATE)
            WHERE id = CAST(:version_id AS uuid)
            RETURNING id, name_ar, status, effective_from, effective_to, is_current, created_at
        """),
        {"version_id": version_id},
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="نسخة الجدول غير موجودة")

    data = dict(row._mapping)
    await audit_event(db, "archive_version", "school_timetable_version", version_id, data)
    await db.commit()
    return data


@router.post("/versions/{version_id}/publish")
async def publish_version(version_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    version_result = await db.execute(
        text("""
            SELECT
                tv.id,
                tv.name_ar,
                tv.status,
                tv.effective_from,
                tv.effective_to,
                tv.is_current,
                tv.created_at,
                count(ts.id) AS slots_count
            FROM school.timetable_versions tv
            LEFT JOIN school.timetable_slots ts ON ts.timetable_version_id = tv.id
            WHERE tv.id = CAST(:version_id AS uuid)
            GROUP BY tv.id, tv.name_ar, tv.status, tv.effective_from, tv.effective_to, tv.is_current, tv.created_at
        """),
        {"version_id": version_id},
    )
    version_row = version_result.first()
    if version_row is None:
        raise HTTPException(status_code=404, detail="نسخة الجدول غير موجودة")

    version_data = dict(version_row._mapping)

    if version_data["status"] != "approved":
        raise HTTPException(status_code=409, detail="لا يمكن نشر نسخة جدول قبل اعتمادها أولًا")

    if int(version_data["slots_count"]) < 1:
        raise HTTPException(status_code=409, detail="لا يمكن نشر نسخة جدول فارغة بدون حصص")

    conflicts_result = await db.execute(
        text("""
            SELECT count(*)
            FROM school.vw_school_timetable_conflicts
            WHERE timetable_version_id = CAST(:version_id AS uuid)
              AND severity = 'hard'
        """),
        {"version_id": version_id},
    )
    hard_conflicts = int(conflicts_result.scalar_one())
    if hard_conflicts > 0:
        raise HTTPException(status_code=409, detail="لا يمكن نشر جدول يحتوي على تعارضات صارمة")

    await db.execute(text("UPDATE school.timetable_versions SET is_current = false"))
    result = await db.execute(
        text("""
            UPDATE school.timetable_versions
            SET status = 'published', is_current = true, effective_from = COALESCE(effective_from, CURRENT_DATE)
            WHERE id = CAST(:version_id AS uuid)
            RETURNING id, name_ar, status, effective_from, effective_to, is_current, created_at
        """),
        {"version_id": version_id},
    )
    data = dict(result.one()._mapping)
    await audit_event(db, "publish_version", "school_timetable_version", version_id, data)
    await db.commit()
    return data


class SlotPayload(BaseModel):
    timetable_version_id: str | None = None
    school_class_id: str
    week_day_id: int
    period_id: str
    subject_name_ar: str
    teacher_id: str | None = None
    classroom_id: str | None = None
    notes: str | None = None


@router.post("/slots")
async def create_slot(payload: SlotPayload, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    version_id = payload.timetable_version_id

    if not version_id:
        version = await db.execute(text("""
            SELECT id
            FROM school.timetable_versions
            WHERE is_current = true
            ORDER BY created_at DESC
            LIMIT 1
        """))
        row = version.first()
        if not row:
            new_version = await db.execute(text("""
                INSERT INTO school.timetable_versions(name_ar, status, is_current)
                VALUES ('جدول المدرسة الأساسي', 'draft', true)
                RETURNING id
            """))
            version_id = str(new_version.one()._mapping["id"])
        else:
            version_id = str(row._mapping["id"])

    version_status_result = await db.execute(text("""
        SELECT id, name_ar, status, is_current
        FROM school.timetable_versions
        WHERE id = CAST(:version_id AS uuid)
        LIMIT 1
    """), {"version_id": version_id})
    version_status_row = version_status_result.first()

    if version_status_row is None:
        raise HTTPException(status_code=404, detail="نسخة الجدول غير موجودة")

    version_data = dict(version_status_row._mapping)
    if version_data["status"] in {"approved", "published"}:
        raise HTTPException(
            status_code=409,
            detail="لا يمكن إضافة حصة داخل نسخة جدول معتمدة أو منشورة. أنشئ نسخة مسودة للتعديل.",
        )

    # تعارض المدرس
    if payload.teacher_id:
        conflict = await db.execute(text("""
            SELECT id
            FROM school.timetable_slots
            WHERE timetable_version_id = CAST(:version_id AS uuid)
              AND teacher_id = CAST(:teacher_id AS uuid)
              AND week_day_id = :week_day_id
              AND period_id = CAST(:period_id AS uuid)
            LIMIT 1
        """), {
            "version_id": version_id,
            "teacher_id": payload.teacher_id,
            "week_day_id": payload.week_day_id,
            "period_id": payload.period_id,
        })
        if conflict.first():
            raise HTTPException(status_code=409, detail="تعارض: المدرس لديه حصة في نفس اليوم والحصة")

    # تعارض القاعة
    if payload.classroom_id:
        conflict = await db.execute(text("""
            SELECT id
            FROM school.timetable_slots
            WHERE timetable_version_id = CAST(:version_id AS uuid)
              AND classroom_id = CAST(:classroom_id AS uuid)
              AND week_day_id = :week_day_id
              AND period_id = CAST(:period_id AS uuid)
            LIMIT 1
        """), {
            "version_id": version_id,
            "classroom_id": payload.classroom_id,
            "week_day_id": payload.week_day_id,
            "period_id": payload.period_id,
        })
        if conflict.first():
            raise HTTPException(status_code=409, detail="تعارض: القاعة مشغولة في نفس اليوم والحصة")

    # تعارض الفصل
    conflict = await db.execute(text("""
        SELECT id
        FROM school.timetable_slots
        WHERE timetable_version_id = CAST(:version_id AS uuid)
          AND school_class_id = CAST(:school_class_id AS uuid)
          AND week_day_id = :week_day_id
          AND period_id = CAST(:period_id AS uuid)
        LIMIT 1
    """), {
        "version_id": version_id,
        "school_class_id": payload.school_class_id,
        "week_day_id": payload.week_day_id,
        "period_id": payload.period_id,
    })
    if conflict.first():
        raise HTTPException(status_code=409, detail="تعارض: الفصل لديه حصة في نفس اليوم والحصة")

    result = await db.execute(text("""
        INSERT INTO school.timetable_slots
        (
          timetable_version_id,
          school_class_id,
          week_day_id,
          period_id,
          subject_name_ar,
          teacher_id,
          classroom_id,
          notes
        )
        VALUES
        (
          CAST(:version_id AS uuid),
          CAST(:school_class_id AS uuid),
          :week_day_id,
          CAST(:period_id AS uuid),
          :subject_name_ar,
          CAST(:teacher_id AS uuid),
          CAST(:classroom_id AS uuid),
          :notes
        )
        RETURNING *
    """), {
        "version_id": version_id,
        "school_class_id": payload.school_class_id,
        "week_day_id": payload.week_day_id,
        "period_id": payload.period_id,
        "subject_name_ar": payload.subject_name_ar,
        "teacher_id": payload.teacher_id,
        "classroom_id": payload.classroom_id,
        "notes": payload.notes,
    })

    row = dict(result.one()._mapping)
    await audit_event(db, "create_slot", "school_timetable_slot", str(row["id"]), row)
    await db.commit()
    return row


@router.delete("/slots/{slot_id}")
async def delete_slot(slot_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    slot_result = await db.execute(text("""
        SELECT
            slot.id,
            slot.timetable_version_id,
            tv.name_ar AS timetable_name_ar,
            tv.status AS timetable_status,
            tv.is_current
        FROM school.timetable_slots slot
        JOIN school.timetable_versions tv ON tv.id = slot.timetable_version_id
        WHERE slot.id = CAST(:slot_id AS uuid)
        LIMIT 1
    """), {"slot_id": slot_id})
    slot_row = slot_result.first()

    if slot_row is None:
        raise HTTPException(status_code=404, detail="الحصة غير موجودة")

    slot_data = dict(slot_row._mapping)
    if slot_data["timetable_status"] in {"approved", "published"}:
        raise HTTPException(
            status_code=409,
            detail="لا يمكن حذف حصة من نسخة جدول معتمدة أو منشورة. أرشف النسخة أو أنشئ نسخة مسودة للتعديل.",
        )

    await db.execute(
        text("DELETE FROM school.timetable_slots WHERE id = CAST(:slot_id AS uuid)"),
        {"slot_id": slot_id},
    )
    await audit_event(db, "delete_slot", "school_timetable_slot", slot_id, json_safe(slot_data))
    await db.commit()
    return {"deleted": True, "id": slot_id}


@router.post("/exports/csv")
async def export_csv(
    payload: ExportCsvPayload | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    requested_version_id = payload.version_id if payload else None
    grid_rows = await grid(version_id=requested_version_id, db=db)

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["day", "period", "class", "subject", "teacher", "room"],
    )
    writer.writeheader()

    for item in grid_rows:
        writer.writerow({
            "day": item.get("day_name_ar") or "",
            "period": item.get("period_name_ar") or "",
            "class": item.get("class_name_ar") or item.get("class_code") or "",
            "subject": item.get("subject_name_ar") or "",
            "teacher": item.get("teacher_name_ar") or "",
            "room": item.get("room_name_ar") or "",
        })

    version_id = requested_version_id or (str(grid_rows[0]["timetable_version_id"]) if grid_rows else None)

    job_result = await db.execute(text("""
        INSERT INTO school.timetable_export_jobs(timetable_version_id, export_type, report_scope, payload)
        VALUES (CAST(:version_id AS uuid), 'csv', 'grid', CAST(:payload AS jsonb))
        RETURNING id
    """), {
        "version_id": version_id,
        "payload": json.dumps({
            "rows_count": len(grid_rows),
            "version_id": version_id,
            "scope": "selected_version" if version_id else "all_versions",
        }, ensure_ascii=False),
    })

    job_id = str(job_result.one()._mapping["id"])

    await audit_event(
        db,
        "export_csv",
        "school_timetable_export_job",
        job_id,
        {"rows_count": len(grid_rows), "version_id": version_id},
    )

    await db.commit()

    return {
        "job_id": job_id,
        "file_name": "school-timetable.csv",
        "content_type": "text/csv; charset=utf-8",
        "csv_text": output.getvalue(),
    }
