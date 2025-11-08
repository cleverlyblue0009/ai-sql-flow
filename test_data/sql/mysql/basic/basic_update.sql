-- Query: basic_update
-- Dialect: mysql
-- Complexity: 15
-- Difficulty: easy

UPDATE users SET status = 'active' WHERE created_at > '2024-01-01';
