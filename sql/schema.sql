-- AI Data Extraction Chatbot — Unified Database Schema
-- Both e-commerce and customer support domains share a single customers table.

-- ═══════════════════════════════════════════════════════════
-- SHARED
-- ═══════════════════════════════════════════════════════════

DROP TABLE IF EXISTS interactions;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS agents;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE,
    location        TEXT,
    contact_info    TEXT,
    account_status  TEXT    NOT NULL DEFAULT 'active'
);

-- ═══════════════════════════════════════════════════════════
-- E-COMMERCE DOMAIN
-- ═══════════════════════════════════════════════════════════

CREATE TABLE categories (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    description TEXT
);

CREATE TABLE products (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    description TEXT,
    price       REAL    NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE orders (
    id           INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL,
    order_date   TEXT    NOT NULL,   -- ISO 8601 date
    total_amount REAL    NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- ═══════════════════════════════════════════════════════════
-- CUSTOMER SUPPORT DOMAIN
-- ═══════════════════════════════════════════════════════════

CREATE TABLE agents (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    department TEXT NOT NULL,
    expertise  TEXT
);

CREATE TABLE tickets (
    id          INTEGER PRIMARY KEY,
    title       TEXT    NOT NULL,
    description TEXT,
    customer_id INTEGER NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'open',    -- open | in_progress | closed
    priority    TEXT    NOT NULL DEFAULT 'medium',   -- low | medium | high
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE interactions (
    id        INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL,
    agent_id  INTEGER NOT NULL,
    timestamp TEXT    NOT NULL,   -- ISO 8601 datetime
    notes     TEXT,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (agent_id)  REFERENCES agents(id)
);

-- ═══════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════

CREATE INDEX idx_orders_customer     ON orders(customer_id);
CREATE INDEX idx_orders_date         ON orders(order_date);
CREATE INDEX idx_products_category   ON products(category_id);
CREATE INDEX idx_tickets_customer    ON tickets(customer_id);
CREATE INDEX idx_tickets_status      ON tickets(status);
CREATE INDEX idx_interactions_ticket ON interactions(ticket_id);
