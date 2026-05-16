"""Tests for the NL→SQL agent — SQL validation, schema context, and tool definitions."""

import re
from backend.agent.tools import TOOLS
from backend.agent.schema_context import build_schema_context, build_system_prompt
from backend.agent.nl_agent import _validate_sql, _format_tool_result


class TestSqlValidation:
    """Test the SQL safety validation layer."""

    def test_valid_select(self):
        assert _validate_sql("SELECT * FROM customers") is True

    def test_valid_select_with_join(self):
        sql = "SELECT c.name, o.total_amount FROM customers c JOIN orders o ON c.id = o.customer_id"
        assert _validate_sql(sql) is True

    def test_valid_select_with_where(self):
        sql = "SELECT * FROM orders WHERE order_date >= date('now', '-1 month')"
        assert _validate_sql(sql) is True

    def test_reject_insert(self):
        assert _validate_sql("INSERT INTO customers (name) VALUES ('hacker')") is False

    def test_reject_update(self):
        assert _validate_sql("UPDATE customers SET name = 'hacked'") is False

    def test_reject_delete(self):
        assert _validate_sql("DELETE FROM customers WHERE id = 1") is False

    def test_reject_drop(self):
        assert _validate_sql("DROP TABLE customers") is False

    def test_reject_alter(self):
        assert _validate_sql("ALTER TABLE customers ADD COLUMN hacked TEXT") is False

    def test_reject_select_with_embedded_drop(self):
        """Even if it starts with SELECT, embedded mutations should be caught."""
        sql = "SELECT * FROM customers; DROP TABLE customers"
        assert _validate_sql(sql) is False

    def test_empty_string(self):
        assert _validate_sql("") is False

    def test_whitespace_only(self):
        assert _validate_sql("   ") is False


class TestSchemaContext:
    """Test schema introspection and system prompt generation."""

    def test_build_schema_context(self, seeded_engine):
        """Schema context should contain all table names."""
        context = build_schema_context(seeded_engine)
        assert "customers" in context
        assert "orders" in context
        assert "tickets" in context
        assert "agents" in context
        assert "products" in context
        assert "categories" in context
        assert "interactions" in context

    def test_build_schema_includes_columns(self, seeded_engine):
        """Schema context should include column names."""
        context = build_schema_context(seeded_engine)
        assert "email" in context
        assert "total_amount" in context
        assert "customer_id" in context
        assert "priority" in context

    def test_system_prompt_has_rules(self, seeded_engine):
        """System prompt should contain safety rules."""
        prompt = build_system_prompt(seeded_engine)
        assert "SELECT" in prompt
        assert "INSERT" in prompt or "never" in prompt.lower()
        assert "customers" in prompt


class TestToolDefinitions:
    """Verify Claude tool definitions are well-formed."""

    def test_tools_has_run_sql_query(self):
        names = [t["name"] for t in TOOLS]
        assert "run_sql_query" in names

    def test_tool_has_required_fields(self):
        tool = TOOLS[0]
        assert "input_schema" in tool
        assert "sql" in tool["input_schema"]["properties"]
        assert "sql" in tool["input_schema"]["required"]

    def test_tool_description_mentions_select(self):
        tool = TOOLS[0]
        assert "SELECT" in tool["description"]


class TestResultFormatter:
    """Test formatting of SQL results for Claude."""

    def test_format_empty_result(self):
        result = {"success": True, "columns": [], "rows": [], "row_count": 0}
        formatted = _format_tool_result(result)
        assert "0 rows" in formatted

    def test_format_with_rows(self):
        result = {
            "success": True,
            "columns": ["name", "total"],
            "rows": [{"name": "Alice", "total": 199.99}],
            "row_count": 1,
        }
        formatted = _format_tool_result(result)
        assert "Alice" in formatted
        assert "199.99" in formatted
        assert "1 row" in formatted
