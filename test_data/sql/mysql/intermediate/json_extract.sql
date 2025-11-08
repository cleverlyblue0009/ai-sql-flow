-- Query: json_extract
-- Dialect: mysql
-- Complexity: 40
-- Difficulty: medium

SELECT id, JSON_EXTRACT(data, '$.customer.name') as customer_name FROM orders;
