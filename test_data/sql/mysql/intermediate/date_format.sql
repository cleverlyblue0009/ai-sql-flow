-- Query: date_format
-- Dialect: mysql
-- Complexity: 40
-- Difficulty: medium

SELECT DATE_FORMAT(order_date, '%Y-%m') as month, SUM(amount) FROM orders GROUP BY DATE_FORMAT(order_date, '%Y-%m');
