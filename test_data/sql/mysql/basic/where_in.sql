-- Query: where_in
-- Dialect: mysql
-- Complexity: 15
-- Difficulty: easy

SELECT * FROM orders WHERE status IN ('pending', 'processing', 'shipped');
