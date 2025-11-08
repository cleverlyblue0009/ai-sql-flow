-- Query: fulltext_search
-- Dialect: mysql
-- Complexity: 50
-- Difficulty: hard
-- Dialect Features: MATCH, AGAINST

SELECT id, title FROM articles WHERE MATCH(content) AGAINST('database optimization' IN BOOLEAN MODE);
