-- Query ID: my_d3_medium_1
-- Source dialect: mysql
-- Target dataset: D3
-- Difficulty: medium
-- Description: Default rate by education level
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT `EDUCATION`, COUNT(*) AS total, SUM(`default_payment_next_month`) AS defaults, SUM(`default_payment_next_month`) / COUNT(*) AS default_rate FROM `d3_table` GROUP BY `EDUCATION` ORDER BY `EDUCATION`