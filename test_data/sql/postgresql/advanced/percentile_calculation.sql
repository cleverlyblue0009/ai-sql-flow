-- Query: percentile_calculation
-- Dialect: postgresql
-- Complexity: 60
-- Difficulty: hard

SELECT 
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary) as p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY salary) as median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary) as p75,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY salary) as p90
FROM employees;
