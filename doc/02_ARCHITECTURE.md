# Architecture

## Stack

| Layer | Choice | Why |
|---|---|---|
| Database | PostgreSQL 16 (Docker) | Real constraints, views, `generate_series` |
| Loader | Python + pandas + psycopg | Idempotent, typed loading |
| Backend | FastAPI | Validated query params, JSON API |
| Frontend | HTML/CSS/JS + Chart.js (served by FastAPI) | No build step, easy to run |
| Tests | pytest | DB, SQL, API checks |
| Packaging | Docker Compose | One command setup (bonus) |

## Data flow

```
Excel files --> load_data.py (pandas, idempotent) --> PostgreSQL
                                                      |- customers (PK)
                                                      |- orders (FK -> customers)
                                                      '- vw_sales (join view)
                                                           ^
Browser (HTML/JS + Chart.js) <--JSON-- FastAPI ------------'
   filters -> query params     /api/dashboard?from&to&category&segment&city&status
```

## Repository layout

```
sales-dashboard/
|- db/         schema.sql, view.sql
|- backend/    main.py, queries.py, load_data.py
|- frontend/   index.html, app.js, styles.css
|- tests/      test_db.py, test_metrics.py, test_api.py
|- data/       customers.xlsx, orders.xlsx
|- docker-compose.yml
'- README.md
```

## Database schema (design)

```sql
CREATE TABLE customers (
  customer_id         VARCHAR(10) PRIMARY KEY,
  customer_name       VARCHAR(100) NOT NULL,
  email               VARCHAR(150) NOT NULL,
  city                VARCHAR(50)  NOT NULL,
  state               VARCHAR(50)  NOT NULL,
  customer_segment    VARCHAR(30)  NOT NULL,
  join_date           DATE         NOT NULL,
  acquisition_channel VARCHAR(30)  NOT NULL
);

CREATE TABLE orders (
  order_id        VARCHAR(10) PRIMARY KEY,
  customer_id     VARCHAR(10) NOT NULL REFERENCES customers(customer_id),
  order_date      DATE NOT NULL,
  product_id      VARCHAR(10) NOT NULL,
  product_name    VARCHAR(100) NOT NULL,
  category        VARCHAR(50)  NOT NULL,
  quantity        INT NOT NULL CHECK (quantity > 0),
  unit_price_inr  NUMERIC(12,2) NOT NULL CHECK (unit_price_inr >= 0),
  discount_rate   NUMERIC(4,3)  NOT NULL CHECK (discount_rate BETWEEN 0 AND 1),
  net_amount_inr  NUMERIC(12,2) NOT NULL CHECK (net_amount_inr >= 0),
  payment_method  VARCHAR(30) NOT NULL,
  order_status    VARCHAR(20) NOT NULL
                  CHECK (order_status IN ('Completed','Returned','Cancelled'))
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date     ON orders(order_date);
CREATE INDEX idx_orders_status   ON orders(order_status);
CREATE INDEX idx_orders_category ON orders(category);
```

## Join view

```sql
CREATE OR REPLACE VIEW vw_sales AS
SELECT o.*, c.customer_name, c.email, c.city, c.state,
       c.customer_segment, c.join_date, c.acquisition_channel
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id;
```

## Metric SQL (all driven by filtered `vw_sales`)

```sql
-- KPIs
SELECT SUM(net_amount_inr)                                   AS net_revenue,
       COUNT(DISTINCT order_id)                              AS total_orders,
       COUNT(DISTINCT customer_id)                           AS unique_customers,
       SUM(net_amount_inr) /
         NULLIF(COUNT(DISTINCT order_id)
                FILTER (WHERE order_status <> 'Cancelled'),0) AS avg_order_value
FROM vw_sales WHERE <filters>;
```

Other queries:
- **Monthly trend:** `generate_series` of months LEFT JOINed to the aggregate, so empty months appear as 0.
- **By category and by segment/city:** `GROUP BY` with `SUM(net_amount_inr)`.
- **Status chart:** `COUNT(DISTINCT order_id) GROUP BY order_status`.
- **Top 5 products:** `GROUP BY product_name ORDER BY SUM DESC LIMIT 5`.
- **Repeat customers:** customers with 2+ non-cancelled orders.

## API contract

`GET /api/dashboard?from=YYYY-MM-DD&to=YYYY-MM-DD&category=&segment=&city=&status=`

```json
{
  "kpis": {"net_revenue": 0, "total_orders": 0, "unique_customers": 0,
           "avg_order_value": null, "repeat_customers": 0},
  "monthly": [{"month": "2026-01", "revenue": 0}],
  "by_category": [{"label": "", "revenue": 0}],
  "by_segment": [],
  "by_city": [],
  "by_status": [{"label": "", "orders": 0}],
  "top_products": []
}
```

Also `GET /api/filters` returns the options for the dropdowns.

## Key design decisions

- **One view, one endpoint:** the frontend does no arithmetic, so numbers cannot drift from SQL.
- **Parameterised queries only:** no string-built SQL.
- **Idempotent loader:** truncate and reload inside a transaction, or `INSERT ... ON CONFLICT`.
- **Constraints in the DB:** bad data is rejected at the source.
- **Empty and zero states:** AOV shows "-" when there are no non-cancelled orders; charts show a message when there is no data.
- **Indian number format:** `en-IN` grouping, for example Rs 11,59,206.
