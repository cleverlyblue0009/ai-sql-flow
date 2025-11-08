-- Query: coalesce_function
-- Dialect: postgresql
-- Complexity: 25
-- Difficulty: medium

SELECT name, COALESCE(phone, email, 'No contact') as contact FROM users;
