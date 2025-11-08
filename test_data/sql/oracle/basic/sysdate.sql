-- Query: sysdate
-- Dialect: oracle
-- Complexity: 15
-- Difficulty: easy

SELECT * FROM orders WHERE order_date >= SYSDATE - 7;
