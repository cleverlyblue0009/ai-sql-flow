-- Query: string_aggregation
-- Dialect: postgresql
-- Complexity: 40
-- Difficulty: medium

SELECT department, STRING_AGG(name, ', ' ORDER BY name) as employees FROM employees GROUP BY department;
