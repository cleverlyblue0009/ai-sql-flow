-- Query: having_clause
-- Dialect: postgresql
-- Complexity: 25
-- Difficulty: easy

SELECT category, COUNT(*) as count FROM products GROUP BY category HAVING COUNT(*) > 10;
