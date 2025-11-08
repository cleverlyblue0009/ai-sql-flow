-- Query: multiple_joins
-- Dialect: postgresql
-- Complexity: 60
-- Difficulty: medium

SELECT u.name, COUNT(o.id) as order_count, SUM(o.amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5;
