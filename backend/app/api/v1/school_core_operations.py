from __future__ import annotations

import json
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/api/v1/school-core", tags=["school-core"])


def _plain(value: Any) -> Any:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                return _plain(json.loads(stripped))
            except json.JSONDecodeError:
                return value
    return value


def _row(row: Any) -> dict[str, Any]:
    return {key: _plain(value) for key, value in dict(row).items()}


async def _one(db: AsyncSession, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    result = await db.execute(text(sql), params or {})
    row = result.mappings().first()
    return _row(row) if row else {}


async def _all(db: AsyncSession, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    result = await db.execute(text(sql), params or {})
    return [_row(row) for row in result.mappings().all()]


@router.get("/overview", response_model=dict)
async def school_core_overview(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    counts = await _one(
        db,
        """
        SELECT
          (SELECT count(*) FROM school.students) AS students_count,
          (SELECT count(*) FROM school.guardians) AS guardians_count,
          (SELECT count(*) FROM school.student_guardians) AS student_guardian_links_count,
          (SELECT count(*) FROM school.school_classes) AS classes_count,
          (SELECT count(*) FROM school.grades) AS grades_count,
          (SELECT count(*) FROM school.institutes) AS institutes_count,
          (SELECT count(*) FROM hr.attendance_records) AS staff_attendance_records_count,
          (SELECT count(*) FROM hr.attendance_records WHERE status = 'present') AS staff_present_count,
          (SELECT count(*) FROM hr.attendance_records WHERE status <> 'present') AS staff_exception_count
        """
    )

    latest_students = await _all(
        db,
        """
        SELECT
          s.id,
          s.legacy_access_id,
          s.national_id,
          s.student_name_ar,
          s.gender,
          s.class_name,
          s.enrollment_status,
          s.created_at
        FROM school.students s
        ORDER BY s.created_at DESC NULLS LAST, s.student_name_ar
        LIMIT 8
        """
    )

    return {
        "module": "school-core-operations",
        "mode": "read-only",
        "database_impact": "none",
        "safe_to_import_slots": False,
        "safe_to_confirm": False,
        "counts": counts,
        "latest_students": latest_students,
        "capabilities": [
            "students_read_model",
            "guardians_read_model",
            "student_guardian_links_read_model",
            "staff_attendance_read_model"
        ],
        "known_limits": [
            "student attendance is not modeled yet; only hr.attendance_records exists now",
            "this API does not create, update, delete, import, or migrate data",
            "ROZ slot import remains blocked"
        ],
        "actions": [
            {
                "title": "الطلاب وأولياء الأمور",
                "description": "عرض تشغيلي read-only للطلاب وروابط أولياء الأمور.",
                "href": "/school/students"
            },
            {
                "title": "الجدول المدرسي",
                "description": "الانتقال إلى استوديو الجدول الحالي.",
                "href": "/timetable"
            }
        ]
    }


@router.get("/students", response_model=list[dict])
async def school_core_students(
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    return await _all(
        db,
        """
        SELECT
          s.id,
          s.legacy_access_id,
          s.national_id,
          s.student_name_ar,
          s.gender,
          s.nationality,
          s.religion,
          s.health_status,
          s.class_name,
          s.enrollment_status,
          s.created_at,
          i.name_ar AS institute_name_ar,
          g.name_ar AS grade_name_ar,
          COALESCE(
            jsonb_agg(
              DISTINCT jsonb_build_object(
                'id', gu.id,
                'full_name_ar', gu.full_name_ar,
                'national_id', gu.national_id,
                'phone', gu.phone,
                'relation_type', COALESCE(sg.relation_type, gu.relation_type),
                'is_primary', COALESCE(sg.is_primary, false)
              )
            ) FILTER (WHERE gu.id IS NOT NULL),
            '[]'::jsonb
          ) AS guardians
        FROM school.students s
        LEFT JOIN school.institutes i ON i.id = s.institute_id
        LEFT JOIN school.grades g ON g.id = s.grade_id
        LEFT JOIN school.student_guardians sg ON sg.student_id = s.id
        LEFT JOIN school.guardians gu ON gu.id = sg.guardian_id
        GROUP BY
          s.id,
          i.name_ar,
          g.name_ar
        ORDER BY s.created_at DESC NULLS LAST, s.student_name_ar
        LIMIT :limit
        """,
        {"limit": limit},
    )


@router.get("/guardians", response_model=list[dict])
async def school_core_guardians(
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    return await _all(
        db,
        """
        SELECT
          gu.id,
          gu.national_id,
          gu.full_name_ar,
          gu.phone,
          gu.relation_type,
          gu.created_at,
          COALESCE(
            jsonb_agg(
              DISTINCT jsonb_build_object(
                'id', s.id,
                'student_name_ar', s.student_name_ar,
                'class_name', s.class_name,
                'relation_type', sg.relation_type,
                'is_primary', sg.is_primary
              )
            ) FILTER (WHERE s.id IS NOT NULL),
            '[]'::jsonb
          ) AS students
        FROM school.guardians gu
        LEFT JOIN school.student_guardians sg ON sg.guardian_id = gu.id
        LEFT JOIN school.students s ON s.id = sg.student_id
        GROUP BY gu.id
        ORDER BY gu.created_at DESC NULLS LAST, gu.full_name_ar
        LIMIT :limit
        """,
        {"limit": limit},
    )


@router.get("/attendance", response_model=list[dict])
async def school_core_staff_attendance(
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    return await _all(
        db,
        """
        SELECT
          ar.id,
          ar.employee_id,
          emp.full_name_ar AS employee_name_ar,
          emp.employee_no,
          ar.attendance_date,
          ar.check_in,
          ar.check_out,
          ar.status,
          ar.notes,
          ar.created_at
        FROM hr.attendance_records ar
        JOIN hr.employees emp ON emp.id = ar.employee_id
        ORDER BY ar.attendance_date DESC, emp.full_name_ar
        LIMIT :limit
        """,
        {"limit": limit},
    )
