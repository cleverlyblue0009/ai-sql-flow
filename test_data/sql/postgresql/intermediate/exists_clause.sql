-- Query: exists_clause
-- Dialect: postgresql
-- Complexity: 40
-- Difficulty: medium

SELECT * FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.amount > 1000);
