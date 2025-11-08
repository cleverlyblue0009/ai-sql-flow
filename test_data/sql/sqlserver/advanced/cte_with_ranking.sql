-- Query: cte_with_ranking
-- Dialect: sqlserver
-- Complexity: 65
-- Difficulty: hard

WITH RankedOrders AS (
    SELECT customer_id, order_date, amount,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) as rn
    FROM orders
)
SELECT * FROM RankedOrders WHERE rn <= 5;
