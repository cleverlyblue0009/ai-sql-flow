-- Query: complex_join_aggregation
-- Dialect: mysql
-- Complexity: 70
-- Difficulty: hard

SELECT p.name, 
    COUNT(DISTINCT o.id) as order_count,
    SUM(oi.quantity) as total_quantity,
    AVG(oi.price) as avg_price
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.id
WHERE o.order_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY p.id, p.name
HAVING order_count > 10;
