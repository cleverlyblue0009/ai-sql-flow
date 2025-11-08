-- Query: decode_function
-- Dialect: oracle
-- Complexity: 35
-- Difficulty: medium

SELECT name, DECODE(status, 1, 'Active', 2, 'Inactive', 'Unknown') as status_text FROM users;
