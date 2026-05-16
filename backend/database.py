"""SQLAlchemy engine, ORM models, and session management."""

from sqlalchemy import (
    Column, Integer, Text, Float, ForeignKey,
    create_engine, event,
)
from sqlalchemy.orm import (
    DeclarativeBase, relationship, sessionmaker, Session,
)
from backend.config import settings


# ─── Engine ───────────────────────────────────────────────────────────────────

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)


# Enable SQLite foreign key enforcement
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)


def get_db() -> Session:
    """FastAPI dependency — yields a DB session, auto-closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Base ─────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─── ORM Models ──────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    location = Column(Text)
    contact_info = Column(Text)
    account_status = Column(Text, nullable=False, default="active")

    orders = relationship("Order", back_populates="customer")
    tickets = relationship("Ticket", back_populates="customer")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    category = relationship("Category", back_populates="products")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(Text, nullable=False)
    total_amount = Column(Float, nullable=False)

    customer = relationship("Customer", back_populates="orders")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    department = Column(Text, nullable=False)
    expertise = Column(Text)

    interactions = relationship("Interaction", back_populates="agent")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(Text, nullable=False, default="open")
    priority = Column(Text, nullable=False, default="medium")

    customer = relationship("Customer", back_populates="tickets")
    interactions = relationship("Interaction", back_populates="ticket")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    timestamp = Column(Text, nullable=False)
    notes = Column(Text)

    ticket = relationship("Ticket", back_populates="interactions")
    agent = relationship("Agent", back_populates="interactions")
