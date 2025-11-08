-- Query: pivot_unpivot
-- Dialect: oracle
-- Complexity: 70
-- Difficulty: hard

SELECT * FROM (
    SELECT year, quarter, revenue
    FROM quarterly_sales
) PIVOT (
    SUM(revenue) FOR quarter IN ('Q1' as Q1, 'Q2' as Q2, 'Q3' as Q3, 'Q4' as Q4)
);
