-- Query: row_number_pagination
-- Dialect: oracle
-- Complexity: 50
-- Difficulty: medium

SELECT * FROM (
    SELECT a.*, ROW_NUMBER() OVER (ORDER BY created_at DESC) as rn
    FROM articles a
) WHERE rn BETWEEN 11 AND 20;
