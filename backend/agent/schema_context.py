"""Runtime schema introspection — builds a compact schema description for Claude's system prompt."""

from sqlalchemy import inspect, Engine


def build_schema_context(engine: Engine) -> str:
    """Introspect the SQLite database and serialize schema as a compact string.

    This ensures Claude always sees the real schema — no stale hardcoded descriptions.
    """
    inspector = inspect(engine)
    sections = []

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)

        # Column definitions
        col_lines = []
        for col in columns:
            nullable = "" if col.get("nullable", True) else " NOT NULL"
            default = f" DEFAULT {col['default']}" if col.get("default") else ""
            col_lines.append(f"    {col['name']} {col['type']}{nullable}{default}")

        # Foreign key constraints
        fk_lines = []
        for fk in foreign_keys:
            src_cols = ", ".join(fk["constrained_columns"])
            ref_table = fk["referred_table"]
            ref_cols = ", ".join(fk["referred_columns"])
            fk_lines.append(f"    FOREIGN KEY ({src_cols}) → {ref_table}({ref_cols})")

        section = f"TABLE {table_name}:\n" + "\n".join(col_lines)
        if fk_lines:
            section += "\n" + "\n".join(fk_lines)

        sections.append(section)

    return "\n\n".join(sections)


# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are a data analyst assistant. You help users query business data using natural language.

You have access to a single SQLite database containing two business domains:

## DATABASE SCHEMA

{schema}

## DOMAIN CONTEXT

**E-Commerce domain:**
- customers: People who buy products
- categories: Product categories (Electronics, Home & Kitchen, Clothing, Books, Sports)
- products: Items for sale, each belonging to a category
- orders: Purchase records with date and total amount

**Customer Support domain:**
- customers: Same table as e-commerce (shared). Fields include contact_info and account_status.
- agents: Support staff with department and expertise
- tickets: Support requests with status (open/in_progress/closed) and priority (low/medium/high)
- interactions: Agent responses on tickets with timestamps and notes

**Cross-domain:** Both domains share the same `customers` table. A customer can have both orders AND tickets. This means cross-domain queries (e.g., "customers who shop but never raised tickets") are simple JOINs or subqueries through customer_id.

## RULES

1. Generate ONLY SELECT statements — never INSERT, UPDATE, DELETE, DROP, or ALTER
2. Use SQLite date functions for date filtering:
   - "last month": WHERE order_date >= date('now', '-1 month')
   - "last 30 days": WHERE order_date >= date('now', '-30 days')
   - Specific dates: WHERE order_date = '2026-05-05'
3. For customer name lookups, use LIKE with % wildcards: WHERE name LIKE '%Alice%'
4. Always use clear column aliases for readability
5. If the question is ambiguous, ask for clarification instead of guessing
6. For aggregate queries, include helpful context (counts, totals, averages)
7. Keep queries efficient — avoid SELECT * when specific columns suffice
8. When presenting results, format them clearly with natural language explanations

## CRITICAL: AVOID CARTESIAN JOINS

NEVER join orders and tickets in the same query like this (it multiplies rows and produces wrong totals):
```
-- WRONG: creates cartesian product
SELECT c.name, SUM(o.total_amount), COUNT(t.id)
FROM customers c
JOIN tickets t ON c.id = t.customer_id
JOIN orders o ON c.id = o.customer_id
GROUP BY c.id
```

Instead, use subqueries or aggregate separately:
```
-- CORRECT: subqueries avoid row multiplication
SELECT c.name,
       (SELECT COALESCE(SUM(o.total_amount), 0) FROM orders o WHERE o.customer_id = c.id) AS total_order_value,
       (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) AS order_count,
       (SELECT COUNT(*) FROM tickets t WHERE t.customer_id = c.id) AS ticket_count
FROM customers c
WHERE c.id IN (SELECT customer_id FROM tickets)
ORDER BY total_order_value DESC
```

This is essential when a customer has BOTH multiple orders AND multiple tickets — a direct JOIN produces N×M rows per customer."""


def build_system_prompt(engine: Engine) -> str:
    """Build the full system prompt with live schema context."""
    schema = build_schema_context(engine)
    return SYSTEM_PROMPT_TEMPLATE.format(schema=schema)
