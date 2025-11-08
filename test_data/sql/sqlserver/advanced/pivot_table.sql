-- Query: pivot_table
-- Dialect: sqlserver
-- Complexity: 70
-- Difficulty: hard

SELECT * FROM (
    SELECT category, month, sales
    FROM monthly_sales
) src
PIVOT (
    SUM(sales) FOR month IN ([Jan], [Feb], [Mar], [Apr])
) piv;
