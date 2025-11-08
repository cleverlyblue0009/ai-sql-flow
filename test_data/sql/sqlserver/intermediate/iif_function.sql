-- Query: iif_function
-- Dialect: sqlserver
-- Complexity: 25
-- Difficulty: medium

SELECT name, IIF(status = 1, 'Active', 'Inactive') as status_text FROM users;
