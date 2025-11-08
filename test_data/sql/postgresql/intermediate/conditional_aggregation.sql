-- Query: conditional_aggregation
-- Dialect: postgresql
-- Complexity: 45
-- Difficulty: medium

SELECT 
    SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as completed_revenue,
    SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_revenue
FROM orders;
