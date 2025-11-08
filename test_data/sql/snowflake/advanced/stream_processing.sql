-- Query: stream_processing
-- Dialect: snowflake
-- Complexity: 70
-- Difficulty: hard

CREATE STREAM orders_stream ON TABLE orders
APPEND_ONLY = TRUE;
SELECT * FROM orders_stream WHERE METADATA$ACTION = 'INSERT';
