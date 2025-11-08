-- Query: jsonb_aggregation
-- Dialect: postgresql
-- Complexity: 60
-- Difficulty: hard
-- Dialect Features: JSONB_AGG, JSONB_BUILD_OBJECT

SELECT category, JSONB_AGG(JSONB_BUILD_OBJECT('name', name, 'price', price)) as products FROM products GROUP BY category;
