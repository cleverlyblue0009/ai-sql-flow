-- Query: left_join_with_aggregation
-- Dialect: mysql
-- Complexity: 50
-- Difficulty: medium

SELECT c.name, COALESCE(SUM(o.amount), 0) as total_spent FROM customers c LEFT JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name;
