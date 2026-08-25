from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILES = [
    str(Path(__file__).resolve().parent.parent.parent / ".env"),
    str(ROOT_DIR / ".env"),
    ".env",
]


class Settings(BaseSettings):
    PROJECT_NAME: str = "Waypoint"
    PROJECT_DESCRIPTION: str = "AI-Assisted Spend & Procurement Approval Router"
    API_PREFIX: str = "/api"
    DATABASE_URL: str = "sqlite+aiosqlite:///./waypoint.db"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    LLM_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.6-flash"
    USE_LIVE_LLM: bool = True
    POLICY_FILE_PATH: str = str(
        Path(__file__).parent.parent / "policies" / "corporate_procurement_policy_v1.md"
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        extra="ignore",
        env_file_encoding="utf-8",
    )


settings = Settings()
