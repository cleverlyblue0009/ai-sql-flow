-- Query: merge_statement
-- Dialect: sqlserver
-- Complexity: 75
-- Difficulty: hard

MERGE INTO target_table AS t
USING source_table AS s
ON t.id = s.id
WHEN MATCHED THEN
    UPDATE SET t.value = s.value, t.updated_at = GETDATE()
WHEN NOT MATCHED THEN
    INSERT (id, value, created_at) VALUES (s.id, s.value, GETDATE());
