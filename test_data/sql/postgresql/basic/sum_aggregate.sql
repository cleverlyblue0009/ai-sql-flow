-- Query: sum_aggregate
-- Dialect: postgresql
-- Complexity: 20
-- Difficulty: easy

SELECT SUM(amount) as total_revenue FROM orders WHERE order_date >= '2024-01-01';
