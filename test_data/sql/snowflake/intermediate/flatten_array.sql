-- Query: flatten_array
-- Dialect: snowflake
-- Complexity: 55
-- Difficulty: medium

SELECT f.value::STRING as tag FROM products, LATERAL FLATTEN(input => tags) f;
