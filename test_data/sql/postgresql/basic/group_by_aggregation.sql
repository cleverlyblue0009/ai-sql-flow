-- Query: group_by_aggregation
-- Dialect: postgresql
-- Complexity: 20
-- Difficulty: easy

SELECT category, COUNT(*) as count FROM products GROUP BY category;
