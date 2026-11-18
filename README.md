# Sales Dashboard

An interactive sales analytics dashboard built with **PostgreSQL**, **FastAPI**, and **Chart.js**.

Loads customer and order data from Excel files into a database, computes KPIs via SQL, and presents them in a responsive web dashboard with filters.

---

## Quick Start (Docker)

```bash
docker-compose up --build
```

Open **http://localhost:8000** in your browser.

That's it — Docker Compose will:
1. Start PostgreSQL 16
2. Build and start the FastAPI app
3. Auto-create tables, load data, and serve the dashboard

---

## Manual Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 16 (running locally or via Docker)

### Steps

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up PostgreSQL
#    Create a database called 'sales' and set environment variables:
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=sales
set DB_USER=postgres
set DB_PASSWORD=postgres

# 4. Start the application (auto-initializes DB and loads data)
uvicorn backend.main:app --reload --port 8000

# 5. Open http://localhost:8000
```

---

## Architecture

```
Excel files --> load_data.py (pandas) --> PostgreSQL
                                            |- customers (PK)
                                            |- orders (FK -> customers)
                                            '- vw_sales (join view)
                                                 ^
Browser (HTML/JS + Chart.js) <--JSON-- FastAPI --'
   filters -> query params     /api/dashboard?from&to&category&segment&city&status
```

| Layer    | Technology              | Rationale                            |
|----------|-------------------------|--------------------------------------|
| Database | PostgreSQL 16 (Docker)  | Real constraints, views, functions   |
| Loader   | Python + pandas         | Idempotent, type-safe loading        |
| Backend  | FastAPI                 | Validated params, JSON API           |
| Frontend | HTML/CSS/JS + Chart.js  | No build step, easy to run           |
| Tests    | pytest                  | DB, SQL, API, pandas oracle          |
| Packaging| Docker Compose          | One-command setup                    |

---

## API Endpoints

### `GET /api/dashboard`

Query parameters (all optional):
| Parameter | Description            | Example        |
|-----------|------------------------|----------------|
| `from`    | Start date (inclusive) | `2026-01-01`   |
| `to`      | End date (inclusive)    | `2026-06-30`   |
| `category`| Product category       | `Electronics`  |
| `segment` | Customer segment       | `Corporate`    |
| `city`    | City                   | `Mumbai`       |
| `status`  | Order status           | `Completed`    |

### `GET /api/filters`

Returns available filter options for all dropdowns.

---

## Dashboard Features

### KPI Cards
- **Net Revenue** — total `Net_Amount_INR`
- **Total Orders** — count of unique `Order_ID`
- **Unique Customers** — count of unique `Customer_ID` in filtered orders
- **Avg Order Value** — net revenue ÷ non-cancelled orders
- **Repeat Customers** — customers with 2+ non-cancelled orders (bonus)

### Charts
1. **Monthly Revenue Trend** — line chart, all 6 months always shown
2. **Revenue by Category** — doughnut chart
3. **Orders by Status** — doughnut chart (color-coded)
4. **Revenue by Segment** — bar chart
5. **Top 5 Products** — horizontal bar chart (bonus)
6. **Revenue by City** — bar chart

### Filters
- Date range (from/to)
- Product category
- Customer segment
- City
- Order status
- Apply and Reset buttons

---

## Ground-Truth KPIs (No Filters)

| Metric             | Value                |
|--------------------|----------------------|
| Net Revenue        | ₹11,59,206           |
| Total Orders       | 240                  |
| Unique Customers   | 59                   |
| Avg Order Value    | ₹5,682.38            |
| Top Product        | Smart Watch (₹2,74,674) |
| Repeat Customers   | 48 of 54             |

---

## Assumptions

- Revenue uses `Net_Amount_INR`; Cancelled orders contribute ₹0.
- "Total orders" counts all unique `Order_ID`s, any status.
- "Unique customers" counts distinct customers in filtered orders (not the full customers table).
- AOV = total net revenue ÷ non-cancelled orders; shows "—" when count is 0.
- Returned orders remain in data and count toward revenue.
- All metrics respond to all filters simultaneously.
- Indian number format (`en-IN` locale) with ₹ prefix.

---

## Running Tests

```bash
# Pandas oracle tests (no DB required)
pytest tests/test_metrics.py -v

# Full test suite (requires running PostgreSQL)
pytest tests/ -v
```

---

## Tools Used

- **Python 3.11** — backend language
- **FastAPI** — REST API framework
- **PostgreSQL 16** — relational database
- **pandas + openpyxl** — Excel loading and data validation
- **psycopg2** — PostgreSQL driver
- **Chart.js 4** — frontend charting library
- **Docker + Docker Compose** — containerized deployment
- **pytest** — test framework

---

## Project Structure

```
sales-dashboard/
├── db/
│   ├── schema.sql          # Table DDL with constraints
│   └── view.sql            # vw_sales join view
├── backend/
│   ├── main.py             # FastAPI application
│   ├── queries.py          # Parameterised SQL queries
│   └── load_data.py        # Idempotent data loader
├── frontend/
│   ├── index.html          # Dashboard page
│   ├── app.js              # Frontend logic
│   └── styles.css          # Styles
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── test_db.py          # Database tests
│   ├── test_metrics.py     # Metric accuracy tests
│   └── test_api.py         # API tests
├── data/
│   ├── customers.xlsx
│   └── orders.xlsx
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Screenshots

> _Screenshots of the running dashboard would go here._

---

## License

This project was built as a technical assessment submission.
