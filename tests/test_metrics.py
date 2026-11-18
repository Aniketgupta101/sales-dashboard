"""
test_metrics.py — Pandas oracle tests for metric accuracy.

Tests M-1 to M-9 from the test plan: validates KPIs, breakdowns,
and bonus metrics using pandas as the independent source of truth.
"""

import pandas as pd
import pytest


class TestMetricsOracle:
    """Validate ground-truth KPIs against pandas-computed values."""

    def test_m1_total_orders(self, df_orders):
        """M-1: Total orders = 240 (count of unique Order_ID)."""
        assert df_orders["Order_ID"].nunique() == 240

    def test_m2_unique_customers(self, df_sales):
        """M-2: Unique customers = 59 (from joined orders, not customers table)."""
        assert df_sales["Customer_ID"].nunique() == 59

    def test_m3_aov(self, df_orders):
        """M-3: AOV = total net revenue / non-cancelled orders = 5682.38."""
        revenue = df_orders["Net_Amount_INR"].sum()
        non_cancelled = df_orders[df_orders["Order_Status"] != "Cancelled"]["Order_ID"].nunique()
        aov = revenue / non_cancelled
        assert round(aov, 2) == 5682.38

    def test_m3_net_revenue(self, df_orders):
        """Net revenue = 1,159,206."""
        assert df_orders["Net_Amount_INR"].sum() == 1_159_206

    def test_m4_revenue_by_category(self, df_orders):
        """M-4: Revenue by category matches expected values."""
        expected = {
            "Electronics": 532_772,
            "Accessories": 248_730,
            "Lifestyle": 192_597,
            "Office": 185_107,
        }
        actual = df_orders.groupby("Category")["Net_Amount_INR"].sum().to_dict()
        for cat, rev in expected.items():
            assert actual[cat] == rev, f"{cat}: expected {rev}, got {actual[cat]}"

    def test_m5_monthly_revenue(self, df_orders):
        """M-5: Monthly revenue for all 6 months."""
        expected = {
            1: 231_812, 2: 157_676, 3: 225_820,
            4: 160_162, 5: 139_176, 6: 244_560,
        }
        df = df_orders.copy()
        df["Month"] = pd.to_datetime(df["Order_Date"]).dt.month
        actual = df.groupby("Month")["Net_Amount_INR"].sum().to_dict()
        for month, rev in expected.items():
            assert actual[month] == rev, f"Month {month}: expected {rev}, got {actual[month]}"

    def test_m6_revenue_by_segment(self, df_sales):
        """M-6: Revenue by customer segment."""
        expected = {
            "Consumer": 473_590,
            "Corporate": 446_560,
            "Small Business": 239_056,
        }
        actual = df_sales.groupby("Customer_Segment")["Net_Amount_INR"].sum().to_dict()
        for seg, rev in expected.items():
            assert actual[seg] == rev, f"{seg}: expected {rev}, got {actual[seg]}"

    def test_m7_orders_by_status(self, df_orders):
        """M-7: Order counts by status."""
        expected = {"Completed": 164, "Returned": 40, "Cancelled": 36}
        actual = df_orders.groupby("Order_Status")["Order_ID"].nunique().to_dict()
        for status, count in expected.items():
            assert actual[status] == count, f"{status}: expected {count}, got {actual[status]}"

    def test_m8_top5_products(self, df_orders):
        """M-8: Top 5 products by revenue."""
        expected = [
            ("Smart Watch", 274_674),
            ("Bluetooth Speaker", 182_337),
            ("USB-C Hub", 116_754),
            ("Mechanical Keyboard", 106_580),
            ("Laptop Stand", 86_717),
        ]
        top5 = (
            df_orders.groupby("Product_Name")["Net_Amount_INR"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        for name, rev in expected:
            assert top5[name] == rev, f"{name}: expected {rev}, got {top5[name]}"

    def test_m9_repeat_customers(self, df_orders):
        """M-9: Repeat customers (2+ non-cancelled orders) = 48."""
        non_cancelled = df_orders[df_orders["Order_Status"] != "Cancelled"]
        orders_per_customer = non_cancelled.groupby("Customer_ID")["Order_ID"].nunique()
        repeat = (orders_per_customer >= 2).sum()
        assert repeat == 48

    def test_cancelled_orders_zero_revenue(self, df_orders):
        """Cancelled orders should all have net amount = 0."""
        cancelled = df_orders[df_orders["Order_Status"] == "Cancelled"]
        assert (cancelled["Net_Amount_INR"] == 0).all()

    def test_returned_revenue(self, df_orders):
        """Returned orders contribute Rs 198,890 revenue."""
        returned = df_orders[df_orders["Order_Status"] == "Returned"]
        assert returned["Net_Amount_INR"].sum() == 198_890


class TestFilteredMetrics:
    """Validate filter scenarios F-1 to F-4 against pandas."""

    def test_f1_status_returned(self, df_sales):
        """F-1: Status = Returned → revenue 198890, orders 40, AOV 4972.25."""
        filtered = df_sales[df_sales["Order_Status"] == "Returned"]
        assert filtered["Net_Amount_INR"].sum() == 198_890
        assert filtered["Order_ID"].nunique() == 40
        aov = filtered["Net_Amount_INR"].sum() / filtered["Order_ID"].nunique()
        assert round(aov, 2) == 4972.25

    def test_f2_status_cancelled(self, df_sales):
        """F-2: Status = Cancelled → revenue 0, orders 36."""
        filtered = df_sales[df_sales["Order_Status"] == "Cancelled"]
        assert filtered["Net_Amount_INR"].sum() == 0
        assert filtered["Order_ID"].nunique() == 36

    def test_f3_category_electronics(self, df_sales):
        """F-3: Category = Electronics → revenue 532772."""
        filtered = df_sales[df_sales["Category"] == "Electronics"]
        assert filtered["Net_Amount_INR"].sum() == 532_772

    def test_f4_january(self, df_sales):
        """F-4: Date 2026-01-01 to 2026-01-31 → revenue 231812, orders 44."""
        df = df_sales.copy()
        df["Order_Date"] = pd.to_datetime(df["Order_Date"])
        filtered = df[(df["Order_Date"] >= "2026-01-01") & (df["Order_Date"] <= "2026-01-31")]
        assert filtered["Net_Amount_INR"].sum() == 231_812
        assert filtered["Order_ID"].nunique() == 44
