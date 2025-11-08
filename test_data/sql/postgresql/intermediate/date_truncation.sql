-- Query: date_truncation
-- Dialect: postgresql
-- Complexity: 40
-- Difficulty: medium

SELECT DATE_TRUNC('month', order_date) as month, SUM(amount) as revenue FROM orders GROUP BY DATE_TRUNC('month', order_date);
