-- Query: limit_offset
-- Dialect: snowflake
-- Complexity: 20
-- Difficulty: easy

SELECT * FROM products ORDER BY created_at DESC LIMIT 10 OFFSET 20;
