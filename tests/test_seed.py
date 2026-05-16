"""Tests for database schema creation and data seeding."""

from backend.database import Customer, Category, Product, Order, Agent, Ticket, Interaction


class TestSchemaIntegrity:
    """Verify that the schema is created correctly and data is loaded."""

    def test_customer_count(self, db_session):
        """15 unique customers after merging ecom (13) + support-only (2)."""
        assert db_session.query(Customer).count() == 15

    def test_category_count(self, db_session):
        assert db_session.query(Category).count() == 5

    def test_customer_fields_merged(self, db_session):
        """Alice Chen should have fields from both ecom and support CSVs."""
        alice = db_session.query(Customer).filter_by(name="Alice Chen").first()
        assert alice is not None
        assert alice.email == "alice.chen@example.com"
        assert alice.location == "London, UK"          # from ecom
        assert alice.contact_info is not None            # from support
        assert alice.account_status == "active"          # from support

    def test_ecom_only_customer(self, db_session):
        """Kojo Mensah is ecom-only — no contact_info."""
        kojo = db_session.query(Customer).filter_by(name="Kojo Mensah").first()
        assert kojo is not None
        assert kojo.location == "Accra, Ghana"
        assert kojo.contact_info is None

    def test_support_only_customer(self, db_session):
        """Nadia Khoury is support-only — no location."""
        nadia = db_session.query(Customer).filter_by(name="Nadia Khoury").first()
        assert nadia is not None
        assert nadia.location is None
        assert nadia.contact_info is not None

    def test_order_foreign_key(self, db_session):
        """Orders should reference valid customers."""
        order = db_session.query(Order).filter_by(id=101).first()
        assert order is not None
        assert order.customer.name == "Alice Chen"

    def test_ticket_foreign_key(self, db_session):
        """Tickets should reference valid customers."""
        ticket = db_session.query(Ticket).filter_by(id=201).first()
        assert ticket is not None
        assert ticket.customer.name == "Alice Chen"

    def test_interaction_relationships(self, db_session):
        """Interactions link to both tickets and agents."""
        interaction = db_session.query(Interaction).filter_by(id=301).first()
        assert interaction is not None
        assert interaction.ticket.title == "Headphones won't pair"
        assert interaction.agent.name == "Priya Sharma"
