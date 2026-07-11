-- Query ID: sf_d3_easy_1
-- Source dialect: snowflake
-- Target dataset: D3
-- Difficulty: easy
-- Description: Average age of defaulters vs non-defaulters
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT "default_payment_next_month", ROUND(AVG("AGE"), 2) AS avg_age, COUNT(*) AS n FROM "d3_table" GROUP BY "default_payment_next_month"