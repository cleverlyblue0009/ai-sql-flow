-- Query: variant_json
-- Dialect: snowflake
-- Complexity: 50
-- Difficulty: hard
-- Dialect Features: VARIANT

SELECT data:customer.name::STRING as customer_name FROM transactions;
