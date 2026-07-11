-- Query ID: ss_d3_easy_1
-- Source dialect: tsql
-- Target dataset: D3
-- Difficulty: easy
-- Description: Average payment amount for defaulted accounts
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT AVG(CAST([PAY_AMT1] AS DECIMAL(18,2))) AS avg_payment FROM [d3_table] WHERE [default_payment_next_month] = 1