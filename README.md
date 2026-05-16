# AI Data Extraction Chatbot

An AI-powered chatbot that lets users query structured e-commerce and customer support data using natural language. Built with Python, FastAPI, SQLite, Claude AI, and React.

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│   React UI      │────▶│   FastAPI API     │────▶│  Claude AI   │
│   (Vite)        │◀────│   /api/chat       │◀────│  (Sonnet)    │
└─────────────────┘     └──────┬───────────┘     └──────────────┘
                               │                        │
                               │                   tool_use:
                               │                  run_sql_query
                               ▼                        │
                        ┌──────────────┐                │
                        │   SQLite DB  │◀───────────────┘
                        │  (unified)   │
                        └──────────────┘
```

**How it works:**

1. User asks a question in plain English
2. FastAPI sends the question + database schema to Claude
3. Claude generates a SQL query via tool-calling (`run_sql_query`)
4. Backend validates the SQL (read-only) and executes it
5. Results are sent back to Claude, which writes a natural language answer
6. The answer (with optional SQL preview) is displayed in the React chat UI

**Key design decisions:**

- **Single unified database** — Both e-commerce and support domains share one `customers` table, enabling cross-domain queries via simple JOINs
- **Schema introspection** — The database schema is introspected at startup and injected into Claude's system prompt, so the LLM never hallucinates column names
- **Tool-calling** — Claude uses native tool-calling (not JSON mode) for reliable SQL generation
- **Read-only safety** — SQL is validated against mutation patterns AND executed on a read-only DB connection

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** (for the React frontend)
- **Anthropic API key** ([console.anthropic.com](https://console.anthropic.com))

## Setup & Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd ai-data-extractor
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 4. Seed the database

```bash
python seed.py
```

Expected output:
```
✓ Database seeded successfully!
  Database: sqlite:///./data.db
  → customers: 15 rows
  → categories: 5 rows
  → products: 20 rows
  → orders: 25 rows
  → agents: 6 rows
  → tickets: 15 rows
  → interactions: 19 rows
```

### 5. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 6. Start the frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

The app will be available at **http://localhost:5173**

## API Documentation

Interactive API docs available at **http://localhost:8000/docs** (Swagger UI).

### POST /api/chat

Send a natural language query.

**Request:**
```json
{
  "message": "Show me all orders from Alice Chen",
  "conversation_id": "optional-uuid-for-follow-ups"
}
```

**Response:**
```json
{
  "answer": "Alice Chen has placed 3 orders:\n\n| Order ID | Date | Amount |\n|---|---|---|\n| 101 | 2026-05-05 | £199.99 |\n| 102 | 2026-04-26 | £59.00 |\n| 112 | 2026-04-10 | £24.50 |\n\nTotal: £283.49",
  "data": [
    {"id": 101, "order_date": "2026-05-05", "total_amount": 199.99},
    {"id": 102, "order_date": "2026-04-26", "total_amount": 59.00},
    {"id": 112, "order_date": "2026-04-10", "total_amount": 24.50}
  ],
  "sql_used": "SELECT o.id, o.order_date, o.total_amount FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.name LIKE '%Alice%'",
  "conversation_id": "abc-123"
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "tables": ["customers", "categories", "products", "orders", "agents", "tickets", "interactions"]
}
```

## Example Queries

| Query | What it tests |
|---|---|
| "Show me all orders from Alice Chen" | Single-domain e-commerce lookup |
| "List all open support tickets" | Single-domain support filter |
| "What is the total order value for each customer who has opened support tickets?" | Cross-domain aggregation |
| "Find customers who made purchases but never raised support tickets" | Cross-domain exclusion (NOT EXISTS) |
| "Show me high priority tickets and which agents are handling them" | Multi-table JOIN |
| "What are the top 5 most expensive products?" | Simple aggregation + ordering |
| "How many orders were placed last month?" | Date filtering |
| "Show me their tickets too" (follow-up) | Conversation context |

## Database Schema

7 tables in a single SQLite database:

```
customers ──┬── orders
             └── tickets ── interactions
                               └── agents
categories ── products
```

- **customers** — Shared across domains (15 records). Linked by `customer_id`.
- **categories** — Product categories (5)
- **products** — E-commerce products (20)
- **orders** — Purchase records (25)
- **agents** — Support staff (6)
- **tickets** — Support requests (15)
- **interactions** — Agent responses on tickets (19)

See [sql/schema.sql](sql/schema.sql) for the full DDL.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agent.py -v

# Run with coverage
pytest tests/ -v --tb=short
```

## Project Structure

```
ai-data-extractor/
├── data/                      # Raw CSV sample data
├── sql/schema.sql             # Database DDL
├── backend/
│   ├── main.py                # FastAPI app + routes
│   ├── config.py              # Settings + schemas + logging
│   ├── database.py            # SQLAlchemy engine + models
│   ├── seed.py                # Database seeding
│   └── agent/
│       ├── nl_agent.py        # Claude NL→SQL pipeline
│       ├── schema_context.py  # DB introspection → prompt
│       └── tools.py           # Claude tool definitions
├── frontend/                  # React 18 + Vite
├── tests/                     # pytest test suite
├── seed.py                    # Convenience seed script
└── README.md
```

## Known Limitations

- **Conversation history is in-memory** — restarting the server clears all conversation context. For production, this would use Redis or a database.
- **No authentication** — the API is open. For production, add API key or OAuth middleware.
- **Single LLM provider** — depends on Anthropic's API availability. Could add fallback to OpenAI.
- **No pagination** — large result sets are truncated at 50 rows in the tool response to Claude.
- **SQLite limitations** — no concurrent write support. For production, use PostgreSQL.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI |
| Database | SQLite + SQLAlchemy 2.0 |
| AI/NLP | Claude Sonnet (Anthropic) |
| Frontend | React 18 + Vite |
| Testing | pytest |
| Logging | structlog |
