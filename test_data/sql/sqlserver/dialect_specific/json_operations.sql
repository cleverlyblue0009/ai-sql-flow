-- Query: json_operations
-- Dialect: sqlserver
-- Complexity: 55
-- Difficulty: hard
-- Dialect Features: JSON_VALUE

SELECT id, JSON_VALUE(data, '$.customer.name') as customer_name FROM orders WHERE JSON_VALUE(data, '$.status') = 'completed';
