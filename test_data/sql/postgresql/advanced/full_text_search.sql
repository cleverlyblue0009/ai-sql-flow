-- Query: full_text_search
-- Dialect: postgresql
-- Complexity: 65
-- Difficulty: hard

SELECT id, title, ts_rank(to_tsvector('english', content), to_tsquery('english', 'database & optimization')) as rank
FROM articles
WHERE to_tsvector('english', content) @@ to_tsquery('english', 'database & optimization')
ORDER BY rank DESC;
