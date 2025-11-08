-- Query: format_function
-- Dialect: sqlserver
-- Complexity: 35
-- Difficulty: medium

SELECT FORMAT(order_date, 'yyyy-MM-dd') as formatted_date, FORMAT(amount, 'C', 'en-US') as formatted_amount FROM orders;
