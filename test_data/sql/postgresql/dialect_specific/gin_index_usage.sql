-- Query: gin_index_usage
-- Dialect: postgresql
-- Complexity: 30
-- Difficulty: hard
-- Dialect Features: GIN

CREATE INDEX idx_products_tags ON products USING GIN(tags);
