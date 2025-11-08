-- Query: simple_join
-- Dialect: postgresql
-- Complexity: 20
-- Difficulty: easy

SELECT u.name, o.order_id FROM users u JOIN orders o ON u.id = o.user_id;
