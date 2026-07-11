-- Query ID: pg_d3_easy_1
-- Source dialect: postgres
-- Target dataset: D3
-- Difficulty: easy
-- Description: Count rows with out-of-range age
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT COUNT(*) AS age_violations FROM d3_table WHERE "AGE" < 18 OR "AGE" > 95