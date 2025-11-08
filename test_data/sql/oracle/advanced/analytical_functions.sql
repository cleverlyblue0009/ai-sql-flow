-- Query: analytical_functions
-- Dialect: oracle
-- Complexity: 75
-- Difficulty: hard

SELECT name, salary, department,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dept_rank,
    DENSE_RANK() OVER (ORDER BY salary DESC) as overall_rank,
    LEAD(salary) OVER (PARTITION BY department ORDER BY salary) as next_salary
FROM employees;
