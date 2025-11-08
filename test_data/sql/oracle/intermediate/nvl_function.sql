-- Query: nvl_function
-- Dialect: oracle
-- Complexity: 25
-- Difficulty: medium

SELECT name, NVL(phone, 'No phone') as contact_phone FROM customers;
