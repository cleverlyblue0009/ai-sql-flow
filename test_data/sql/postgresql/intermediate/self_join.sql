-- Query: self_join
-- Dialect: postgresql
-- Complexity: 40
-- Difficulty: medium

SELECT e1.name as employee, e2.name as manager FROM employees e1 LEFT JOIN employees e2 ON e1.manager_id = e2.id;
