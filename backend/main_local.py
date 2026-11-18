"""
main_local.py — Local version of the FastAPI app using SQLite (no PostgreSQL needed).

Run with:  uvicorn backend.main_local:app --reload --port 8000
"""

import os
import sys
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Sales Dashboard API (Local)")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "sales.db")
DATA_DIR = os.path.join(BASE_DIR, "data")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Create tables, load data from Excel into SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create tables
    cur.executescript("""
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            customer_id         TEXT PRIMARY KEY,
            customer_name       TEXT NOT NULL,
            email               TEXT NOT NULL,
            city                TEXT NOT NULL,
            state               TEXT NOT NULL,
            customer_segment    TEXT NOT NULL,
            join_date           TEXT NOT NULL,
            acquisition_channel TEXT NOT NULL
        );

        CREATE TABLE orders (
            order_id        TEXT PRIMARY KEY,
            customer_id     TEXT NOT NULL REFERENCES customers(customer_id),
            order_date      TEXT NOT NULL,
            product_id      TEXT NOT NULL,
            product_name    TEXT NOT NULL,
            category        TEXT NOT NULL,
            quantity        INTEGER NOT NULL,
            unit_price_inr  REAL NOT NULL,
            discount_rate   REAL NOT NULL,
            net_amount_inr  REAL NOT NULL,
            payment_method  TEXT NOT NULL,
            order_status    TEXT NOT NULL
        );

        CREATE INDEX idx_orders_customer ON orders(customer_id);
        CREATE INDEX idx_orders_date     ON orders(order_date);
        CREATE INDEX idx_orders_status   ON orders(order_status);
        CREATE INDEX idx_orders_category ON orders(category);

        CREATE VIEW IF NOT EXISTS vw_sales AS
        SELECT o.*, c.customer_name, c.email, c.city, c.state,
               c.customer_segment, c.join_date, c.acquisition_channel
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id;
    """)

    # Load customers
    df_cust = pd.read_excel(os.path.join(DATA_DIR, "customers.xlsx"))
    for _, row in df_cust.iterrows():
        jd = row["Join_Date"]
        join_date_str = jd.strftime("%Y-%m-%d") if hasattr(jd, "strftime") else str(jd)
        cur.execute(
            "INSERT INTO customers VALUES (?,?,?,?,?,?,?,?)",
            (row["Customer_ID"], row["Customer_Name"], row["Email"],
             row["City"], row["State"], row["Customer_Segment"],
             join_date_str, row["Acquisition_Channel"]),
        )

    # Load orders
    df_ord = pd.read_excel(os.path.join(DATA_DIR, "orders.xlsx"))
    for _, row in df_ord.iterrows():
        od = row["Order_Date"]
        order_date_str = od.strftime("%Y-%m-%d") if hasattr(od, "strftime") else str(od)
        cur.execute(
            "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (row["Order_ID"], row["Customer_ID"], order_date_str,
             row["Product_ID"], row["Product_Name"], row["Category"],
             int(row["Quantity"]), float(row["Unit_Price_INR"]),
             float(row["Discount_Rate"]), float(row["Net_Amount_INR"]),
             row["Payment_Method"], row["Order_Status"]),
        )

    conn.commit()
    conn.close()
    print(f"SQLite DB initialized at {DB_PATH}: {len(df_cust)} customers, {len(df_ord)} orders.")


# ── Query helpers ────────────────────────────────────────────────────

def _build_where(filters):
    conditions = []
    params = []
    if filters.get("from_date"):
        conditions.append("order_date >= ?")
        params.append(filters["from_date"])
    if filters.get("to_date"):
        conditions.append("order_date <= ?")
        params.append(filters["to_date"])
    if filters.get("category"):
        conditions.append("category = ?")
        params.append(filters["category"])
    if filters.get("segment"):
        conditions.append("customer_segment = ?")
        params.append(filters["segment"])
    if filters.get("city"):
        conditions.append("city = ?")
        params.append(filters["city"])
    if filters.get("status"):
        conditions.append("order_status = ?")
        params.append(filters["status"])
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    return where, params


def _get_kpis(cur, filters):
    where, params = _build_where(filters)
    cur.execute(f"""
        SELECT
            COALESCE(SUM(net_amount_inr), 0),
            COUNT(DISTINCT order_id),
            COUNT(DISTINCT customer_id)
        FROM vw_sales {where}
    """, params)
    rev, orders, custs = cur.fetchone()

    # Non-cancelled count for AOV
    and_or_where = "AND" if where else "WHERE"
    cur.execute(f"""
        SELECT COUNT(DISTINCT order_id)
        FROM vw_sales {where} {and_or_where} order_status <> 'Cancelled'
    """, params)
    non_cancelled = cur.fetchone()[0]

    aov = round(rev / non_cancelled, 2) if non_cancelled > 0 else None

    # Repeat customers
    cur.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT customer_id
            FROM vw_sales {where} {and_or_where} order_status <> 'Cancelled'
            GROUP BY customer_id
            HAVING COUNT(DISTINCT order_id) >= 2
        )
    """, params)
    repeat = cur.fetchone()[0]

    return {
        "net_revenue": float(rev),
        "total_orders": orders,
        "unique_customers": custs,
        "avg_order_value": aov,
        "repeat_customers": repeat,
    }


def _get_monthly(cur, filters):
    where, params = _build_where(filters)
    # Generate all 6 months, left join with filtered data
    months = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
    cur.execute(f"""
        SELECT substr(order_date, 1, 7) AS month, COALESCE(SUM(net_amount_inr), 0)
        FROM vw_sales {where}
        GROUP BY month ORDER BY month
    """, params)
    data = {r[0]: float(r[1]) for r in cur.fetchall()}
    return [{"month": m, "revenue": data.get(m, 0.0)} for m in months]


def _get_grouped(cur, filters, group_col, value_expr="SUM(net_amount_inr)", value_key="revenue"):
    where, params = _build_where(filters)
    cur.execute(f"""
        SELECT {group_col} AS label, COALESCE({value_expr}, 0) AS val
        FROM vw_sales {where}
        GROUP BY {group_col} ORDER BY val DESC
    """, params)
    return [{"label": r[0], value_key: float(r[1]) if value_key == "revenue" else r[1]} for r in cur.fetchall()]


def _get_top_products(cur, filters, limit=5):
    where, params = _build_where(filters)
    params.append(limit)
    cur.execute(f"""
        SELECT product_name AS label, COALESCE(SUM(net_amount_inr), 0) AS revenue
        FROM vw_sales {where}
        GROUP BY product_name ORDER BY revenue DESC LIMIT ?
    """, params)
    return [{"label": r[0], "revenue": float(r[1])} for r in cur.fetchall()]


# ── API endpoints ────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_database()


@app.get("/api/dashboard")
def dashboard(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    category: Optional[str] = Query(None),
    segment: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    if from_date:
        try:
            date.fromisoformat(from_date)
        except ValueError:
            raise HTTPException(422, f"Invalid from date: {from_date}")
    if to_date:
        try:
            date.fromisoformat(to_date)
        except ValueError:
            raise HTTPException(422, f"Invalid to date: {to_date}")

    filters = {"from_date": from_date, "to_date": to_date, "category": category,
               "segment": segment, "city": city, "status": status}

    with get_db() as conn:
        cur = conn.cursor()
        return {
            "kpis": _get_kpis(cur, filters),
            "monthly": _get_monthly(cur, filters),
            "by_category": _get_grouped(cur, filters, "category"),
            "by_segment": _get_grouped(cur, filters, "customer_segment"),
            "by_city": _get_grouped(cur, filters, "city"),
            "by_status": _get_grouped(cur, filters, "order_status", "COUNT(DISTINCT order_id)", "orders"),
            "top_products": _get_top_products(cur, filters),
        }


@app.get("/api/filters")
def filters_endpoint():
    with get_db() as conn:
        cur = conn.cursor()
        result = {}
        for key, col in [("categories", "category"), ("segments", "customer_segment"),
                          ("cities", "city"), ("statuses", "order_status")]:
            cur.execute(f"SELECT DISTINCT {col} FROM vw_sales ORDER BY {col}")
            result[key] = [r[0] for r in cur.fetchall()]
        return result


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
