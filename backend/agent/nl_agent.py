"""Core NL→SQL agent — orchestrates LLM tool-calling to translate
natural language into SQL, execute it, and return human-readable answers.

Supports both Anthropic (Claude) and OpenAI (GPT) providers.
Includes in-memory conversation history for follow-up questions.
"""

import re
import uuid
import json
from typing import Any

import structlog
from sqlalchemy import text, create_engine

from backend.config import settings
from backend.agent.tools import TOOLS, OPENAI_TOOLS
from backend.agent.schema_context import build_system_prompt

log = structlog.get_logger()

# ─── Conversation Store ───────────────────────────────────────────────────────
# Simple in-memory dict: conversation_id → list of message dicts

conversation_store: dict[str, list[dict]] = {}


# ─── SQL Safety ───────────────────────────────────────────────────────────────

_FORBIDDEN_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|ATTACH|DETACH)\b",
    re.IGNORECASE,
)


def _validate_sql(sql: str) -> bool:
    """Return True if the SQL is a safe read-only SELECT."""
    stripped = sql.strip().rstrip(";")
    if not stripped.upper().startswith("SELECT"):
        return False
    if _FORBIDDEN_PATTERNS.search(stripped):
        return False
    return True


# ─── SQL Execution ────────────────────────────────────────────────────────────

def _execute_sql(sql: str, db_url: str) -> dict[str, Any]:
    """Execute a read-only SQL query and return results."""
    ro_url = db_url
    if "sqlite" in db_url and "?mode=ro" not in db_url:
        ro_url = db_url.replace("sqlite:///", "sqlite:///file:", 1)
        if "?" in ro_url:
            ro_url += "&mode=ro"
        else:
            ro_url += "?mode=ro&uri=true"

    try:
        ro_engine = create_engine(ro_url, connect_args={"check_same_thread": False})
        with ro_engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return {"success": True, "columns": columns, "rows": rows, "row_count": len(rows)}
    except Exception as e:
        log.error("sql.execution_failed", sql=sql, error=str(e))
        return {"success": False, "error": str(e)}


def _format_tool_result(result: dict) -> str:
    """Format SQL results as a compact string for the LLM to interpret."""
    rows = result["rows"]
    if not rows:
        return "Query returned 0 rows."

    columns = result["columns"]
    lines = [f"Query returned {result['row_count']} row(s)."]
    lines.append("Columns: " + ", ".join(columns))
    lines.append("---")

    for row in rows[:50]:
        line = " | ".join(str(row.get(col, "")) for col in columns)
        lines.append(line)

    if result["row_count"] > 50:
        lines.append(f"... and {result['row_count'] - 50} more rows (truncated)")

    return "\n".join(lines)


# ─── Tool Execution (shared) ─────────────────────────────────────────────────

def _handle_tool_call(sql: str, db_url: str) -> tuple[str, list[dict] | None, bool]:
    """Validate and execute a SQL tool call. Returns (result_text, data, is_error)."""
    if not _validate_sql(sql):
        return "ERROR: Only SELECT queries are allowed.", None, True

    result = _execute_sql(sql, db_url)
    if result["success"]:
        log.info("agent.query_result", rows=result["row_count"])
        return _format_tool_result(result), result["rows"], False
    else:
        return f"SQL Error: {result['error']}. Please fix the query and try again.", None, True


# ═══════════════════════════════════════════════════════════════════════════════
# ANTHROPIC PROVIDER
# ═══════════════════════════════════════════════════════════════════════════════

class AnthropicAgent:
    """NL→SQL agent using Claude via Anthropic API."""

    def __init__(self, system_prompt: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.system_prompt = system_prompt
        self.model = settings.claude_model
        log.info("agent.initialized", provider="anthropic", model=self.model)

    def call(self, history: list[dict]) -> dict[str, Any]:
        sql_used = None
        data = None

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            tools=TOOLS,
            messages=history,
        )

        while response.stop_reason == "tool_use":
            tool_block = next(b for b in response.content if b.type == "tool_use")
            tool_input = tool_block.input
            sql = tool_input.get("sql", "")
            sql_used = sql

            log.info("agent.tool_call", tool=tool_block.name, sql=sql[:100])

            result_text, result_data, is_error = _handle_tool_call(sql, settings.database_url)
            if result_data is not None:
                data = result_data

            tool_result = {
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": result_text,
                "is_error": is_error,
            }

            history.append({"role": "assistant", "content": response.content})
            history.append({"role": "user", "content": [tool_result]})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=TOOLS,
                messages=history,
            )

        # Extract final text
        answer = "".join(b.text for b in response.content if hasattr(b, "text"))
        history.append({"role": "assistant", "content": answer})

        return {"answer": answer, "data": data, "sql_used": sql_used}


# ═══════════════════════════════════════════════════════════════════════════════
# OPENAI PROVIDER
# ═══════════════════════════════════════════════════════════════════════════════

class OpenAIAgent:
    """NL→SQL agent using GPT via OpenAI API."""

    def __init__(self, system_prompt: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.system_prompt = system_prompt
        self.model = settings.openai_model
        log.info("agent.initialized", provider="openai", model=self.model)

    def call(self, history: list[dict]) -> dict[str, Any]:
        sql_used = None
        data = None

        # OpenAI expects system message in the messages array
        messages = [{"role": "system", "content": self.system_prompt}] + history

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=OPENAI_TOOLS,
            max_tokens=4096,
        )

        msg = response.choices[0].message

        while msg.tool_calls:
            # Add assistant message with tool calls
            history.append(msg.model_dump(exclude_none=True))

            for tool_call in msg.tool_calls:
                args = json.loads(tool_call.function.arguments)
                sql = args.get("sql", "")
                sql_used = sql

                log.info("agent.tool_call", tool=tool_call.function.name, sql=sql[:100])

                result_text, result_data, is_error = _handle_tool_call(sql, settings.database_url)
                if result_data is not None:
                    data = result_data

                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_text,
                })

            messages = [{"role": "system", "content": self.system_prompt}] + history
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=OPENAI_TOOLS,
                max_tokens=4096,
            )
            msg = response.choices[0].message

        answer = msg.content or ""
        history.append({"role": "assistant", "content": answer})

        return {"answer": answer, "data": data, "sql_used": sql_used}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN AGENT (provider-agnostic wrapper)
# ═══════════════════════════════════════════════════════════════════════════════

class NLAgent:
    """Natural language to SQL agent — delegates to the configured LLM provider."""

    def __init__(self, db_engine):
        system_prompt = build_system_prompt(db_engine)
        self.max_history = settings.max_history
        self.provider = settings.llm_provider.lower()

        if self.provider == "openai":
            self._agent = OpenAIAgent(system_prompt)
        else:
            self._agent = AnthropicAgent(system_prompt)

    def process(self, message: str, conversation_id: str | None = None) -> dict[str, Any]:
        """Process a natural language query and return a structured response."""
        conv_id = conversation_id or str(uuid.uuid4())

        if conv_id not in conversation_store:
            conversation_store[conv_id] = []
        history = conversation_store[conv_id]

        history.append({"role": "user", "content": message})

        if len(history) > self.max_history:
            history = history[-self.max_history:]
            conversation_store[conv_id] = history

        log.info("agent.processing", provider=self.provider, conversation_id=conv_id, message=message[:100])

        try:
            result = self._agent.call(history)
            result["conversation_id"] = conv_id
            return result

        except Exception as e:
            log.exception("agent.error", error=str(e))
            return {
                "answer": f"Something went wrong: {str(e)}. Please try again.",
                "data": None,
                "sql_used": None,
                "conversation_id": conv_id,
            }
