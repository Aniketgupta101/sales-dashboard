"""
main.py — FastAPI application for the sales dashboard.

Serves the REST API and static frontend files.
On startup: creates tables, view, and loads data.
"""

import os
import sys
from contextlib import contextmanager
from datetime import date
from typing import Optional

import psycopg2
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add parent to path so we can import sibling modules
sys.path.insert(0, os.path.dirname(__file__))

from queries import get_dashboard_data, get_filter_options
from load_data import load_data

app = FastAPI(title="Sales Dashboard API")

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "sales"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize database: run schema, view, and load data."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    schema_path = os.path.join(base_dir, "db", "schema.sql")
    view_path = os.path.join(base_dir, "db", "view.sql")
    data_dir = os.path.join(base_dir, "data")

    with get_db() as conn:
        cur = conn.cursor()

        # Run schema
        with open(schema_path, "r") as f:
            cur.execute(f.read())
        conn.commit()

        # Run view
        with open(view_path, "r") as f:
            cur.execute(f.read())
        conn.commit()

        cur.close()

        # Load data
        load_data(conn, data_dir)

    print("Database initialized successfully.")


@app.on_event("startup")
def startup():
    """Initialize database on application startup."""
    try:
        init_database()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("The app will start but API calls may fail until the DB is ready.")


@app.get("/api/dashboard")
def dashboard(
    from_date: Optional[str] = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Product category filter"),
    segment: Optional[str] = Query(None, description="Customer segment filter"),
    city: Optional[str] = Query(None, description="City filter"),
    status: Optional[str] = Query(None, description="Order status filter"),
):
    """Get all dashboard data with optional filters."""
    # Validate dates
    if from_date:
        try:
            date.fromisoformat(from_date)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid from date: {from_date}")

    if to_date:
        try:
            date.fromisoformat(to_date)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid to date: {to_date}")

    filters = {
        "from_date": from_date,
        "to_date": to_date,
        "category": category,
        "segment": segment,
        "city": city,
        "status": status,
    }

    with get_db() as conn:
        cur = conn.cursor()
        try:
            data = get_dashboard_data(cur, filters)
            return data
        finally:
            cur.close()


@app.get("/api/filters")
def filters():
    """Get available filter options for dropdowns."""
    with get_db() as conn:
        cur = conn.cursor()
        try:
            return get_filter_options(cur)
        finally:
            cur.close()


# Serve frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


@app.get("/")
def serve_index():
    """Serve the main dashboard page."""
    return FileResponse(os.path.join(frontend_dir, "index.html"))


app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
