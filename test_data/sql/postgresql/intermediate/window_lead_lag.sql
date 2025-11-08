-- Query: window_lead_lag
-- Dialect: postgresql
-- Complexity: 50
-- Difficulty: medium

SELECT date, revenue,
    LAG(revenue) OVER (ORDER BY date) as previous_day_revenue,
    LEAD(revenue) OVER (ORDER BY date) as next_day_revenue
FROM daily_sales;
