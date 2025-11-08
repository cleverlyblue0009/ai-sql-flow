-- Query: array_agg
-- Dialect: postgresql
-- Complexity: 40
-- Difficulty: hard
-- Dialect Features: ARRAY_AGG

SELECT department, ARRAY_AGG(name ORDER BY name) as employees FROM employees GROUP BY department;
