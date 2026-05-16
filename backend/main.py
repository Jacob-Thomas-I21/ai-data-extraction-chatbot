"""FastAPI application — routes, CORS, and static file serving."""

from pathlib import Path

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import inspect

from backend.config import settings, setup_logging, ChatRequest, ChatResponse, HealthResponse
from backend.database import engine, SessionLocal
from backend.agent.nl_agent import NLAgent

# ─── App Setup ────────────────────────────────────────────────────────────────

setup_logging()
log = structlog.get_logger()

app = FastAPI(
    title="AI Data Extraction Chatbot",
    description="Natural language interface for querying e-commerce and customer support data.",
    version="1.0.0",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the NL agent
agent = NLAgent(db_engine=engine)


# ─── API Routes ───────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Process a natural language query and return an answer."""
    log.info("api.chat", message=request.message[:100], conversation_id=request.conversation_id)

    result = agent.process(
        message=request.message,
        conversation_id=request.conversation_id,
    )

    return ChatResponse(
        answer=result["answer"],
        data=result.get("data"),
        sql_used=result.get("sql_used"),
        conversation_id=result["conversation_id"],
    )


@app.get("/api/health", response_model=HealthResponse)
def health():
    """Health check — verifies database connectivity and lists tables."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Quick row count check
        db = SessionLocal()
        try:
            from backend.database import Customer
            customer_count = db.query(Customer).count()
            if customer_count == 0:
                return HealthResponse(
                    status="warning",
                    database="connected but empty — run 'python seed.py' first",
                    tables=tables,
                )
        finally:
            db.close()

        return HealthResponse(
            status="healthy",
            database="connected",
            tables=tables,
        )
    except Exception as e:
        log.error("health.failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Database unavailable: {e}")


# ─── Static Files (Production) ───────────────────────────────────────────────
# Serve the React build if it exists

FRONTEND_BUILD = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_BUILD.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_BUILD / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """Serve React SPA — all non-API routes return index.html."""
        file_path = FRONTEND_BUILD / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_BUILD / "index.html")
