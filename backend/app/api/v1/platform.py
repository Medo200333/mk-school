from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


COUNT_QUERIES = {
    "core": [
        ("organizations", "core.organizations"),
        ("users", "core.users"),
        ("documents", "core.documents"),
        ("modules", "core.app_modules"),
    ],
    "hr": [
        ("employees", "hr.employees"),
        ("teachers", "hr.teacher_profiles"),
        ("attendance_records", "hr.attendance_records"),
        ("leave_requests", "hr.leave_requests"),
    ],
    "school": [
        ("institutes", "school.institutes"),
        ("students", "school.students"),
        ("guardians", "school.guardians"),
        ("classrooms", "school.classrooms"),
        ("school_classes", "school.school_classes"),
    ],
    "timetable": [
        ("days", "school.week_days"),
        ("periods", "school.lesson_periods"),
        ("lessons", "school.timetable_slots"),
        ("versions", "school.timetable_versions"),
        ("subjects", "school.subjects"),
        ("curriculum_plans", "school.curriculum_plans"),
        ("constraints", "school.timetable_constraints"),
        ("generation_runs", "school.timetable_generation_runs"),
        ("teachers", "school.teachers"),
        ("conflicts", "school.vw_school_timetable_conflicts"),
    ],
    "education-control": [
        ("subjects", "education_control.subjects"),
        ("committees", "education_control.committees"),
        ("scores", "education_control.score_entries"),
        ("results", "education_control.results"),
    ],
    "access-mirror": [
        ("batches", "education_control.access_import_batches"),
        ("snapshots", "education_control.access_import_table_snapshots"),
    ],
    "operations": [
        ("import_jobs", "operations.import_jobs"),
        ("reports", "operations.report_templates"),
        ("feature_flags", "operations.feature_flags"),
        ("scanner_batches", "education_control.scanner_import_batches"),
    ],
}


async def table_count(db: AsyncSession, table_name: str) -> int:
    exists = await db.execute(text("SELECT to_regclass(:table_name)"), {"table_name": table_name})
    if exists.scalar_one() is None:
        return 0

    result = await db.execute(text(f"SELECT count(*) FROM {table_name}"))
    return int(result.scalar_one())


async def module_counts(db: AsyncSession, module_code: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key, table_name in COUNT_QUERIES[module_code]:
        counts[key] = await table_count(db, table_name)
    return counts


@router.get("/modules", response_model=list[dict[str, Any]])
async def list_modules(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    modules_result = await db.execute(
        text(
            """
            SELECT code, name_ar, scope_name, route_path, status, sort_order, feature_flag
            FROM core.app_modules
            ORDER BY sort_order, name_ar
            """
        )
    )
    modules = [dict(row._mapping) for row in modules_result]

    for module in modules:
        code = module["code"]
        module["counts"] = await module_counts(db, code) if code in COUNT_QUERIES else {}
        module["acceptance"] = [
            "Migration",
            "API Contract",
            "Frontend Route",
            "Audit Ready",
        ]

    return modules


@router.get("/overview", response_model=dict[str, Any])
async def platform_overview(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    modules = await list_modules(db)
    flags_result = await db.execute(
        text(
            """
            SELECT code, name_ar, is_enabled
            FROM operations.feature_flags
            ORDER BY code
            """
        )
    )
    flags = [dict(row._mapping) for row in flags_result]

    return {
        "product": "ERP تعليمي متكامل للمدارس والمعاهد والموظفين والكنترول",
        "version": "1.0",
        "principle": "Core Platform + Modules + Raw Mirror + Normalized Operations",
        "modules": modules,
        "feature_flags": flags,
    }
