-- Query ID: pg_d3_medium_1
-- Source dialect: postgres
-- Target dataset: D3
-- Difficulty: medium
-- Description: Average credit limit by education level
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT "EDUCATION", COUNT(*) AS n, ROUND(AVG("LIMIT_BAL"::numeric), 2) AS avg_limit FROM d3_table GROUP BY "EDUCATION" ORDER BY "EDUCATION"