-- Query: cte_basic
-- Dialect: postgresql
-- Complexity: 50
-- Difficulty: medium

WITH high_value_customers AS (
    SELECT user_id, SUM(amount) as total
    FROM orders
    GROUP BY user_id
    HAVING SUM(amount) > 5000
)
SELECT u.name, hvc.total FROM users u
JOIN high_value_customers hvc ON u.id = hvc.user_id;
