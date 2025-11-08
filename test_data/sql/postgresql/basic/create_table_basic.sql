-- Query: create_table_basic
-- Dialect: postgresql
-- Complexity: 30
-- Difficulty: easy

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);
