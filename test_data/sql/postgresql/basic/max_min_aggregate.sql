-- Query: max_min_aggregate
-- Dialect: postgresql
-- Complexity: 15
-- Difficulty: easy

SELECT MAX(price) as max_price, MIN(price) as min_price FROM products;
