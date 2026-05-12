from typing import Any
from uuid import UUID

from app.repositories.education_control import EducationControlRepository


class EducationControlService:
    def __init__(self, repository: EducationControlRepository) -> None:
        self.repository = repository

    async def list_institutes(self) -> list[dict[str, Any]]:
        return await self.repository.list_institutes()

    async def create_institute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.repository.create_institute(payload)

    async def list_students(self) -> list[dict[str, Any]]:
        return await self.repository.list_students()

    async def create_student(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.repository.create_student(payload)

    async def list_subjects(self) -> list[dict[str, Any]]:
        return await self.repository.list_subjects()

    async def create_subject(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.repository.create_subject(payload)

    async def list_activation_settings(self) -> list[dict[str, Any]]:
        return await self.repository.list_activation_settings()

    async def readiness(self) -> dict[str, Any]:
        counts = await self.repository.readiness()
        return {
            "module": "education-control",
            "status": "started",
            "database": "ready",
            "backend": "ready",
            "frontend": "pending",
            "counts": counts,
            "next_steps": [
                "import_access_inventory",
                "map_access_tables_to_normalized_schema",
                "build_frontend_pages",
                "connect_frontend_to_api",
                "add_strict_tests",
            ],
        }

    async def calculate_student_result(self, student_id: UUID) -> dict[str, Any]:
        return await self.repository.calculate_student_result(student_id)
