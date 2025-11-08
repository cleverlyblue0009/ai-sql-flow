-- Query: array_operations
-- Dialect: postgresql
-- Complexity: 30
-- Difficulty: medium

SELECT id, name FROM products WHERE 'electronics' = ANY(tags);
