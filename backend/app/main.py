from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.education_control import router as education_control_router
from app.api.v1.school_core_operations import router as school_core_operations_router
from app.api.v1.school_timetable_operational import router as school_timetable_operational_router
from app.api.v1.platform import router as platform_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="School ERP with Education Control module",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "locale": settings.app_locale,
        "timezone": settings.app_timezone,
    }


app.include_router(platform_router)
app.include_router(school_core_operations_router)
app.include_router(education_control_router)
app.include_router(school_timetable_operational_router)
