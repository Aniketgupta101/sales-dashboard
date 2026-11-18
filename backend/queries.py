"""
queries.py — All parameterised SQL queries for the sales dashboard.

Every function takes a connection and optional filter dict, returns data.
No string interpolation for SQL — parameterised queries only.
"""


def _build_where_clause(filters):
    """Build WHERE clause and params from filter dict.

    Returns (where_sql, params) where where_sql starts with 'WHERE ...'
    or is empty string if no filters.
    """
    conditions = []
    params = []

    if filters.get("from_date"):
        conditions.append("order_date >= %s")
        params.append(filters["from_date"])

    if filters.get("to_date"):
        conditions.append("order_date <= %s")
        params.append(filters["to_date"])

    if filters.get("category"):
        conditions.append("category = %s")
        params.append(filters["category"])

    if filters.get("segment"):
        conditions.append("customer_segment = %s")
        params.append(filters["segment"])

    if filters.get("city"):
        conditions.append("city = %s")
        params.append(filters["city"])

    if filters.get("status"):
        conditions.append("order_status = %s")
        params.append(filters["status"])

    if conditions:
        return "WHERE " + " AND ".join(conditions), params
    return "", params


def get_kpis(cur, filters):
    """Get KPI metrics: net revenue, total orders, unique customers, AOV, repeat customers."""
    where, params = _build_where_clause(filters)

    # Main KPIs
    cur.execute(
        f"""
        SELECT
            COALESCE(SUM(net_amount_inr), 0)                           AS net_revenue,
            COUNT(DISTINCT order_id)                                   AS total_orders,
            COUNT(DISTINCT customer_id)                                AS unique_customers,
            CASE
                WHEN COUNT(DISTINCT order_id) FILTER (WHERE order_status <> 'Cancelled') = 0
                THEN NULL
                ELSE SUM(net_amount_inr) /
                     COUNT(DISTINCT order_id) FILTER (WHERE order_status <> 'Cancelled')
            END                                                        AS avg_order_value
        FROM vw_sales
        {where}
        """,
        params,
    )
    row = cur.fetchone()
    kpis = {
        "net_revenue": float(row[0]),
        "total_orders": row[1],
        "unique_customers": row[2],
        "avg_order_value": round(float(row[3]), 2) if row[3] is not None else None,
    }

    # Repeat customers (2+ non-cancelled orders within the filter)
    cur.execute(
        f"""
        SELECT COUNT(*) FROM (
            SELECT customer_id
            FROM vw_sales
            {where}
            {"AND" if where else "WHERE"} order_status <> 'Cancelled'
            GROUP BY customer_id
            HAVING COUNT(DISTINCT order_id) >= 2
        ) sub
        """,
        params,
    )
    kpis["repeat_customers"] = cur.fetchone()[0]

    return kpis


def get_monthly_revenue(cur, filters):
    """Monthly revenue trend using generate_series to include empty months."""
    where, params = _build_where_clause(filters)

    cur.execute(
        f"""
        WITH months AS (
            SELECT generate_series(
                '2026-01-01'::date,
                '2026-06-01'::date,
                '1 month'::interval
            )::date AS month_start
        ),
        filtered AS (
            SELECT date_trunc('month', order_date)::date AS order_month,
                   net_amount_inr
            FROM vw_sales
            {where}
        )
        SELECT
            to_char(m.month_start, 'YYYY-MM') AS month,
            COALESCE(SUM(f.net_amount_inr), 0) AS revenue
        FROM months m
        LEFT JOIN filtered f ON f.order_month = m.month_start
        GROUP BY m.month_start
        ORDER BY m.month_start
        """,
        params,
    )
    return [{"month": row[0], "revenue": float(row[1])} for row in cur.fetchall()]


def get_revenue_by_category(cur, filters):
    """Revenue grouped by product category."""
    where, params = _build_where_clause(filters)
    cur.execute(
        f"""
        SELECT category AS label, COALESCE(SUM(net_amount_inr), 0) AS revenue
        FROM vw_sales
        {where}
        GROUP BY category
        ORDER BY revenue DESC
        """,
        params,
    )
    return [{"label": row[0], "revenue": float(row[1])} for row in cur.fetchall()]


def get_revenue_by_segment(cur, filters):
    """Revenue grouped by customer segment."""
    where, params = _build_where_clause(filters)
    cur.execute(
        f"""
        SELECT customer_segment AS label, COALESCE(SUM(net_amount_inr), 0) AS revenue
        FROM vw_sales
        {where}
        GROUP BY customer_segment
        ORDER BY revenue DESC
        """,
        params,
    )
    return [{"label": row[0], "revenue": float(row[1])} for row in cur.fetchall()]


def get_revenue_by_city(cur, filters):
    """Revenue grouped by city."""
    where, params = _build_where_clause(filters)
    cur.execute(
        f"""
        SELECT city AS label, COALESCE(SUM(net_amount_inr), 0) AS revenue
        FROM vw_sales
        {where}
        GROUP BY city
        ORDER BY revenue DESC
        """,
        params,
    )
    return [{"label": row[0], "revenue": float(row[1])} for row in cur.fetchall()]


def get_orders_by_status(cur, filters):
    """Order count grouped by status."""
    where, params = _build_where_clause(filters)
    cur.execute(
        f"""
        SELECT order_status AS label, COUNT(DISTINCT order_id) AS orders
        FROM vw_sales
        {where}
        GROUP BY order_status
        ORDER BY orders DESC
        """,
        params,
    )
    return [{"label": row[0], "orders": row[1]} for row in cur.fetchall()]


def get_top_products(cur, filters, limit=5):
    """Top N products by revenue."""
    where, params = _build_where_clause(filters)
    params.append(limit)
    cur.execute(
        f"""
        SELECT product_name AS label, COALESCE(SUM(net_amount_inr), 0) AS revenue
        FROM vw_sales
        {where}
        GROUP BY product_name
        ORDER BY revenue DESC
        LIMIT %s
        """,
        params,
    )
    return [{"label": row[0], "revenue": float(row[1])} for row in cur.fetchall()]


def get_filter_options(cur):
    """Get distinct values for each filter dropdown."""
    result = {}

    cur.execute("SELECT DISTINCT category FROM vw_sales ORDER BY category")
    result["categories"] = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT customer_segment FROM vw_sales ORDER BY customer_segment")
    result["segments"] = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT city FROM vw_sales ORDER BY city")
    result["cities"] = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT order_status FROM vw_sales ORDER BY order_status")
    result["statuses"] = [row[0] for row in cur.fetchall()]

    return result


def get_dashboard_data(cur, filters):
    """Get all dashboard data in one call."""
    return {
        "kpis": get_kpis(cur, filters),
        "monthly": get_monthly_revenue(cur, filters),
        "by_category": get_revenue_by_category(cur, filters),
        "by_segment": get_revenue_by_segment(cur, filters),
        "by_city": get_revenue_by_city(cur, filters),
        "by_status": get_orders_by_status(cur, filters),
        "top_products": get_top_products(cur, filters),
    }
