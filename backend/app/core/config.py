from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "GPSR Compliance Tool"
    APP_ENV: str = "development"
    SECRET_KEY: str = "changeme"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/gpsr_db"
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
