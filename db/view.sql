-- view.sql
-- Join view combining orders with customer details

CREATE OR REPLACE VIEW vw_sales AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    o.product_id,
    o.product_name,
    o.category,
    o.quantity,
    o.unit_price_inr,
    o.discount_rate,
    o.net_amount_inr,
    o.payment_method,
    o.order_status,
    c.customer_name,
    c.email,
    c.city,
    c.state,
    c.customer_segment,
    c.join_date,
    c.acquisition_channel
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id;
