-- Query: insert_values
-- Dialect: snowflake
-- Complexity: 20
-- Difficulty: easy

INSERT INTO orders (customer_id, amount, order_date) VALUES (123, 99.99, CURRENT_TIMESTAMP());
