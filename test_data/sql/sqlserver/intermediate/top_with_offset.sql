-- Query: top_with_offset
-- Dialect: sqlserver
-- Complexity: 30
-- Difficulty: medium

SELECT * FROM products ORDER BY created_at DESC OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY;
