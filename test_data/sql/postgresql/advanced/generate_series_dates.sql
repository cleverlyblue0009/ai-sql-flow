-- Query: generate_series_dates
-- Dialect: postgresql
-- Complexity: 70
-- Difficulty: hard

SELECT dates.day, COALESCE(COUNT(o.id), 0) as order_count
FROM generate_series(
    '2024-01-01'::date,
    '2024-12-31'::date,
    '1 day'::interval
) AS dates(day)
LEFT JOIN orders o ON dates.day = o.order_date::date
GROUP BY dates.day
ORDER BY dates.day;
