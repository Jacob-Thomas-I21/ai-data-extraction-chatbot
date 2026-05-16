"""Application settings, Pydantic schemas, and structlog configuration."""

import logging
import structlog
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# ─── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT
SQL_DIR = PROJECT_ROOT / "sql"


# ─── Settings ─────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    """App configuration loaded from environment / .env file."""

    # LLM provider: "anthropic" or "openai"
    llm_provider: str = "anthropic"

    # Anthropic
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data.db'}"
    log_level: str = "INFO"

    # Conversation history limit (messages per conversation)
    max_history: int = 20

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


# ─── Pydantic Request / Response Schemas ──────────────────────────────────────

class ChatRequest(BaseModel):
    """Incoming chat message from the user."""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    """Response returned to the user."""
    answer: str
    data: list[dict] | None = None
    sql_used: str | None = None
    conversation_id: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    tables: list[str]


# ─── Structlog Configuration ─────────────────────────────────────────────────

def setup_logging() -> None:
    """Configure structlog for structured JSON logging."""

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if settings.log_level == "DEBUG"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
