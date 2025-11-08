-- Query: case_when
-- Dialect: mysql
-- Complexity: 35
-- Difficulty: medium

SELECT name, CASE WHEN salary > 100000 THEN 'High' WHEN salary > 50000 THEN 'Medium' ELSE 'Low' END as salary_band FROM employees;
