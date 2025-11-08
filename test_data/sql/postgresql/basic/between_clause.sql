-- Query: between_clause
-- Dialect: postgresql
-- Complexity: 15
-- Difficulty: easy

SELECT * FROM orders WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31';
