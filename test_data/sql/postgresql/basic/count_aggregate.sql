-- Query: count_aggregate
-- Dialect: postgresql
-- Complexity: 10
-- Difficulty: easy

SELECT COUNT(*) FROM orders WHERE status = 'completed';
