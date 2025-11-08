-- Query: window_function_rank
-- Dialect: postgresql
-- Complexity: 45
-- Difficulty: medium

SELECT name, salary, department,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) as salary_rank
FROM employees;
