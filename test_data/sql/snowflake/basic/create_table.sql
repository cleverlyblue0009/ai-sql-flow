-- Query: create_table
-- Dialect: snowflake
-- Complexity: 35
-- Difficulty: easy

CREATE TABLE customers (
    id NUMBER AUTOINCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
