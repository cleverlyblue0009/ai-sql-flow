-- Query: try_convert
-- Dialect: sqlserver
-- Complexity: 35
-- Difficulty: medium

SELECT id, TRY_CONVERT(INT, price_string) as price FROM raw_data WHERE TRY_CONVERT(INT, price_string) IS NOT NULL;
