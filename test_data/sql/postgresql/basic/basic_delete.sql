-- Query: basic_delete
-- Dialect: postgresql
-- Complexity: 20
-- Difficulty: easy

DELETE FROM temp_data WHERE created_at < NOW() - INTERVAL '30 days';
