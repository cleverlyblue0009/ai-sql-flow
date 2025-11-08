-- Query: window_moving_average
-- Dialect: postgresql
-- Complexity: 70
-- Difficulty: hard

SELECT date, revenue,
    AVG(revenue) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_avg_7d,
    SUM(revenue) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as rolling_sum_30d
FROM daily_sales;
