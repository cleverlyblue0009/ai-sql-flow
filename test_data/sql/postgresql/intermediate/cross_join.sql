-- Query: cross_join
-- Dialect: postgresql
-- Complexity: 25
-- Difficulty: medium

SELECT p.name, c.color FROM products p CROSS JOIN colors c;
