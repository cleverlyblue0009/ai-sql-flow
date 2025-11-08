-- Query: jsonb_operations
-- Dialect: postgresql
-- Complexity: 55
-- Difficulty: medium

SELECT id, 
    data->>'customer_name' as customer,
    CAST(data->'amount' as DECIMAL) as amount
FROM transactions
WHERE data @> '{"status": "completed"}';
