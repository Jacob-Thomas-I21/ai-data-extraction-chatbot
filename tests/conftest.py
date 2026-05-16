"""Shared test fixtures — seeded in-memory database for fast, isolated tests."""

import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import Base, Customer, Category, Product, Order, Agent, Ticket, Interaction


@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def seeded_engine(test_engine):
    """Seed the test database with sample data and return the engine."""
    Session = sessionmaker(bind=test_engine)
    db = Session()

    # ── Customers (unified: 15 unique) ──
    customers = [
        Customer(id=1, name="Alice Chen", email="alice.chen@example.com", location="London, UK", contact_info="+44 20 7946 0001", account_status="active"),
        Customer(id=2, name="Ben Okafor", email="ben.okafor@example.com", location="Manchester, UK", contact_info="+44 161 555 0002", account_status="active"),
        Customer(id=3, name="Carla Rossi", email="carla.rossi@example.com", location="Milan, Italy", contact_info="+39 02 555 0003", account_status="active"),
        Customer(id=4, name="Dmitri Volkov", email="dmitri.volkov@example.com", location="Berlin, Germany", contact_info="+49 30 555 0004", account_status="active"),
        Customer(id=5, name="Elena Marquez", email="elena.marquez@example.com", location="Madrid, Spain", contact_info="+34 91 555 0005", account_status="suspended"),
        Customer(id=6, name="Farah Haddad", email="farah.haddad@example.com", location="Dubai, UAE", contact_info="+971 4 555 0006", account_status="active"),
        Customer(id=7, name="George Smith", email="george.smith@example.com", location="London, UK", contact_info="+44 20 7946 0007", account_status="active"),
        Customer(id=8, name="Hina Patel", email="hina.patel@example.com", location="Mumbai, India", contact_info="+91 22 555 0008", account_status="active"),
        Customer(id=9, name="Ivan Petrov", email="ivan.petrov@example.com", location="Moscow, Russia", contact_info="+7 495 555 0009", account_status="active"),
        Customer(id=10, name="Julia Becker", email="julia.becker@example.com", location="Vienna, Austria", contact_info="+43 1 555 0010", account_status="active"),
        Customer(id=11, name="Kojo Mensah", email="kojo.mensah@example.com", location="Accra, Ghana", account_status="active"),
        Customer(id=12, name="Lina Andersson", email="lina.andersson@example.com", location="Stockholm, Sweden", account_status="active"),
        Customer(id=13, name="Mateo Silva", email="mateo.silva@example.com", location="Lisbon, Portugal", account_status="active"),
        Customer(id=14, name="Nadia Khoury", email="nadia.khoury@example.com", contact_info="+961 1 555 0014", account_status="active"),
        Customer(id=15, name="Oscar Nilsen", email="oscar.nilsen@example.com", contact_info="+47 22 555 0015", account_status="active"),
    ]
    db.add_all(customers)

    # ── Categories ──
    categories = [
        Category(id=1, name="Electronics", description="Phones, laptops, headphones, and accessories"),
        Category(id=2, name="Home & Kitchen", description="Cookware, appliances, and household items"),
        Category(id=3, name="Clothing", description="Apparel for men, women, and children"),
        Category(id=4, name="Books", description="Fiction, non-fiction, and reference"),
        Category(id=5, name="Sports", description="Equipment and apparel for outdoor and indoor sports"),
    ]
    db.add_all(categories)

    # ── Products (subset for testing) ──
    products = [
        Product(id=1, name="Wireless Headphones", description="Over-ear noise-cancelling", price=199.99, category_id=1),
        Product(id=2, name="Smartphone X12", description="6.5 inch display", price=699.00, category_id=1),
        Product(id=10, name="Cotton T-Shirt", description="Plain cotton crew-neck", price=19.99, category_id=3),
    ]
    db.add_all(products)

    # ── Orders ──
    orders = [
        Order(id=101, customer_id=1, order_date="2026-05-05", total_amount=199.99),
        Order(id=102, customer_id=1, order_date="2026-04-26", total_amount=59.00),
        Order(id=103, customer_id=2, order_date="2026-05-03", total_amount=449.00),
        Order(id=112, customer_id=1, order_date="2026-04-10", total_amount=24.50),
        Order(id=109, customer_id=11, order_date="2026-04-28", total_amount=110.00),
    ]
    db.add_all(orders)

    # ── Agents ──
    agents = [
        Agent(id=1, name="Priya Sharma", department="Technical", expertise="Hardware troubleshooting, returns"),
        Agent(id=2, name="Tom Walker", department="Billing", expertise="Refunds, invoicing, payment disputes"),
    ]
    db.add_all(agents)

    # ── Tickets ──
    tickets = [
        Ticket(id=201, title="Headphones won't pair", description="Bluetooth pairing fails", customer_id=1, status="open", priority="high"),
        Ticket(id=202, title="Refund for damaged smartphone", description="Phone arrived cracked", customer_id=2, status="open", priority="high"),
        Ticket(id=204, title="Wrong size t-shirt", description="Ordered medium, received small", customer_id=4, status="closed", priority="low"),
    ]
    db.add_all(tickets)

    # ── Interactions ──
    interactions = [
        Interaction(id=301, ticket_id=201, agent_id=1, timestamp="2026-05-05 00:00:00", notes="Asked customer for phone model"),
        Interaction(id=303, ticket_id=202, agent_id=2, timestamp="2026-05-04 00:00:00", notes="Logged refund request"),
    ]
    db.add_all(interactions)

    db.commit()
    db.close()

    return test_engine


@pytest.fixture
def db_session(seeded_engine):
    """Per-test database session."""
    Session = sessionmaker(bind=seeded_engine)
    session = Session()
    yield session
    session.close()
