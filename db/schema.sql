-- schema.sql
-- Sales Dashboard: Table definitions with constraints and indexes

DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id         VARCHAR(10)  PRIMARY KEY,
    customer_name       VARCHAR(100) NOT NULL,
    email               VARCHAR(150) NOT NULL,
    city                VARCHAR(50)  NOT NULL,
    state               VARCHAR(50)  NOT NULL,
    customer_segment    VARCHAR(30)  NOT NULL,
    join_date           DATE         NOT NULL,
    acquisition_channel VARCHAR(30)  NOT NULL
);

CREATE TABLE orders (
    order_id        VARCHAR(10)   PRIMARY KEY,
    customer_id     VARCHAR(10)   NOT NULL REFERENCES customers(customer_id),
    order_date      DATE          NOT NULL,
    product_id      VARCHAR(10)   NOT NULL,
    product_name    VARCHAR(100)  NOT NULL,
    category        VARCHAR(50)   NOT NULL,
    quantity        INT           NOT NULL CHECK (quantity > 0),
    unit_price_inr  NUMERIC(12,2) NOT NULL CHECK (unit_price_inr >= 0),
    discount_rate   NUMERIC(4,3)  NOT NULL CHECK (discount_rate BETWEEN 0 AND 1),
    net_amount_inr  NUMERIC(12,2) NOT NULL CHECK (net_amount_inr >= 0),
    payment_method  VARCHAR(30)   NOT NULL,
    order_status    VARCHAR(20)   NOT NULL
                    CHECK (order_status IN ('Completed', 'Returned', 'Cancelled'))
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date     ON orders(order_date);
CREATE INDEX idx_orders_status   ON orders(order_status);
CREATE INDEX idx_orders_category ON orders(category);
