import os
from typing import List, Union
from pydantic import AnyHttpUrl, BeforeValidator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated


def parse_cors(v: Union[str, List[str]]) -> List[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NexusFlow Enterprise API"

    # CORS configuration
    BACKEND_CORS_ORIGINS: Annotated[
        List[str], BeforeValidator(parse_cors)
    ] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if not v:
            return ["*"]
        return v

    # Multi-tenant PostgreSQL configurations
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "nexusflow"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = ""

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str, info) -> str:
        if v:
            return v
        
        # Check environment variables directly or assemble
        env_url = os.getenv("DATABASE_URL", "")
        if env_url:
            return env_url
            
        # Lightweight local development mode supported via SQLite fallback if no pg creds exist
        pg_server = os.getenv("POSTGRES_SERVER", "localhost")
        pg_user = os.getenv("POSTGRES_USER", "")
        pg_password = os.getenv("POSTGRES_PASSWORD", "")
        pg_db = os.getenv("POSTGRES_DB", "")
        pg_port = os.getenv("POSTGRES_PORT", "5432")
        
        if pg_user and pg_password and pg_db:
            return f"postgresql://{pg_user}:{pg_password}@{pg_server}:{pg_port}/{pg_db}"
            
        # Lightweight SQLite configuration strictly for rapid local development
        return "sqlite:///./nexusflow_local_dev.db"

    # Security Configuration
    SECRET_KEY: str = "SUPER_SECRET_NEXUSFLOW_KEY_DO_NOT_USE_IN_PRODUCTION_1234567890"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 2  # 2 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Caching / Message Queue (Redis & Celery)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Cloud Storage (Azure Blob Storage)
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "nexusflow-attachments"
    LOCAL_UPLOAD_DIR: str = "./uploads"

    # Enterprise Feature Flags (Admin configurable toggles)
    ENABLE_NOTIFICATIONS: bool = True
    ENABLE_ESCALATION: bool = True
    ENABLE_ANALYTICS: bool = True
    ENABLE_REDIS_CACHE: bool = False  # Turned off by default in MVP boundaries to prevent infrastructure locks

    # Observability settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"


settings = Settings()
