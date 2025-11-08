-- Query: listen_notify
-- Dialect: postgresql
-- Complexity: 20
-- Difficulty: hard
-- Dialect Features: NOTIFY

NOTIFY order_updates, 'New order placed';
