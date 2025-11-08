-- Query: basic_insert
-- Dialect: postgresql
-- Complexity: 15
-- Difficulty: easy

INSERT INTO users (name, email, created_at) VALUES ('John Doe', 'john@example.com', NOW());
