-- Query: avg_aggregate
-- Dialect: postgresql
-- Complexity: 20
-- Difficulty: easy

SELECT AVG(price) as avg_price FROM products GROUP BY category;
