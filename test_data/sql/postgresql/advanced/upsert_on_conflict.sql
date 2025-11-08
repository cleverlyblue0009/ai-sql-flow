-- Query: upsert_on_conflict
-- Dialect: postgresql
-- Complexity: 60
-- Difficulty: hard

INSERT INTO user_stats (user_id, order_count, total_spent, last_updated)
VALUES (123, 1, 99.99, NOW())
ON CONFLICT (user_id)
DO UPDATE SET
    order_count = user_stats.order_count + 1,
    total_spent = user_stats.total_spent + 99.99,
    last_updated = NOW();
