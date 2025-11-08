-- Query: multiple_ctes
-- Dialect: postgresql
-- Complexity: 80
-- Difficulty: hard

WITH monthly_sales AS (
    SELECT DATE_TRUNC('month', order_date) as month, SUM(amount) as total
    FROM orders
    GROUP BY DATE_TRUNC('month', order_date)
),
yearly_sales AS (
    SELECT DATE_TRUNC('year', order_date) as year, SUM(amount) as total
    FROM orders
    GROUP BY DATE_TRUNC('year', order_date)
)
SELECT m.month, m.total as monthly, y.total as yearly
FROM monthly_sales m
JOIN yearly_sales y ON DATE_TRUNC('year', m.month) = y.year;
