-- Query: clone_table
-- Dialect: snowflake
-- Complexity: 20
-- Difficulty: hard
-- Dialect Features: CLONE

CREATE TABLE orders_backup CLONE orders;
