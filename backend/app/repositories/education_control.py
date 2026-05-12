from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class EducationControlRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_institutes(self) -> list[dict[str, Any]]:
        result = await self.db.execute(
            text("""
                SELECT id, code, name_ar, institute_type, education_stage,
                       zone_name, administration_name, is_active, created_at
                FROM school.institutes
                ORDER BY created_at DESC
                LIMIT 200
            """)
        )
        return [dict(row._mapping) for row in result]

    async def create_institute(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = await self.db.execute(
            text("""
                INSERT INTO school.institutes
                (code, name_ar, institute_type, education_stage, zone_name, administration_name)
                VALUES
                (:code, :name_ar, :institute_type, :education_stage, :zone_name, :administration_name)
                RETURNING id, code, name_ar, institute_type, education_stage,
                          zone_name, administration_name, is_active, created_at
            """),
            payload,
        )
        await self.db.commit()
        return dict(result.one()._mapping)

    async def list_students(self) -> list[dict[str, Any]]:
        result = await self.db.execute(
            text("""
                SELECT id, legacy_access_id, national_id, student_name_ar, gender,
                       nationality, religion, health_status, class_name,
                       enrollment_status, created_at
                FROM school.students
                ORDER BY created_at DESC
                LIMIT 200
            """)
        )
        return [dict(row._mapping) for row in result]

    async def create_student(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = await self.db.execute(
            text("""
                INSERT INTO school.students
                (legacy_access_id, national_id, student_name_ar, gender,
                 nationality, religion, health_status, class_name)
                VALUES
                (:legacy_access_id, :national_id, :student_name_ar, :gender,
                 :nationality, :religion, :health_status, :class_name)
                RETURNING id, legacy_access_id, national_id, student_name_ar,
                          gender, nationality, religion, health_status, class_name,
                          enrollment_status, created_at
            """),
            payload,
        )
        await self.db.commit()
        return dict(result.one()._mapping)

    async def list_subjects(self) -> list[dict[str, Any]]:
        result = await self.db.execute(
            text("""
                SELECT id, grade_id, code, name_ar, max_score, min_score,
                       has_written, has_coursework, sort_order, is_active
                FROM education_control.subjects
                ORDER BY sort_order, name_ar
                LIMIT 300
            """)
        )
        return [dict(row._mapping) for row in result]

    async def create_subject(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = await self.db.execute(
            text("""
                INSERT INTO education_control.subjects
                (grade_id, code, name_ar, max_score, min_score,
                 has_written, has_coursework, sort_order)
                VALUES
                (:grade_id, :code, :name_ar, :max_score, :min_score,
                 :has_written, :has_coursework, :sort_order)
                RETURNING id, grade_id, code, name_ar, max_score, min_score,
                          has_written, has_coursework, sort_order, is_active
            """),
            payload,
        )
        await self.db.commit()
        return dict(result.one()._mapping)

    async def list_activation_settings(self) -> list[dict[str, Any]]:
        result = await self.db.execute(
            text("""
                SELECT id, source_file, activation_code, activation_name_ar,
                       is_active, imported_at
                FROM education_control.activation_settings
                ORDER BY activation_code
            """)
        )
        return [dict(row._mapping) for row in result]

    async def readiness(self) -> dict[str, Any]:
        result = await self.db.execute(
            text("""
                SELECT
                  (SELECT count(*) FROM school.institutes) AS institutes_count,
                  (SELECT count(*) FROM school.students) AS students_count,
                  (SELECT count(*) FROM education_control.subjects) AS subjects_count,
                  (SELECT count(*) FROM education_control.activation_settings) AS activations_count
            """)
        )
        return dict(result.one()._mapping)

    async def calculate_student_result(self, student_id: UUID) -> dict[str, Any]:
        result = await self.db.execute(
            text("""
                SELECT COALESCE(SUM(total_score), 0) AS total_score
                FROM education_control.score_entries
                WHERE student_id = :student_id
            """),
            {"student_id": str(student_id)},
        )
        total = float(result.one()._mapping["total_score"] or 0)

        status = "pass" if total > 0 else "pending"

        inserted = await self.db.execute(
            text("""
                INSERT INTO education_control.results
                (student_id, total_score, percentage, status)
                VALUES (:student_id, :total_score, :percentage, :status)
                ON CONFLICT (student_id, academic_year_id)
                DO UPDATE SET
                  total_score = EXCLUDED.total_score,
                  percentage = EXCLUDED.percentage,
                  status = EXCLUDED.status
                RETURNING id, student_id, total_score, percentage, status,
                          rank_no, is_approved, created_at
            """),
            {
                "student_id": str(student_id),
                "total_score": total,
                "percentage": total,
                "status": status,
            },
        )
        await self.db.commit()
        return dict(inserted.one()._mapping)
