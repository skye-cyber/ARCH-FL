"""
Configuration management for FileWarp backend.
Loads settings from environment variables with defaults.
"""

from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from dotenv import load_dotenv


# Base directories
BASE_DIR = Path(__file__).parent.parent
DEFAULT_LOG_DIR = BASE_DIR / "logs"

# Load .env file if present
ENV_FILE_PATH = (BASE_DIR / ".env").absolute()
load_dotenv(ENV_FILE_PATH)


class Settings(BaseSettings):
    """Application settings"""

    # Server settings
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8008, env="PORT")
    DEBUG: bool = Field(False, env="DEBUG")
    RELOAD: bool = Field(False, env="RELOAD")
    WORKERS: int = Field(1, env="WORKERS")

    # API settings
    API_V1_PREFIX: str = "/api/v1"
    API_TITLE: str = "ARCH-FL Dashboard API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Backend API for ARCH-FL Federated Dashboard"

    # Security
    SECRET_KEY: str = Field(
        "archfl-secret-key-to-be-changed-in-production", env="SECRET_KEY"
    )
    API_KEY: Optional[str] = Field(None, env="API_KEY")
    ENABLE_AUTH: bool = Field(False, env="ENABLE_AUTH")
    CORS_ORIGINS: List[str] = Field(["*"], env="CORS_ORIGINS")
    ALLOWED_METHODS: List[str] = Field(["*"], env="ALLOWED_METHODS")
    ALLOWED_HEADERS: List[str] = Field(["*"], env="ALLOWED_HEADERS")
    ALLOW_CREDENTIALS: bool = Field(True, env="ALLOW_CREDENTIALS")

    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT"
    )

    # Paths
    LOG_DIR: Path = Field(DEFAULT_LOG_DIR, env="LOG_DIR")
    LOG_FILE: str = Field("archfl_server.log", env="LOG_FILE")
    DATASET_BASE_PATH: str = Field(
        (Path(__file__).parent.parent.parent.parent / "src/datasets").as_posix(),
        env="DATASET_BASE_PATH",
    )
    TASK_PATH: str = Field(
        (Path(__file__).parent.parent / "tasks/tasks.json").as_posix(),
        env="TASKS_PATH",
    )
    TASK_DIR: str = Field(
        (Path(__file__).parent.parent / "tasks/").as_posix(),
        env="TASKS_DIR",
    )
    # WebSocket
    WS_PING_INTERVAL: int = Field(30, env="WS_PING_INTERVAL")
    WS_MAX_CONNECTIONS: int = Field(1000, env="WS_MAX_CONNECTIONS")

    # Performance
    ENABLE_CACHE: bool = Field(True, env="ENABLE_CACHE")
    CACHE_TTL: int = Field(300, env="CACHE_TTL")  # 5 minutes

    @field_validator("LOG_DIR", mode="before")
    def create_directories(cls, v):
        """Create directories if they don't exist"""
        if v and isinstance(v, (str, Path)):
            path = Path(v)
            path.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ENV_FILE_PATH
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Create global settings instance
settings = Settings()
