-- Query: try_cast
-- Dialect: snowflake
-- Complexity: 40
-- Difficulty: medium

SELECT id, TRY_CAST(price_string AS NUMBER) as price FROM raw_data WHERE TRY_CAST(price_string AS NUMBER) IS NOT NULL;
