-- Query: pivot_crosstab
-- Dialect: postgresql
-- Complexity: 80
-- Difficulty: hard

SELECT *
FROM crosstab(
    'SELECT customer_id, product_category, SUM(amount) FROM orders GROUP BY 1, 2 ORDER BY 1, 2',
    'SELECT DISTINCT product_category FROM orders ORDER BY 1'
) AS ct(customer_id int, electronics numeric, clothing numeric, food numeric);
