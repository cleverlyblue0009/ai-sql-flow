-- Query: listagg
-- Dialect: oracle
-- Complexity: 50
-- Difficulty: hard
-- Dialect Features: LISTAGG

SELECT department, LISTAGG(name, ', ') WITHIN GROUP (ORDER BY name) as employees FROM employees GROUP BY department;
