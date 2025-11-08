-- Query: cte_with_window
-- Dialect: snowflake
-- Complexity: 80
-- Difficulty: hard

WITH monthly_sales AS (
    SELECT DATE_TRUNC('month', order_date) as month, 
           SUM(amount) as total,
           LAG(SUM(amount)) OVER (ORDER BY DATE_TRUNC('month', order_date)) as prev_month
    FROM orders
    GROUP BY DATE_TRUNC('month', order_date)
)
SELECT month, total, prev_month,
       ((total - prev_month) / prev_month * 100) as growth_percent
FROM monthly_sales;
