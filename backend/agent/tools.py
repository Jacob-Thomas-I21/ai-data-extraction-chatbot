"""Tool definitions for LLM providers.

TOOLS         — Anthropic format (used by Claude)
OPENAI_TOOLS  — OpenAI format (used by GPT and Grok)
"""

# ─── Anthropic Format ─────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "run_sql_query",
        "description": (
            "Execute a read-only SQL SELECT query against the SQLite database. "
            "Use this tool to look up data about e-commerce customers, orders, "
            "products, categories, support tickets, agents, and interactions. "
            "All data is in a single database with a shared 'customers' table. "
            "Only SELECT statements are allowed — never use INSERT, UPDATE, DELETE, or DROP."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": (
                        "A valid SQLite SELECT statement. Use standard SQL syntax. "
                        "For date filtering use SQLite's date() function, e.g. "
                        "date('now', '-1 month'). For name lookups use LIKE with "
                        "% wildcards for partial matching."
                    ),
                },
                "explanation": {
                    "type": "string",
                    "description": "Brief explanation of what this query does and why.",
                },
            },
            "required": ["sql", "explanation"],
        },
    }
]

# ─── OpenAI Format ────────────────────────────────────────────────────────────

OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": (
                "Execute a read-only SQL SELECT query against the SQLite database. "
                "Use this tool to look up data about e-commerce customers, orders, "
                "products, categories, support tickets, agents, and interactions. "
                "All data is in a single database with a shared 'customers' table. "
                "Only SELECT statements are allowed — never use INSERT, UPDATE, DELETE, or DROP."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": (
                            "A valid SQLite SELECT statement. Use standard SQL syntax. "
                            "For date filtering use SQLite's date() function, e.g. "
                            "date('now', '-1 month'). For name lookups use LIKE with "
                            "% wildcards for partial matching."
                        ),
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Brief explanation of what this query does and why.",
                    },
                },
                "required": ["sql", "explanation"],
            },
        },
    }
]
