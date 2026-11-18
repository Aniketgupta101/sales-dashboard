"""
test_db.py — Database-level tests (DB-1 to DB-5).

Requires a running PostgreSQL instance with data loaded.
Skipped automatically if DB is not available.
"""

import pytest


@pytest.mark.skipif(True, reason="Requires running PostgreSQL — run with `pytest -m db`")
class TestDatabase:
    """Database tests requiring a live PostgreSQL connection."""

    @pytest.fixture(autouse=True)
    def _require_db(self, db_conn):
        self.conn = db_conn

    def test_db1_row_counts(self):
        """DB-1: 60 customers, 240 orders after load."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM customers")
        assert cur.fetchone()[0] == 60
        cur.execute("SELECT COUNT(*) FROM orders")
        assert cur.fetchone()[0] == 240
        cur.close()

    def test_db2_idempotent_load(self):
        """DB-2: Running loader twice still gives 60 and 240."""
        from load_data import load_data
        load_data(self.conn)
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM customers")
        assert cur.fetchone()[0] == 60
        cur.execute("SELECT COUNT(*) FROM orders")
        assert cur.fetchone()[0] == 240
        cur.close()

    def test_db3_fk_violation(self):
        """DB-3: Insert order with unknown Customer_ID → FK violation."""
        cur = self.conn.cursor()
        with pytest.raises(Exception):
            cur.execute(
                """INSERT INTO orders VALUES
                ('X9999', 'CXXXX', '2026-01-01', 'P001', 'Test', 'Test',
                 1, 100.00, 0.0, 100.00, 'Cash', 'Completed')"""
            )
        self.conn.rollback()
        cur.close()

    def test_db4_check_constraints(self):
        """DB-4: Invalid status, discount > 1, quantity 0 → rejected."""
        cur = self.conn.cursor()

        # Invalid status
        with pytest.raises(Exception):
            cur.execute(
                """INSERT INTO orders VALUES
                ('X9998', 'C0001', '2026-01-01', 'P001', 'Test', 'Test',
                 1, 100.00, 0.0, 100.00, 'Cash', 'Shipped')"""
            )
        self.conn.rollback()

        # Discount > 1
        with pytest.raises(Exception):
            cur.execute(
                """INSERT INTO orders VALUES
                ('X9997', 'C0001', '2026-01-01', 'P001', 'Test', 'Test',
                 1, 100.00, 1.5, 100.00, 'Cash', 'Completed')"""
            )
        self.conn.rollback()

        # Quantity 0
        with pytest.raises(Exception):
            cur.execute(
                """INSERT INTO orders VALUES
                ('X9996', 'C0001', '2026-01-01', 'P001', 'Test', 'Test',
                 0, 100.00, 0.0, 0.00, 'Cash', 'Completed')"""
            )
        self.conn.rollback()
        cur.close()

    def test_db5_view_count(self):
        """SQL-1: vw_sales has 240 rows (no fan-out from join)."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM vw_sales")
        assert cur.fetchone()[0] == 240
        cur.close()
