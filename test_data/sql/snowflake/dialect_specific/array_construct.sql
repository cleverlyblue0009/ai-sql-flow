-- Query: array_construct
-- Dialect: snowflake
-- Complexity: 30
-- Difficulty: hard
-- Dialect Features: ARRAY_CONSTRUCT

SELECT ARRAY_CONSTRUCT('red', 'green', 'blue') as colors FROM DUAL;
