from functools import lru_cache
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, PostgresDsn, validator, HttpUrl
from pydantic.types import SecretStr

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "Py-Connect"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: SecretStr = Field(default_factory=lambda: SecretStr("your-secret-key-here"))
    
    # API
    API_PREFIX: str = "/api"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "pyconnect"
    DATABASE_URI: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # File Uploads
    UPLOAD_DIR: Path = Path("/tmp/pyconnect_uploads")
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set[str] = {"zip"}
    
    # Docker
    DOCKER_NETWORK: str = "pyconnect_network"
    DOCKER_PORT_RANGE: tuple[int, int] = (10000, 20000)
    
    # Security
    SECURE_COOKIES: bool = True
    SESSION_COOKIE_NAME: str = "pyconnect_session"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
