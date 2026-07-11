-- Query ID: pg_d2_medium_1
-- Source dialect: postgres
-- Target dataset: D2
-- Difficulty: medium
-- Description: Agency-level average gross pay with HAVING filter
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT "Agency_Name", ROUND(AVG("Regular_Gross_Paid"::numeric), 2) AS avg_gross FROM d2_table GROUP BY "Agency_Name" HAVING AVG("Regular_Gross_Paid"::numeric) > 50000 ORDER BY avg_gross DESC LIMIT 10