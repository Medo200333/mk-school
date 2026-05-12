from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.education_control import EducationControlRepository
from app.schemas.education_control import (
    InstituteCreate,
    ModuleReadiness,
    StudentCreate,
    SubjectCreate,
)
from app.services.education_control import EducationControlService

router = APIRouter(prefix="/api/v1/education-control", tags=["education-control"])


def get_service(db: AsyncSession = Depends(get_db)) -> EducationControlService:
    repository = EducationControlRepository(db)
    return EducationControlService(repository)


@router.get("/readiness", response_model=dict)
async def readiness(service: EducationControlService = Depends(get_service)) -> dict:
    return await service.readiness()


@router.get("/institutes", response_model=list[dict])
async def list_institutes(service: EducationControlService = Depends(get_service)) -> list[dict]:
    return await service.list_institutes()


@router.post("/institutes", response_model=dict)
async def create_institute(
    payload: InstituteCreate,
    service: EducationControlService = Depends(get_service),
) -> dict:
    return await service.create_institute(payload.model_dump())


@router.get("/students", response_model=list[dict])
async def list_students(service: EducationControlService = Depends(get_service)) -> list[dict]:
    return await service.list_students()


@router.post("/students", response_model=dict)
async def create_student(
    payload: StudentCreate,
    service: EducationControlService = Depends(get_service),
) -> dict:
    return await service.create_student(payload.model_dump())


@router.get("/subjects", response_model=list[dict])
async def list_subjects(service: EducationControlService = Depends(get_service)) -> list[dict]:
    return await service.list_subjects()


@router.post("/subjects", response_model=dict)
async def create_subject(
    payload: SubjectCreate,
    service: EducationControlService = Depends(get_service),
) -> dict:
    return await service.create_subject(payload.model_dump())


@router.get("/activation-settings", response_model=list[dict])
async def list_activation_settings(
    service: EducationControlService = Depends(get_service),
) -> list[dict]:
    return await service.list_activation_settings()


@router.post("/students/{student_id}/calculate-result", response_model=dict)
async def calculate_student_result(
    student_id: UUID,
    service: EducationControlService = Depends(get_service),
) -> dict:
    return await service.calculate_student_result(student_id)
