from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InstituteCreate(BaseModel):
    code: str | None = None
    name_ar: str
    institute_type: str | None = None
    education_stage: str | None = None
    zone_name: str | None = None
    administration_name: str | None = None


class InstituteRead(InstituteCreate):
    id: UUID
    is_active: bool
    created_at: datetime


class StudentCreate(BaseModel):
    legacy_access_id: str | None = None
    national_id: str | None = None
    student_name_ar: str
    gender: str | None = None
    nationality: str | None = None
    religion: str | None = None
    health_status: str | None = None
    class_name: str | None = None


class StudentRead(StudentCreate):
    id: UUID
    enrollment_status: str
    created_at: datetime


class SubjectCreate(BaseModel):
    grade_id: UUID | None = None
    code: str
    name_ar: str
    max_score: float | None = None
    min_score: float | None = None
    has_written: bool = True
    has_coursework: bool = False
    sort_order: int = 0


class SubjectRead(SubjectCreate):
    id: UUID
    is_active: bool


class ScoreEntryCreate(BaseModel):
    student_id: UUID
    subject_id: UUID
    exam_term_id: UUID | None = None
    exam_round_id: UUID | None = None
    written_score: float | None = Field(default=None, ge=0)
    coursework_score: float | None = Field(default=None, ge=0)
    is_absent: bool = False


class ScoreEntryRead(ScoreEntryCreate):
    id: UUID
    total_score: float
    is_locked: bool
    created_at: datetime


class ResultRead(BaseModel):
    id: UUID
    student_id: UUID
    total_score: float
    percentage: float
    status: str
    rank_no: int | None
    is_approved: bool
    created_at: datetime


class AccessTableSnapshot(BaseModel):
    source_database: str
    source_table: str
    rows_count: int
    columns_json: list[str]
    sample_json: list[dict] = []
    classification: str | None = None


class ModuleReadiness(BaseModel):
    module: str
    status: str
    database: str
    backend: str
    frontend: str
    next_steps: list[str]
