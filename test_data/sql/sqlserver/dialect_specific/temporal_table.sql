-- Query: temporal_table
-- Dialect: sqlserver
-- Complexity: 50
-- Difficulty: hard
-- Dialect Features: SYSTEM_TIME

SELECT * FROM employees FOR SYSTEM_TIME AS OF '2024-01-01';
