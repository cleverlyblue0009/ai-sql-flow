-- Query: uuid_generation
-- Dialect: postgresql
-- Complexity: 25
-- Difficulty: hard
-- Dialect Features: gen_random_uuid

INSERT INTO users (id, name, email) VALUES (gen_random_uuid(), 'John Doe', 'john@example.com');
