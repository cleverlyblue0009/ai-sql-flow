-- Query: complex_nested_query
-- Dialect: postgresql
-- Complexity: 75
-- Difficulty: hard

SELECT u.name, u.email,
    (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as total_orders,
    (SELECT SUM(amount) FROM orders o WHERE o.user_id = u.id) as total_spent,
    (SELECT AVG(amount) FROM orders o WHERE o.user_id = u.id) as avg_order
FROM users u
WHERE u.id IN (
    SELECT user_id FROM orders
    GROUP BY user_id
    HAVING SUM(amount) > 1000
)
ORDER BY total_spent DESC;
