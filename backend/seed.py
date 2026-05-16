"""Seed script — creates schema and loads CSV sample data into the unified SQLite DB.

Idempotent: safe to run multiple times. Drops and recreates all tables on each run.

Usage:
    python seed.py              (from project root)
    python -m backend.seed      (as module)
"""

import csv
import sys
from pathlib import Path

import structlog

from backend.config import settings, setup_logging, DATA_DIR, SQL_DIR
from backend.database import engine, SessionLocal, Base
from backend.database import (
    Customer, Category, Product, Order,
    Agent, Ticket, Interaction,
)


log = structlog.get_logger()


def _read_csv(filepath: Path) -> list[dict]:
    """Read a CSV file and return a list of row dicts."""
    with open(filepath, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _merge_customers(ecom_rows: list[dict], support_rows: list[dict]) -> list[Customer]:
    """Merge e-commerce and support customers by email into unified Customer records.

    Strategy:
    - E-commerce customers keep their original IDs (1–13)
    - Support-only customers (14, 15) are added with their original IDs
    - Overlapping customers (same email) get fields merged from both sources
    """
    # Index support customers by email for quick lookup
    support_by_email = {row["email"]: row for row in support_rows}
    seen_emails = set()
    customers = []

    # Process e-commerce customers first (IDs 1–13)
    for row in ecom_rows:
        email = row["email"]
        seen_emails.add(email)

        support_row = support_by_email.get(email, {})
        customers.append(Customer(
            id=int(row["id"]),
            name=row["name"],
            email=email,
            location=row.get("location"),
            contact_info=support_row.get("contact_info"),
            account_status=support_row.get("account_status", "active"),
        ))

    # Add support-only customers (not in e-commerce)
    for row in support_rows:
        if row["email"] not in seen_emails:
            customers.append(Customer(
                id=int(row["id"]),
                name=row["name"],
                email=row["email"],
                location=None,
                contact_info=row.get("contact_info"),
                account_status=row.get("account_status", "active"),
            ))

    return customers


def seed() -> None:
    """Drop all tables, recreate schema, and load CSV data."""
    setup_logging()
    log.info("seed.start", database_url=settings.database_url)

    # Drop and recreate all tables
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    log.info("seed.schema_created")

    # Also run the raw SQL schema for indexes
    schema_sql = (SQL_DIR / "schema.sql").read_text(encoding="utf-8")
    # Extract only CREATE INDEX statements (tables already created by SQLAlchemy)
    index_statements = [
        stmt.strip()
        for stmt in schema_sql.split(";")
        if stmt.strip().upper().startswith("CREATE INDEX")
    ]
    with engine.connect() as conn:
        for stmt in index_statements:
            conn.execute(conn.connection.cursor().execute(stmt) if False else __import__("sqlalchemy").text(stmt))
        conn.commit()
    log.info("seed.indexes_created", count=len(index_statements))

    # Load data
    db = SessionLocal()
    try:
        # ── Customers (merged from both domains) ──
        ecom_customers = _read_csv(DATA_DIR / "ecommerce" / "ecom_customers.csv")
        support_customers = _read_csv(DATA_DIR / "support" / "support_customers.csv")
        customers = _merge_customers(ecom_customers, support_customers)
        db.add_all(customers)
        db.flush()
        log.info("seed.loaded", table="customers", rows=len(customers))

        # ── Categories ──
        categories = [
            Category(id=int(r["id"]), name=r["name"], description=r.get("description"))
            for r in _read_csv(DATA_DIR / "ecommerce" / "ecom_categories.csv")
        ]
        db.add_all(categories)
        db.flush()
        log.info("seed.loaded", table="categories", rows=len(categories))

        # ── Products ──
        products = [
            Product(
                id=int(r["id"]),
                name=r["name"],
                description=r.get("description"),
                price=float(r["price"]),
                category_id=int(r["category_id"]),
            )
            for r in _read_csv(DATA_DIR / "ecommerce" / "ecom_products.csv")
        ]
        db.add_all(products)
        db.flush()
        log.info("seed.loaded", table="products", rows=len(products))

        # ── Orders ──
        # customer_id maps directly (ecom IDs 1-13 = unified IDs 1-13)
        orders = [
            Order(
                id=int(r["id"]),
                customer_id=int(r["customer_id"]),
                order_date=r["order_date"],
                total_amount=float(r["total_amount"]),
            )
            for r in _read_csv(DATA_DIR / "ecommerce" / "ecom_orders.csv")
        ]
        db.add_all(orders)
        db.flush()
        log.info("seed.loaded", table="orders", rows=len(orders))

        # ── Agents ──
        agents = [
            Agent(
                id=int(r["id"]),
                name=r["name"],
                department=r["department"],
                expertise=r.get("expertise"),
            )
            for r in _read_csv(DATA_DIR / "support" / "support_agents.csv")
        ]
        db.add_all(agents)
        db.flush()
        log.info("seed.loaded", table="agents", rows=len(agents))

        # ── Tickets ──
        # customer_id maps directly (support IDs 1-10,14,15 = unified IDs)
        tickets = [
            Ticket(
                id=int(r["id"]),
                title=r["title"],
                description=r.get("description"),
                customer_id=int(r["customer_id"]),
                status=r["status"],
                priority=r["priority"],
            )
            for r in _read_csv(DATA_DIR / "support" / "support_tickets.csv")
        ]
        db.add_all(tickets)
        db.flush()
        log.info("seed.loaded", table="tickets", rows=len(tickets))

        # ── Interactions ──
        interactions = [
            Interaction(
                id=int(r["id"]),
                ticket_id=int(r["ticket_id"]),
                agent_id=int(r["agent_id"]),
                timestamp=r["timestamp"],
                notes=r.get("notes"),
            )
            for r in _read_csv(DATA_DIR / "support" / "support_interactions.csv")
        ]
        db.add_all(interactions)
        db.flush()
        log.info("seed.loaded", table="interactions", rows=len(interactions))

        db.commit()
        log.info("seed.complete", total_customers=len(customers))

    except Exception:
        db.rollback()
        log.exception("seed.failed")
        raise
    finally:
        db.close()


# ─── Summary ──────────────────────────────────────────────────────────────────

def print_summary() -> None:
    """Print a human-readable summary of seeded data."""
    db = SessionLocal()
    try:
        counts = {
            "customers": db.query(Customer).count(),
            "categories": db.query(Category).count(),
            "products": db.query(Product).count(),
            "orders": db.query(Order).count(),
            "agents": db.query(Agent).count(),
            "tickets": db.query(Ticket).count(),
            "interactions": db.query(Interaction).count(),
        }
        print("\n✓ Database seeded successfully!")
        print(f"  Database: {settings.database_url}")
        for table, count in counts.items():
            print(f"  → {table}: {count} rows")
        print()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print_summary()
