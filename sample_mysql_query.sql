-- Sample MySQL Database Schema and Queries
-- This file demonstrates various MySQL features that need translation

-- Create users table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active TINYINT(1) DEFAULT 1,
    profile_data LONGTEXT
);

-- Create orders table  
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    order_date TIMESTAMP DEFAULT NOW(),
    status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Sample queries that need translation
SELECT 
    u.user_id,
    u.username,
    COUNT(o.order_id) as order_count,
    SUM(o.total_amount) as total_spent,
    DATE_FORMAT(u.created_at, '%Y-%m') as signup_month
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE u.created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
  AND u.is_active = 1
GROUP BY u.user_id, DATE_FORMAT(u.created_at, '%Y-%m')
HAVING COUNT(o.order_id) > 0
ORDER BY total_spent DESC
LIMIT 100;

-- Another query with MySQL-specific functions
SELECT 
    `user_id`,
    `username`,
    CONCAT('User: ', `username`) as display_name,
    DATE_FORMAT(`created_at`, '%W, %M %d, %Y') as formatted_date
FROM `users`
WHERE `created_at` BETWEEN DATE_SUB(NOW(), INTERVAL 1 YEAR) AND NOW()
ORDER BY `created_at` DESC;

-- Update statement with MySQL syntax
UPDATE `users` 
SET `profile_data` = JSON_OBJECT('last_login', NOW())
WHERE `user_id` IN (
    SELECT DISTINCT `user_id` 
    FROM `orders` 
    WHERE `order_date` >= DATE_SUB(NOW(), INTERVAL 30 DAY)
);