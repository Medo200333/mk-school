from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MK School ERP"
    app_locale: str = "ar-EG"
    app_timezone: str = "Africa/Cairo"
    database_url: str = "postgresql+asyncpg://mk_user:mk_password@localhost:55433/mk_school"
    redis_url: str = "redis://localhost:56379/0"


settings = Settings()
