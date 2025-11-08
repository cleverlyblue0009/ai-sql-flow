-- Query: extract_date_parts
-- Dialect: postgresql
-- Complexity: 40
-- Difficulty: medium

SELECT EXTRACT(YEAR FROM order_date) as year, EXTRACT(MONTH FROM order_date) as month, SUM(amount) FROM orders GROUP BY 1, 2;
