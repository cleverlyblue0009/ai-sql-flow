-- Query: insert_with_now
-- Dialect: mysql
-- Complexity: 15
-- Difficulty: easy

INSERT INTO users (name, email, created_at) VALUES ('John Doe', 'john@example.com', NOW());
