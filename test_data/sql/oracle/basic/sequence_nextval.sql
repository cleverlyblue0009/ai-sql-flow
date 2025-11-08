-- Query: sequence_nextval
-- Dialect: oracle
-- Complexity: 20
-- Difficulty: easy

INSERT INTO orders (id, customer_id, amount) VALUES (order_seq.NEXTVAL, 123, 99.99);
