-- Query: xml_operations
-- Dialect: sqlserver
-- Complexity: 60
-- Difficulty: hard
-- Dialect Features: XML

SELECT id, data.value('(/root/customer)[1]', 'NVARCHAR(100)') as customer FROM orders;
