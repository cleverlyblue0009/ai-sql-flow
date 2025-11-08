-- Query: qualify_clause
-- Dialect: snowflake
-- Complexity: 60
-- Difficulty: medium

SELECT name, salary, department
FROM employees
QUALIFY ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) = 1;
