-- Query: subquery_in
-- Dialect: postgresql
-- Complexity: 35
-- Difficulty: medium

SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 1000);
