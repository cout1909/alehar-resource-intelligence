"""Validated environment configuration; no external services are required."""

import os
from functools import lru_cache
from urllib.parse import urlsplit

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, model_validator


class Settings(BaseModel):
    app_env: str = "development"
    database_url: str = "sqlite:///./alehar.db"
    request_timeout: float = Field(default=10, gt=0, le=120)
    max_source_text_length: int = Field(default=30000, ge=100, le=100000)
    max_source_bytes: int = Field(default=2000000, ge=1024, le=10000000)
    max_redirects: int = Field(default=5, ge=0, le=10)
    verify_all_delay: float = Field(default=0.5, ge=0, le=10)
    log_level: str = "INFO"
    ai_enabled: bool = False
    ai_provider: str = "groq"
    groq_api_key: SecretStr = Field(default=SecretStr(""), exclude=True)
    ai_model: str = ""
    ai_temperature: float = Field(default=0, ge=0, le=2)
    ai_timeout: float = Field(default=20, gt=0, le=120)
    ai_max_input_chars: int = Field(default=12000, ge=100, le=30000)
    frontend_origin: str = "http://localhost:5173"
    allowed_origins: str = ""
    public_demo_mode: bool = False
    public_demo_snapshot: bool = False
    enable_docs: bool = True
    scheduler_enabled: bool = False
    verification_interval_hours: float = Field(default=168, ge=1, le=8760)

    @property
    def cors_origins(self) -> list[str]:
        return list(dict.fromkeys(value.strip().rstrip("/") for value in
                                 (self.allowed_origins or self.frontend_origin).split(",") if value.strip()))

    @model_validator(mode="after")
    def validate_origins(self):
        if self.public_demo_snapshot and not self.public_demo_mode:
            raise ValueError("PUBLIC_DEMO_SNAPSHOT requires PUBLIC_DEMO_MODE=true")
        for origin in self.cors_origins:
            parsed = urlsplit(origin)
            if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                    or parsed.username or parsed.password or parsed.path
                    or parsed.query or parsed.fragment or "*" in origin):
                raise ValueError("CORS origins must be explicit HTTP(S) origins without paths or wildcards")
        if not self.cors_origins:
            raise ValueError("At least one explicit frontend origin is required")
        return self

    @property
    def ai_config_status(self) -> str:
        if not self.ai_enabled:
            return "disabled"
        if self.ai_provider != "groq":
            return "unavailable"
        if not self.groq_api_key.get_secret_value().strip() or not self.ai_model.strip():
            return "not_configured"
        return "ready"

    @property
    def ai_active(self) -> bool:
        return self.ai_config_status == "ready"


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    values = {
        field: os.environ[field.upper()]
        for field in Settings.model_fields
        if field.upper() in os.environ
    }
    return Settings(**values)
