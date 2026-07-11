-- Query ID: ora_d3_medium_1
-- Source dialect: oracle
-- Target dataset: D3
-- Difficulty: medium
-- Description: Delinquency rate by marriage status
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT "MARRIAGE", COUNT(*) n, SUM("default_payment_next_month") defaults, ROUND(SUM("default_payment_next_month") / COUNT(*), 4) AS default_rate FROM "d3_table" GROUP BY "MARRIAGE" ORDER BY "MARRIAGE"