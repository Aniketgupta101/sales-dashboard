"""
conftest.py — Shared pytest fixtures for the sales dashboard tests.

Provides pandas DataFrames as the independent "oracle" for metric validation,
plus optional DB connection and FastAPI TestClient fixtures.
"""

import os
import sys
import pytest
import pandas as pd

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@pytest.fixture(scope="session")
def df_customers():
    """Load customers DataFrame from Excel (oracle data)."""
    return pd.read_excel(os.path.join(DATA_DIR, "customers.xlsx"))


@pytest.fixture(scope="session")
def df_orders():
    """Load orders DataFrame from Excel (oracle data)."""
    return pd.read_excel(os.path.join(DATA_DIR, "orders.xlsx"))


@pytest.fixture(scope="session")
def df_sales(df_customers, df_orders):
    """Joined DataFrame (simulates vw_sales view)."""
    return pd.merge(df_orders, df_customers, on="Customer_ID", how="inner")


@pytest.fixture(scope="session")
def db_conn():
    """Database connection fixture — skipped if DB not available."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "sales"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        )
        yield conn
        conn.close()
    except Exception:
        pytest.skip("Database not available")


@pytest.fixture(scope="session")
def api_client(db_conn):
    """FastAPI TestClient fixture — requires DB connection."""
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as client:
        yield client
