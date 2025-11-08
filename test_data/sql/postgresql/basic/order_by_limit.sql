-- Query: order_by_limit
-- Dialect: postgresql
-- Complexity: 15
-- Difficulty: easy

SELECT * FROM users ORDER BY created_at DESC LIMIT 10;
