-- Query ID: pg_d3_hard_1
-- Source dialect: postgres
-- Target dataset: D3
-- Difficulty: hard
-- Description: Window function: running avg bill amount per education tier
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT "EDUCATION", "AGE", "BILL_AMT1", AVG("BILL_AMT1"::numeric) OVER (PARTITION BY "EDUCATION" ORDER BY "AGE" ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS rolling_avg FROM d3_table LIMIT 500