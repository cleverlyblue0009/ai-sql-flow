-- Query: time_travel
-- Dialect: snowflake
-- Complexity: 40
-- Difficulty: hard
-- Dialect Features: TIME TRAVEL

SELECT * FROM orders AT(TIMESTAMP => '2024-01-01 00:00:00'::TIMESTAMP);
