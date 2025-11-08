-- Query: rownum_limit
-- Dialect: oracle
-- Complexity: 25
-- Difficulty: easy

SELECT * FROM (SELECT * FROM users ORDER BY created_at DESC) WHERE ROWNUM <= 10;
