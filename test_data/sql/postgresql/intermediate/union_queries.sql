-- Query: union_queries
-- Dialect: postgresql
-- Complexity: 30
-- Difficulty: medium

SELECT 'premium' as tier, name FROM premium_users
UNION ALL
SELECT 'standard' as tier, name FROM standard_users;
