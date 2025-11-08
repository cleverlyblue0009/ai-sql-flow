-- Query: regexp_matching
-- Dialect: postgresql
-- Complexity: 35
-- Difficulty: medium

SELECT * FROM users WHERE email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$';
