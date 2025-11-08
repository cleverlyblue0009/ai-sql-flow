-- Query: to_char_date
-- Dialect: oracle
-- Complexity: 40
-- Difficulty: medium

SELECT TO_CHAR(order_date, 'YYYY-MM') as month, SUM(amount) FROM orders GROUP BY TO_CHAR(order_date, 'YYYY-MM');
