-- Query: iff_function
-- Dialect: snowflake
-- Complexity: 25
-- Difficulty: medium

SELECT name, IFF(status = 1, 'Active', 'Inactive') as status_text FROM users;
