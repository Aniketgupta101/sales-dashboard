"""
load_data.py — Idempotent data loader for the sales dashboard.

Reads customers.xlsx and orders.xlsx, loads them into PostgreSQL.
Idempotent: TRUNCATE + re-insert inside a single transaction.
"""

import os
import sys
import pandas as pd
import psycopg2


def get_connection():
    """Create a PostgreSQL connection from environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "sales"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def load_data(conn, data_dir=None):
    """Load Excel data into the database (idempotent: truncate + insert)."""
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    customers_path = os.path.join(data_dir, "customers.xlsx")
    orders_path = os.path.join(data_dir, "orders.xlsx")

    # Read Excel files
    df_customers = pd.read_excel(customers_path)
    df_orders = pd.read_excel(orders_path)

    cur = conn.cursor()
    try:
        # Truncate in correct order (orders first due to FK)
        cur.execute("TRUNCATE TABLE orders CASCADE;")
        cur.execute("TRUNCATE TABLE customers CASCADE;")

        # Insert customers
        for _, row in df_customers.iterrows():
            cur.execute(
                """
                INSERT INTO customers
                    (customer_id, customer_name, email, city, state,
                     customer_segment, join_date, acquisition_channel)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row["Customer_ID"],
                    row["Customer_Name"],
                    row["Email"],
                    row["City"],
                    row["State"],
                    row["Customer_Segment"],
                    row["Join_Date"].date() if hasattr(row["Join_Date"], "date") else row["Join_Date"],
                    row["Acquisition_Channel"],
                ),
            )

        # Insert orders
        for _, row in df_orders.iterrows():
            cur.execute(
                """
                INSERT INTO orders
                    (order_id, customer_id, order_date, product_id, product_name,
                     category, quantity, unit_price_inr, discount_rate,
                     net_amount_inr, payment_method, order_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row["Order_ID"],
                    row["Customer_ID"],
                    row["Order_Date"].date() if hasattr(row["Order_Date"], "date") else row["Order_Date"],
                    row["Product_ID"],
                    row["Product_Name"],
                    row["Category"],
                    int(row["Quantity"]),
                    float(row["Unit_Price_INR"]),
                    float(row["Discount_Rate"]),
                    float(row["Net_Amount_INR"]),
                    row["Payment_Method"],
                    row["Order_Status"],
                ),
            )

        conn.commit()
        print(f"Loaded {len(df_customers)} customers and {len(df_orders)} orders.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


if __name__ == "__main__":
    conn = get_connection()
    try:
        load_data(conn)
    finally:
        conn.close()
