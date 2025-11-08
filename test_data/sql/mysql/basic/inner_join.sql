-- Query: inner_join
-- Dialect: mysql
-- Complexity: 20
-- Difficulty: easy

SELECT u.name, o.order_id FROM users u INNER JOIN orders o ON u.id = o.user_id;
