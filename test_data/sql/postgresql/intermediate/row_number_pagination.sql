-- Query: row_number_pagination
-- Dialect: postgresql
-- Complexity: 50
-- Difficulty: medium

SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (ORDER BY created_at DESC) as rn
    FROM products
) sub WHERE rn BETWEEN 11 AND 20;
