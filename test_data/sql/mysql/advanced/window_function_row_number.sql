-- Query: window_function_row_number
-- Dialect: mysql
-- Complexity: 60
-- Difficulty: hard

SELECT name, department, salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as dept_rank
FROM employees;
