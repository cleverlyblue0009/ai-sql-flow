-- Query: lateral_join
-- Dialect: postgresql
-- Complexity: 65
-- Difficulty: hard

SELECT u.name, recent_orders.*
FROM users u
CROSS JOIN LATERAL (
    SELECT o.id, o.amount, o.order_date
    FROM orders o
    WHERE o.user_id = u.id
    ORDER BY o.order_date DESC
    LIMIT 5
) recent_orders;
