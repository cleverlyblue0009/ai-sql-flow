-- Query: is_null_check
-- Dialect: postgresql
-- Complexity: 10
-- Difficulty: easy

SELECT * FROM users WHERE last_login IS NULL;
