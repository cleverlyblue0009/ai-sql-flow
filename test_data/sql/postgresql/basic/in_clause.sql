-- Query: in_clause
-- Dialect: postgresql
-- Complexity: 15
-- Difficulty: easy

SELECT * FROM users WHERE role IN ('admin', 'manager', 'supervisor');
