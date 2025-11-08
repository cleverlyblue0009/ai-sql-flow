-- Query: case_statement
-- Dialect: postgresql
-- Complexity: 35
-- Difficulty: medium

SELECT name,
    CASE 
        WHEN salary > 100000 THEN 'Executive'
        WHEN salary > 50000 THEN 'Senior'
        ELSE 'Junior'
    END as level
FROM employees;
