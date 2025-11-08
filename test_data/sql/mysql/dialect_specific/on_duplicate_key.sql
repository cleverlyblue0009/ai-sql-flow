-- Query: on_duplicate_key
-- Dialect: mysql
-- Complexity: 55
-- Difficulty: hard
-- Dialect Features: ON DUPLICATE KEY UPDATE

INSERT INTO user_stats (user_id, order_count, total_spent)
VALUES (123, 1, 99.99)
ON DUPLICATE KEY UPDATE
    order_count = order_count + 1,
    total_spent = total_spent + 99.99;
