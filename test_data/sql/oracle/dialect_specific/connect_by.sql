-- Query: connect_by
-- Dialect: oracle
-- Complexity: 70
-- Difficulty: hard
-- Dialect Features: START WITH, CONNECT BY

SELECT id, name, level
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR id = manager_id;
