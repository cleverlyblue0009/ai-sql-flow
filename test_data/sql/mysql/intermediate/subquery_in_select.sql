-- Query: subquery_in_select
-- Dialect: mysql
-- Complexity: 45
-- Difficulty: medium

SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as order_count FROM users u;
