-- Query: aggregate_count
-- Dialect: mysql
-- Complexity: 20
-- Difficulty: easy

SELECT category, COUNT(*) as product_count FROM products GROUP BY category;
