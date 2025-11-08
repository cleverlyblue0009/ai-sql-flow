-- Query: group_concat
-- Dialect: mysql
-- Complexity: 40
-- Difficulty: medium

SELECT department, GROUP_CONCAT(name ORDER BY name SEPARATOR ', ') as employees FROM employees GROUP BY department;
